from sat.model.official.llama_model import LLaMAModel
import json
import torch
from functools import partial
from sat.model.base_model import BaseMixin
import torch.nn as nn
import numpy as np

from .eva_clip_L_hf import Eva2LargeEncoder
from .mixin import LlamaVisionExpertFCMixin, LlamaVisionExpertAttnMixin


class GLU(nn.Module):
    def __init__(self, args, in_features):
        super().__init__()
        self.linear_proj = nn.Linear(in_features, args.hidden_size, bias=False)
        self.norm1 = nn.LayerNorm(args.hidden_size)
        self.act1 = nn.GELU()
        self.act2 = nn.functional.silu
        self.dense_h_to_4h = nn.Linear(args.hidden_size, args.inner_hidden_size, bias=False)
        self.gate_proj = nn.Linear(args.hidden_size, args.inner_hidden_size, bias=False)
        self.dense_4h_to_h = nn.Linear(args.inner_hidden_size, args.hidden_size, bias=False)

    def forward(self, x):
        x = self.linear_proj(x)
        x = self.act1(self.norm1(x))
        x = self.act2(self.gate_proj(x)) * self.dense_h_to_4h(x)
        x = self.dense_4h_to_h(x)
        return x

from .eva_clip_model import EVA2CLIPModel
import argparse
from copy import deepcopy
def override_dist_dtype_device_args(args, b={}):
    if args.mode == 'inference':
        minimal_args = argparse.Namespace(
            world_size=args.world_size,
            rank=args.rank,
            local_rank=args.local_rank,
            skip_init=args.skip_init,
            use_gpu_initialization=args.use_gpu_initialization,
            deepspeed=args.deepspeed,
            bf16=args.bf16,
            fp16=args.fp16,
            mode=args.mode,
            device=args.device
        )
    else:
        minimal_args = argparse.Namespace(
                world_size=args.world_size,
                rank=args.rank,
                local_rank=args.local_rank,
                skip_init=args.skip_init,
                use_gpu_initialization=args.use_gpu_initialization,
                deepspeed=args.deepspeed,
                bf16=args.bf16,
                fp16=args.fp16,
                mode=args.mode,
                checkpoint_activations=args.checkpoint_activations if not hasattr(args, 'vit_checkpoint_activations') else args.vit_checkpoint_activations,
                checkpoint_num_layers=args.checkpoint_num_layers,
                device=args.device,
                hidden_dropout=0.,
                attention_dropout=0.,
            )
    if hasattr(args, 'model_parallel_size'):
        b['model_parallel_size'] = args.model_parallel_size
    return argparse.Namespace(**deepcopy(b), **vars(minimal_args))


