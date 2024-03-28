import torch
import torch.nn as nn
import torch.nn.functional as F
from sat.transformer_defaults import attention_fn_default
from sat.model.base_model import BaseMixin, non_conflict
from sat.mpu.layers import ColumnParallelLinear, RowParallelLinear
from sat.mpu.utils import split_tensor_along_last_dim
from sat import mpu


class LlamaVisionExpertFCMixin(BaseMixin):
    def __init__(self, in_features, hidden_features, num_layers=32, num_vision_layers=0, vision_layer_range=None,
                 params_dtype=torch.float, device=torch.device('cpu')):
        super().__init__()

        self.num_layers = num_layers
        self.num_vision_layers = num_vision_layers
        if vision_layer_range is None:
            vision_layer_range = [i for i in range(min(num_vision_layers, num_layers))]
        self.vision_layer_range = vision_layer_range
        self.gate_proj = nn.ModuleList([ColumnParallelLinear(
            in_features,
            hidden_features,
            gather_output=False,
            init_method=None,
            bias=False,
            params_dtype=params_dtype,
            module=self,
            name="dense_h_to_4h_gate",
            skip_init=True,
            device=device
        ) for i in range(num_layers)])
        # Trainable vision expert parameters
        vision_dense_h_to_4h_list = []
        vision_dense_4h_to_h_list = []
        gate_proj_list = []


        for i in vision_layer_range:
            vision_dense_h_to_4h = ColumnParallelLinear(
                in_features,
                hidden_features,
                gather_output=False,
                init_method=None,
                bias=False,
                params_dtype=params_dtype,
                module=self,
                name="vision_dense_h_to_4h",
                skip_init=True,
                device=device
            )

            # Project back to h.
            vision_dense_4h_to_h = RowParallelLinear(
                hidden_features,
                in_features,
                input_is_parallel=True,
                init_method=None,
                bias=False,
                params_dtype=params_dtype,
                module=self,
                name="vision_dense_4h_to_h",
                skip_init=True,
                device=device
            )

            gate_proj = ColumnParallelLinear(
                in_features,
                hidden_features,
                gather_output=False,
                init_method=None,
                bias=False,
                params_dtype=params_dtype,
                module=self,
                name="vision_gate_proj",
                skip_init=True,
                device=device
            )

            vision_dense_h_to_4h_list.append(vision_dense_h_to_4h)
            vision_dense_4h_to_h_list.append(vision_dense_4h_to_h)
            gate_proj_list.append(gate_proj)

        self.vision_dense_h_to_4h_list = nn.ModuleDict([
            (str(layer_id), vision_dense_h_to_4h)
            for layer_id, vision_dense_h_to_4h in zip(vision_layer_range, vision_dense_h_to_4h_list)
        ])
        self.vision_dense_4h_to_h_list = nn.ModuleDict([
            (str(layer_id), vision_dense_4h_to_h)
            for layer_id, vision_dense_4h_to_h in zip(vision_layer_range, vision_dense_4h_to_h_list)
        ])
        self.vision_gate_proj = nn.ModuleDict([
            (str(layer_id), gate_proj)
            for layer_id, gate_proj in zip(vision_layer_range, gate_proj_list)
        ])

    def mlp_forward(self, hidden_states, **kw_args):
        mixin_self = self
        self = self.transformer.layers[kw_args['layer_id']].mlp
        if "vision_expert_mask" in kw_args:
            vision_expert_mask = kw_args['vision_expert_mask']
        else:
            vision_expert_mask = None

        layer_id_key = str(int(kw_args['layer_id']))

        if kw_args['layer_id'] in mixin_self.vision_layer_range and (vision_expert_mask is not None) and vision_expert_mask.any():
            vision_dense_h_to_4h = mixin_self.vision_dense_h_to_4h_list[layer_id_key]
            vision_dense_4h_to_h = mixin_self.vision_dense_4h_to_h_list[layer_id_key]
            vision_gate_proj = mixin_self.vision_gate_proj[layer_id_key]
            output = torch.empty(hidden_states.shape, dtype=hidden_states.dtype, device=hidden_states.device)

            language_hidden_state = hidden_states[~vision_expert_mask.bool()]
            language_intermediate_parallel = self.activation_func(mixin_self.gate_proj[kw_args['layer_id']](language_hidden_state)) * self.dense_h_to_4h(language_hidden_state)
            output[~vision_expert_mask.bool()] = self.dense_4h_to_h(language_intermediate_parallel)  # language_output

            vision_hidden_state = hidden_states[vision_expert_mask.bool()]
            vision_intermediate_parallel = vision_dense_h_to_4h(vision_hidden_state)
            gate_output = vision_gate_proj(vision_hidden_state)

            vision_intermediate_parallel *= self.activation_func(gate_output)
            output[vision_expert_mask.bool()] = vision_dense_4h_to_h(vision_intermediate_parallel)  # vision_output
        else:
            intermediate_parallel = self.activation_func(mixin_self.gate_proj[kw_args['layer_id']](hidden_states)) * self.dense_h_to_4h(hidden_states)
            output = self.dense_4h_to_h(intermediate_parallel)

        return output.contiguous()

    def copy_param(self):
        with torch.no_grad():
            for i in self.vision_layer_range:
                self.vision_gate_proj[str(i)].weight.data.copy_(self.gate_proj[i].weight.data)
                self.vision_dense_4h_to_h_list[str(i)].weight.data.copy_(self.transformer.layers[i].mlp.dense_4h_to_h.weight.data)
                self.vision_dense_h_to_4h_list[str(i)].weight.data.copy_(self.transformer.layers[i].mlp.dense_h_to_4h.weight.data)

