import base64
import copy
import io
import json
import time
from typing import Any, Optional
from PIL import Image

import requests

from .base import BaseService
from ufo.utils import print_with_color


class OllamaService(BaseService):
    def __init__(self, config, agent_type: str):
        self.config_llm = config[agent_type]
        self.config = config
        self.max_retry = self.config["MAX_RETRY"]
        self.timeout = self.config["TIMEOUT"]

    def chat_completion(
        self,
        messages,
        n,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        top_p: Optional[float] = None,
        **kwargs: Any,
    ):
        
        temperature = temperature if temperature is not None else self.config["TEMPERATURE"]
        max_tokens = max_tokens if max_tokens is not None else self.config["MAX_TOKENS"]
        top_p = top_p if top_p is not None else self.config["TOP_P"]

        responses = []
        
        for i in range(n):
            for _ in range(self.max_retry):
                try:
                    response = self._chat_completion(
                            messages=messages[i],
                            temperature=temperature,
                            max_tokens=max_tokens,
                            top_p=top_p,
                            **kwargs,
                        )
                    responses.append(response)
                except Exception as e:
                    print_with_color(f"Error making API request: {e}", "red")
                    try:
                        print_with_color(response, "red")
                    except:
                        _ 
                    time.sleep(3)
                    continue
            return responses, None






    def _chat_completion(
        self,
        messages,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        top_p: Optional[float] = None,
        **kwargs: Any,
    ):
        api_endpoint = "/api/chat"
        payload = {
            "model": self.config_llm["API_MODEL"],
            "messages": self._process_messages(messages),
            "format": "json",
            "options": {
                "temperature": temperature,
                "top_p": top_p,
                },
            "stream": False,
        }


        resp =  self._request_api(api_endpoint, payload)
        if resp.status_code != 200:
            raise Exception(
                f"Failed to get completion with error code {resp.status_code}: {resp.text}",
            )
        response: str = resp.json()['message']['content']

        return response

    def resize_base64_image(self, base64_str):
        image_data = base64.b64decode(base64_str)
        image = Image.open(io.BytesIO(image_data))

        #resize
        orig_width, orig_height = image.size
        max_size = 1024
        scale_w = min(max_size / orig_width, 1)
        scale_h = min(max_size / orig_height, 1)
        scale = min(scale_w, scale_h)
        new_width = int(orig_width * scale)
        new_height = int(orig_height * scale)
        image_resized = image.resize((new_width, new_height), Image.LANCZOS)
        buffer = io.BytesIO()
        image_resized.save(buffer, format="PNG")

        return base64.b64encode(buffer.getvalue()).decode()

    def _process_messages(self, messages):
        _messages = copy.deepcopy(messages)
        # Process messages and save images if any.
        tmp_image_text = tmp_image = None
        for i, message in enumerate(_messages):
            if isinstance(message['content'], list):
                for j, content in enumerate(message['content']):
                    if content['type']=='text':
                        tmp_text = content.get('text')
                    elif content['type']=='image_url':
                        tmp_image = content.get('image_url')['url'].split('base64,')[1]
                        tmp_image_text = tmp_text
                message['content'] = tmp_text + "And the image is the screenshot from windows," + tmp_image_text[:-1]
                message['images'] = [self.resize_base64_image(tmp_image)]
        return _messages


    def _request_api(self, api_path: str, payload: Any, stream: bool = False):
        url = f"{self.config_llm['API_BASE']}{api_path}"
        response = requests.post(url=url, json=payload, timeout=self.timeout, stream=stream)
        return response
