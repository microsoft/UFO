from sat.model.official.llama_model import LLaMAModel, rotate_half
from sat.transformer_defaults import attention_fn_default, split_tensor_along_last_dim
import torch.nn.functional as F


def base_history_to_prompt(self, query, history):
    prompt = '<EOI>' + query
    return prompt

def chat_history_to_prompt(self, query, history):
    prompt = "<EOI> [INST] "
    for i, (old_query, response) in enumerate(history):
        prompt += old_query + " [/INST] " + response + " [INST] "
    prompt += query + " [/INST] "
    return prompt

def vqa_history_to_prompt(self, query, history):
    # Only support single round chat in vqa mode
    prompt = "<EOI>Question: "
    # for i, (old_query, response) in enumerate(history):
    #     prompt += old_query + " Short answer: " + response + " Question: "
    prompt += query + " Short answer:"
    return prompt

def chat_old_history_to_prompt(self, query, history):
    prompt = "<EOI>Question: "
    for i, (old_query, response) in enumerate(history):
        prompt += old_query + " Answer: " + response + "\nQuestion: "
    prompt += query + " Answer:"
    return prompt

_history_to_prompt = {
    "base": base_history_to_prompt,
    "chat": chat_history_to_prompt,
    "vqa": vqa_history_to_prompt,
    "chat_old": chat_old_history_to_prompt, # for cogvlm-v1.1
}

from transformers import LlamaTokenizer

def llama2_tokenizer(tokenizer_path, signal_type="base"):
    tokenizer = LlamaTokenizer.from_pretrained(tokenizer_path)
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token_id = 32000
    tokenizer.boi = "[IMG]"
    tokenizer.eoi = "[/IMG]"
    assert signal_type in ["base", "chat", "vqa", "chat_old"]
    tokenizer.signal_type = signal_type
    return tokenizer

import re
import numpy as np
import torch

class llama2_text_processor:
    def __init__(self, tokenizer, max_target_length=2048, image_length=257, model=None):
        self.tokenizer = tokenizer
        self.max_target_length = max_target_length
        self.image_length = image_length

    def __call__(self, caption, prompt=""):
        if '<EOI>' not in prompt:
            prompt = self.replace_tags_with_empty(prompt)
            # caption = self.replace_tags_with_empty(caption)
            history = []
            prompt = self.history_to_prompt(prompt, history)

        input_ids = [self.tokenizer.bos_token_id]

        prompt_splits = prompt.split('<EOI>')
        caption_splits = caption.split('<EOI>')
        if len(prompt_splits) > 0:
            input_ids.extend(self.tokenizer.encode(prompt_splits[0], add_special_tokens=False))
        for tokens in prompt_splits[1:]:
            tokens_with_img = [-100] + self.tokenizer.encode(tokens, add_special_tokens=False)
            input_ids.extend(tokens_with_img)
        context_length = len(input_ids) + (len(prompt_splits)-1) * (self.image_length + 1)
        if context_length > self.max_target_length - 10:
            return None
        if len(caption_splits) > 0:
            input_ids.extend(self.tokenizer.encode(caption_splits[0], add_special_tokens=False))
        for tokens in caption_splits[1:]:
            tokens_with_img = [-100] + self.tokenizer.encode(tokens, add_special_tokens=False)
            input_ids.extend(tokens_with_img)

        if len(input_ids) > self.max_target_length - self.image_length - 5:
            input_ids = input_ids[:self.max_target_length - self.image_length - 5]

        input_ids += [self.tokenizer.eos_token_id]

        while -100 in input_ids:
            img_idx = input_ids.index(-100)
            input_ids = input_ids[:img_idx] + [0] * (self.image_length + 1) + [-1] + input_ids[img_idx+1:]

        image_position = []
        while -1 in input_ids:
            img_idx = input_ids.index(-1)
            input_ids[img_idx] = 0
            image_position.append(img_idx)

        image_embed_mask = [0] * len(input_ids)
        vision_expert_mask = [0] * len(input_ids)
        image_rope_mask = [0] * len(input_ids)
        for idx in image_position:
            image_embed_mask[idx-self.image_length-1: idx+1] = [1] * (self.image_length + 2)
            vision_expert_mask[idx-self.image_length-1: idx] = [1] * (self.image_length + 1)
            image_rope_mask[idx - self.image_length: idx] = [1] * self.image_length
        attention_mask = [1] * len(input_ids)
        labels = [-100] * context_length + input_ids[context_length:]

        pad_len = self.max_target_length - len(input_ids)
        input_ids = input_ids + [self.tokenizer.pad_token_id] * pad_len
        attention_mask = attention_mask + [1] * pad_len
        vision_expert_mask = vision_expert_mask + [0] * pad_len
        image_embed_mask = image_embed_mask + [0] * pad_len
        image_rope_mask = image_rope_mask + [0] * pad_len
        np_mask = np.tril(np.expand_dims(np.array(attention_mask), 0).repeat(len(attention_mask), 0))
        labels = labels + [-100] * pad_len

        for idx in image_position:
            labels[idx-self.image_length-1: idx+1] = [-100] * (self.image_length + 2)

        position_ids = []
        pid = -1
        for i in range(len(input_ids)):
            if image_rope_mask[i] == 0 or (i > 0 and image_rope_mask[i] != image_rope_mask[i - 1]):
                pid += 1
            position_ids.append(pid)

        input_ids = torch.tensor(input_ids).unsqueeze(0)
        labels = torch.tensor(labels).unsqueeze(0)
        attention_mask = torch.from_numpy(np_mask).unsqueeze(0).unsqueeze(0)
        image_embed_mask = torch.tensor(image_embed_mask).unsqueeze(0)
        vision_expert_mask = torch.tensor(vision_expert_mask).unsqueeze(0)
        image_rope_mask = torch.tensor(image_rope_mask).unsqueeze(0)
        position_ids = torch.tensor(position_ids).unsqueeze(0)
        context_length = torch.tensor(context_length).unsqueeze(0).long()
        return {'input_ids': input_ids, 'labels': labels, 'position_ids': position_ids, 'attention_mask': attention_mask, 'image_embed_mask': image_embed_mask,
                'context_length': context_length, 'image_position': image_position, 'vision_expert_mask': vision_expert_mask, 'image_rope_mask': image_rope_mask
                }

    def history_to_prompt(self, query, history):
        return _history_to_prompt[self.tokenizer.signal_type](self, query, history)

    def replace_tags_with_empty(self, text):
        return re.sub('<pad>|<s>|</s>|<EOI>', '', text)