from sat.mpu import get_model_parallel_world_size
from sat.mpu.utils import divide
from sat.model.position_embedding.triton_rotary_embeddings import FastRotaryEmbedding

class LlamaVisionExpertAttnMixin(BaseMixin):
    def __init__(self, hidden_size, num_heads, num_layers=28, num_vision_layers=0, use_vision_expert=True, vision_layer_range=None,
                 params_dtype=torch.float, device=torch.device('cpu')):
        super().__init__()

        world_size = get_model_parallel_world_size()
        self.hidden_size = hidden_size
        self.num_attention_heads = num_heads
        self.hidden_size_per_attention_head = divide(hidden_size, num_heads)
        self.num_attention_heads_per_partition = divide(num_heads, world_size)
        self.inner_hidden_size = num_heads * self.hidden_size_per_attention_head

        self.rotary_emb = FastRotaryEmbedding(
             hidden_size // num_heads, pos_idx_in_fp32=False
         )

        self.num_vision_layers = num_vision_layers
        self.num_layers = num_layers
        if vision_layer_range is None:
            vision_layer_range = [i for i in range(min(num_vision_layers, num_layers))]
        self.vision_layer_range = vision_layer_range

        self.use_vision_expert = use_vision_expert
        # Trainable vision expert parameters

        if self.use_vision_expert:
            vision_query_key_value_list = []
            vision_dense_list = []
            for i in vision_layer_range:
                vision_query_key_value = ColumnParallelLinear(
                    hidden_size,
                    3 * hidden_size,
                    stride=3,
                    gather_output=False,
                    init_method=None,
                    bias=False,
                    params_dtype=params_dtype,
                    module=self,
                    name="vision_query_key_value",
                    skip_init=True,
                    device=device
                )

                vision_dense = RowParallelLinear(
                    self.inner_hidden_size,
                    hidden_size,
                    input_is_parallel=True,
                    init_method=None,
                    bias=False,
                    params_dtype=params_dtype,
                    module=self,
                    name="vision_dense",
                    skip_init=True,
                    device=device,
                    final_bias=False
                )

                vision_query_key_value_list.append(vision_query_key_value)
                vision_dense_list.append(vision_dense)

            self.vision_query_key_value_list = nn.ModuleDict([
                (str(layer_id), vision_query_key_value)
                for layer_id, vision_query_key_value in zip(vision_layer_range, vision_query_key_value_list)
            ])
            self.vision_dense_list = nn.ModuleDict([
                (str(layer_id), vision_dense)
                for layer_id, vision_dense in zip(vision_layer_range, vision_dense_list)
            ])

    def attention_forward(self, hidden_states, mask, **kw_args):
        mixin_self = self
        self = self.transformer.layers[kw_args['layer_id']].attention
        attention_fn = attention_fn_default
        if 'attention_fn' in self.hooks:
            attention_fn = self.hooks['attention_fn']
        if "vision_expert_mask" in kw_args:
            vision_expert_mask = kw_args['vision_expert_mask']
        else:
            vision_expert_mask = None

        layer_id_key = str(int(kw_args['layer_id']))
        if mixin_self.use_vision_expert and kw_args['layer_id'] in mixin_self.vision_layer_range and (
                vision_expert_mask is not None) and vision_expert_mask.any():
            shape = list(hidden_states.shape)
            parallel_size = mpu.get_model_parallel_world_size()
            shape[-1] = shape[-1] * 3 // parallel_size
            vision_query_key_value = mixin_self.vision_query_key_value_list[layer_id_key]
            mixed_raw_layer = torch.empty(shape, dtype=hidden_states.dtype, device=hidden_states.device)
            language_hidden_states = hidden_states[~vision_expert_mask.bool()]
            vision_hidden_states = hidden_states[vision_expert_mask.bool()]
            mixed_raw_layer[~vision_expert_mask.bool()] = self.query_key_value(
                language_hidden_states)  # language_mixed_raw_layer
            mixed_raw_layer[vision_expert_mask.bool()] = vision_query_key_value(
                vision_hidden_states)  # vision_mixed_raw_layer
        else:
            mixed_raw_layer = self.query_key_value(hidden_states)

        (mixed_query_layer,
            mixed_key_layer,
            mixed_value_layer) = split_tensor_along_last_dim(mixed_raw_layer, 3)

        dropout_fn = self.attention_dropout if self.training else None

        query_layer = self._transpose_for_scores(mixed_query_layer)
        key_layer = self._transpose_for_scores(mixed_key_layer)
        value_layer = self._transpose_for_scores(mixed_value_layer)

        query_layer, key_layer = mixin_self.rotary_emb(query_layer,key_layer, kw_args['position_ids'], max_seqlen=kw_args['position_ids'].max()+1, layer_id=kw_args['layer_id'])
        
        context_layer = attention_fn(query_layer, key_layer, value_layer, mask, dropout_fn, **kw_args)

        context_layer = context_layer.permute(0, 2, 1, 3).contiguous()
        new_context_layer_shape = context_layer.size()[:-2] + (self.hidden_size_per_partition,)
        context_layer = context_layer.view(*new_context_layer_shape)

        if mixin_self.use_vision_expert and kw_args['layer_id'] in mixin_self.vision_layer_range and (
                vision_expert_mask is not None) and vision_expert_mask.any():
            vision_dense = mixin_self.vision_dense_list[layer_id_key]
            parallel_size = mpu.get_model_parallel_world_size()
            target_shape = context_layer.shape[:-1] + (context_layer.shape[-1] * parallel_size,)
            output = torch.empty(target_shape, dtype=hidden_states.dtype, device=hidden_states.device)
            output[~vision_expert_mask.bool()] = self.dense(context_layer[~vision_expert_mask.bool()])  # language
            output[vision_expert_mask.bool()] = vision_dense(context_layer[vision_expert_mask.bool()])  # vision
        else:
            output = self.dense(context_layer)

        if self.training:
            output = self.output_dropout(output)
        return output.contiguous()

    def copy_param(self):
        with torch.no_grad():
            for i in self.vision_layer_range:
                self.vision_query_key_value_list[str(i)].weight.data.copy_(self.transformer.layers[i].attention.query_key_value.weight.data)
                self.vision_dense_list[str(i)].weight.data.copy_(self.transformer.layers[i].attention.dense.weight.data)