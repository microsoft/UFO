from contextlib import contextmanager
from typing import Any, Optional

import requests




class OllamaService:
    def __init__(self, config, agent_type: str, is_visual: bool = True):
        self.config_llm = config[agent_type]["VISUAL" if is_visual else "NON_VISUAL"]
        self.config = config
        self.max_retry = self.config["MAX_RETRY"]

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

        for _ in range(self.max_retry):
            try:
                return self._chat_completion(
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    top_p=top_p,
                    **kwargs,
                )
            except Exception:
                return self._completion(
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    top_p=top_p,
                    **kwargs,
                )

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
            "messages": messages,
            "format": "json",
            "temperature": temperature,
            "max_tokens": max_tokens,
            "top_p": top_p,
        }


        with self._request_api(api_endpoint, payload) as resp:
            if resp.status_code != 200:
                raise Exception(
                    f"Failed to get completion with error code {resp.status_code}: {resp.text}",
                )
            response: str = resp.json()["response"]
        return response


    def _completion(
        self,
        messages,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        top_p: Optional[float] = None,
        **kwargs: Any,
    ):
        api_endpoint = "/api/generate"
        payload = {
            "model": self.config_llm["API_MODEL"],
            "prompt": "",
            "temperature": temperature,
            "max_tokens": max_tokens,
            "top_p": top_p,
        }

        if self.config.response_format == "json":
            payload["format"] = "json"

        for message in messages:
            content: str = message["content"]
            if message["role"] == "system":
                payload["system"] = content
            else:
                payload["prompt"] = f"{payload['prompt']}\n{content}"

        with self._request_api(api_endpoint, payload) as resp:
            if resp.status_code != 200:
                raise Exception(
                    f"Failed to get completion with error code {resp.status_code}: {resp.text}",
                )
            response: str = resp.json()["response"]
        return response

    @contextmanager
    def _request_api(self, api_path: str, payload: Any, stream: bool = False):
        url = f"{self.config_llm["API_BASE"]}{api_path}"
        with requests.Session() as session:
            with session.post(url, json=payload, stream=stream) as resp:
                yield resp