class ExternalVisionModel(BaseMixin):
    '''A combination of vit and a linear projection'''
    def __init__(self, args, vitclass):
        '''
            args: the args to initialize the vit model
            vitclass: the class of VIT model, must be a subclass of BaseModel
            project_dim: the dimension of the projection layer
            default_load: the default load path for the vit model
            model_parallel_size: the model parallel size for the vit model
        '''
        super().__init__()
        self.vit = vitclass()
        # self.ppx = nn.Embedding(80, 1024)
        # self.ppy = nn.Embedding(80, 1024)
        # nn.init.uniform_(self.ppx.weight.data)
        # nn.init.uniform_(self.ppy.weight.data)

        # self.pos_embed = nn.Parameter(
        #     torch.from_numpy(get_2d_sincos_pos_embed(1024, 80)).float()
        # )
        cross_image_length = (args.cross_image_pix//14)**2
        self.pos_embed = nn.Parameter(
            torch.zeros(cross_image_length, 1024)
        )

    def forward(self, *args, **kw_args):
        enc = self.vit(*args, **kw_args)
        # i = torch.arange(80, device=enc.device)
        # j = torch.arange(80, device=enc.device)
        # posx = self.ppx(i).unsqueeze(0).repeat(80, 1, 1)
        # posy = self.ppy(j).unsqueeze(1).repeat(1, 80, 1)
        # pos = (posx + posy).view(-1, 1024).unsqueeze(0)

        # return enc + pos + self.pos_embed.unsqueeze(0)
        return enc + self.pos_embed.unsqueeze(0)

class ImageMixin(BaseMixin):
    def __init__(self, args):
        super().__init__()
        vit_args = override_dist_dtype_device_args(args, args.eva_args)
        self.vit_model = EVA2CLIPModel(EVA2CLIPModel.get_args(**vars(vit_args)))
        self.in_features = 1792
        self.linear_proj = GLU(args, self.in_features)
        self.image_length = args.image_length
        self.boi = nn.Parameter(torch.zeros(1, 1, args.hidden_size))
        self.eoi = nn.Parameter(torch.zeros(1, 1, args.hidden_size))
        
        # self.ppx = nn.Embedding(16,1792)
        # self.ppy = nn.Embedding(16,1792)

        # self.pos_embed = nn.Parameter(
        #     torch.from_numpy(get_2d_sincos_pos_embed(1792, 16)).float()
        # )
        self.pos_embed = nn.Parameter(
            torch.zeros(self.image_length, 1792)
        )

    def word_embedding_forward(self, input_ids, output_cross_layer, **kw_args):
        vision_inputs = {}
        for k in kw_args:
            if k.startswith('vision_') and k != 'vision_expert_mask':
                vision_inputs[k[7:]] = kw_args[k]
        if input_ids.shape[1] == 1 or not vision_inputs:
            return self.transformer.word_embeddings(input_ids)
        image_emb = self.vit_model(**vision_inputs)[0]
        
        # i = torch.arange(16, device=image_emb.device)
        # j = torch.arange(16, device=image_emb.device)
        # posx = self.ppx(i).unsqueeze(0).repeat(16, 1, 1)
        # posy = self.ppy(j).unsqueeze(1).repeat(1, 16, 1)
        # pos = (posx + posy).view(256, -1).unsqueeze(0)
        # image_emb = image_emb + pos + self.pos_embed.unsqueeze(0)
        image_emb = image_emb + self.pos_embed.unsqueeze(0)
            
        image_emb = self.linear_proj(image_emb)

        image_embed_mask = kw_args['image_embed_mask']
        word_embedding = self.transformer.word_embeddings(input_ids).clone()
        word_embedding[image_embed_mask.bool()] = torch.cat([self.boi.repeat(len(image_emb), 1, 1), image_emb, self.eoi.repeat(len(image_emb), 1, 1)], dim=1).reshape(-1, image_emb.shape[-1])

        return word_embedding.contiguous()
    
class CogAgentModel(LLaMAModel):
    def __init__(self, args, transformer=None, parallel_output=True, **kwargs):
        super().__init__(args, transformer=transformer, parallel_output=parallel_output, **kwargs)
        self.image_length = args.image_length
        self.cross_image_pix = args.cross_image_pix
        self.add_mixin("eva", ImageMixin(args))
        self.del_mixin("mlp")
        self.add_mixin("mlp", LlamaVisionExpertFCMixin(args.hidden_size, args.inner_hidden_size, args.num_layers, 32))
        self.del_mixin("rotary")
        self.add_mixin("rotary", LlamaVisionExpertAttnMixin(args.hidden_size, args.num_attention_heads, args.num_layers, 32))
        
        cross_model = ExternalVisionModel(args, vitclass=partial(Eva2LargeEncoder, image_size=self.cross_image_pix))
        # if args.mode != 'inference':
        # cross_model.vit.model.set_grad_checkpointing(True)
        self.add_mixin("encoder", cross_model)

    @classmethod
    def add_model_specific_args(cls, parser):
        group = parser.add_argument_group('CogAgent', 'CogAgent Configurations')
        group.add_argument('--image_length', type=int, default=256)
        group.add_argument('--cross_image_pix', type=int, default=1120) # Standard CogAgent use 1120; if you want to adjust this param, finetune the model first.
        group.add_argument('--eva_args', type=json.loads, default={})
        return super().add_model_specific_args(parser)

    def forward(self, input_ids, vision_expert_mask, image_embed_mask, **kwargs):
        
        cross_inputs = {}
        for k in kwargs:
            if k.startswith('cross_'):
                cross_inputs[k[6:]] = kwargs[k]
        if kwargs.get("mems_cross") is not None:
            kwargs['encoder_outputs'] = kwargs["mems_cross"][0]
        else:
            outputs = self.get_mixin('encoder')(**cross_inputs)
            kwargs['encoder_outputs'] = outputs
        kwargs['cross_attention_mask'] = cross_inputs['attention_mask'] 
                
        if input_ids.shape[1] > 1:
            return super().forward(input_ids=input_ids, vision_expert_mask=vision_expert_mask, image_embed_mask=image_embed_mask, **kwargs)
        return super().forward(input_ids=input_ids, **kwargs)


class FineTuneTrainCogAgentModel(CogAgentModel):
    def __init__(self, args, transformer=None, parallel_output=True, **kw_args):
        super().__init__(args, transformer=transformer, parallel_output=parallel_output, **kw_args)
        self.args = args
        # If you want to use model parallel with a mp_size=1 checkpoint, and meanwhile you also want to use lora,
        # you have to add_mixin after loading model checkpoint.
        
    @classmethod
    def add_model_specific_args(cls, parser):
        group = parser.add_argument_group('CogAgent-finetune', 'CogAgent finetune Configurations')
        group.add_argument('--pre_seq_len', type=int, default=8)
        group.add_argument('--lora_rank', type=int, default=10)
        group.add_argument('--use_ptuning', action="store_true")
        group.add_argument('--use_lora', action="store_true")
        group.add_argument('--use_qlora', action="store_true")
        group.add_argument('--layer_range', nargs='+', type=int, default=None)
        return super().add_model_specific_args(parser)


from sat.model.finetune import PTuningV2Mixin
from sat.model.finetune.lora2 import LoraMixin
class FineTuneTestCogAgentModel(CogAgentModel):
    def __init__(self, args, transformer=None, parallel_output=True, **kw_args):
        super().__init__(args, transformer=transformer, parallel_output=parallel_output, **kw_args)
        if args.use_ptuning:
            self.add_mixin("ptuning", PTuningV2Mixin(args.num_layers, args.hidden_size // args.num_attention_heads, args.num_attention_heads, args.pre_seq_len))
        if args.use_lora:
            self.add_mixin("lora", LoraMixin(args.num_layers, args.lora_rank, layer_range=args.layer_range), reinit=True)
            self.get_mixin("eva").vit_model.add_mixin("lora", LoraMixin(args.eva_args['num_layers'], args.lora_rank, layer_range=args.layer_range), reinit=True)
        elif args.use_qlora:
            self.add_mixin("lora", LoraMixin(args.num_layers, args.lora_rank, layer_range=args.layer_range, qlora=True), reinit=True)
        self.args = args
        
    @classmethod
    def add_model_specific_args(cls, parser):
        group = parser.add_argument_group('CogAgent-finetune', 'CogAgent finetune Configurations')
        group.add_argument('--pre_seq_len', type=int, default=8)
        group.add_argument('--lora_rank', type=int, default=10)
        group.add_argument('--use_ptuning', action="store_true")
        group.add_argument('--use_lora', action="store_true")
        group.add_argument('--use_qlora', action="store_true")
        group.add_argument('--layer_range', nargs='+', type=int, default=None)
        return super().add_model_specific_args(parser)
