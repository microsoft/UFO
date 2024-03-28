import time
from .conv_temp import conv_templates
from typing import Any, Optional

import requests
from ufo.utils import print_with_color
from .base import BaseService

DEFAULT_IMAGE_TOKEN = "<image>"

class LlavaService(BaseService):
    def __init__(self, config, agent_type: str):
        self.config_llm = config[agent_type]
        self.config = config
        self.max_retry = self.config["MAX_RETRY"]
        self.timeout = self.config["TIMEOUT"]
        self.max_tokens = 2048 #default max tokens for llava for now

    def chat_completion(
        self,
        messages,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        top_p: Optional[float] = None,
        **kwargs: Any,
    ):
        
        temperature = temperature if temperature is not None else self.config["TEMPERATURE"]
        max_tokens = max_tokens if max_tokens is not None else self.config["MAX_TOKENS"]
        top_p = top_p if top_p is not None else self.config["TOP_P"]
        conv = conv_templates[self._conversation()].copy()

        # system = messages[0]['content']
        # conv.system = system
        if self.config_llm["VISUAL_MODE"]:
            inp = DEFAULT_IMAGE_TOKEN + '\n' + messages[1]['content'][-1]['text']
            conv.append_message(conv.roles[0], inp)
            image_base64 = messages[1]['content'][-2]['image_url']\
                ['url'].split('base64,')[1]
        else:
            conv.append_message(conv.roles[0], messages[1]['content'][-1]['text'])
        # conv.append_message(conv.roles[1], None)
        prompt = conv.get_prompt()

        payload = {
            'model': self.config_llm['API_MODEL'],
            'prompt': prompt,
            'temperature': temperature,
            'top_p': top_p,
            'max_new_tokens': self.max_tokens,
            "image":image_base64
        }

        for _ in range(self.max_retry):
            try:
                response = requests.post(self.config_llm['API_BASE']+"/chat/completions", json=payload, timeout=self.timeout)
                if response.status_code == 200:
                    response = response.json()
                    text = response["text"]
                    return text, None
                else:
                    raise Exception(
                f"Failed to get completion with error code {response.status_code}: {response.text}",
            )
            except Exception as e:
                print_with_color(f"Error making API request: {e}", "red")
                try:
                    print_with_color(response, "red")
                except:
                    _ 
                time.sleep(3)
                continue
    


    def _conversation(
        self,
    ):
        model_paths = self.config_llm["API_MODEL"].strip("/").split("/")
        model_name = model_paths[-2] + "_" + model_paths[-1] if model_paths[-1].startswith('checkpoint-') else model_paths[-1]
        if "llama-2" in model_name.lower():
            conv_mode = "llava_llama_2"
        elif "mistral" in model_name.lower():
            conv_mode = "mistral_instruct"
        elif "v1.6-34b" in model_name.lower():
            conv_mode = "chatml_direct"
        elif "v1" in model_name.lower():
            conv_mode = "llava_v1"
        elif "mpt" in model_name.lower():
            conv_mode = "mpt"
        else:
            conv_mode = "vicuna_v1"
        return conv_mode
    