from functools import partial
def get_masks_and_position_ids(seq, image_logits_mask):
    tokens = seq.unsqueeze(0)

    attention_mask = torch.ones((1, len(seq), len(seq)), device=tokens.device)
    attention_mask.tril_()
    attention_mask.unsqueeze_(1)

    position_ids = []
    pid = -1
    for i in range(len(image_logits_mask[0])):
        if image_logits_mask[0][i] == 0 or (i > 0 and image_logits_mask[0][i] != image_logits_mask[0][i - 1]):
            pid += 1
        position_ids.append(pid)
    for i in range(tokens.shape[1]-image_logits_mask.shape[1]):
        pid += 1
        position_ids.append(pid)
    position_ids = torch.tensor(position_ids, dtype=torch.long, device=tokens.device)
    position_ids = position_ids.unsqueeze(0)

    return tokens, attention_mask, position_ids

class llama2_text_processor_inference:
    def __init__(self, tokenizer, max_target_length=1024, image_length=257, model=None, no_prompt=False, english=True):
        self.tokenizer = tokenizer
        self.max_target_length = max_target_length
        self.image_length = image_length
        if self.tokenizer.signal_type == "chat":
            self.sep = "[/INST]"
        elif self.tokenizer.signal_type == "vqa":
            self.sep = " Short answer:"
        elif self.tokenizer.signal_type == "chat_old":
            self.sep = " Answer:"
        else:
            self.sep = "<unk>"

        self.invalid_slices = []
        self.no_eoi = True

    def __call__(self, prompt=""):
        if '<EOI>' not in prompt:
            prompt = self.replace_tags_with_empty(prompt)
            # caption = self.replace_tags_with_empty(caption)
            history = []
            prompt = self.history_to_prompt(prompt, history)

        input_ids = [self.tokenizer.bos_token_id]

        prompt_splits = prompt.split('<EOI>')
        if len(prompt_splits) > 0:
            input_ids.extend(self.tokenizer.encode(prompt_splits[0], add_special_tokens=False))
        for tokens in prompt_splits[1:]:
            tokens_with_img = [-100] + self.tokenizer.encode(tokens, add_special_tokens=False)
            input_ids.extend(tokens_with_img)

        while -100 in input_ids:
            img_idx = input_ids.index(-100)
            input_ids = input_ids[:img_idx] + [0] * (self.image_length + 1) + [-1] + input_ids[img_idx + 1:]

        image_position = []
        while -1 in input_ids:
            img_idx = input_ids.index(-1)
            input_ids[img_idx] = 0
            image_position.append(img_idx)

        image_embed_mask = [0] * len(input_ids)
        vision_expert_mask = [0] * len(input_ids)
        image_rope_mask = [0] * len(input_ids)
        for idx in image_position:
            image_embed_mask[idx - self.image_length - 1: idx + 1] = [1] * (self.image_length + 2)
            vision_expert_mask[idx - self.image_length - 1: idx] = [1] * (self.image_length + 1)
            image_rope_mask[idx - self.image_length: idx] = [1] * self.image_length

        input_ids = torch.tensor(input_ids).unsqueeze(0)
        image_embed_mask = torch.tensor(image_embed_mask).unsqueeze(0)
        vision_expert_mask = torch.tensor(vision_expert_mask).unsqueeze(0)
        image_rope_mask = torch.tensor(image_rope_mask).unsqueeze(0)
        return {'input_ids': input_ids, 'image_embed_mask': image_embed_mask, 'vision_expert_mask': vision_expert_mask, 'image_rope_mask': image_rope_mask}

    def history_to_prompt(self, query, history):
        return _history_to_prompt[self.tokenizer.signal_type](self, query, history)

    def replace_tags_with_empty(self, text):
        return re.sub('<pad>|<s>|</s>|<EOI>', '', text)

    def process_response(self, response):
        return response.replace('</s>', '')
    
    def get_func(self, inputs, **kwargs):
        get_func = partial(get_masks_and_position_ids, image_logits_mask=kwargs['image_rope_mask'])
        return get_func