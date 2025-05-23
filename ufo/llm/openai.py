# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import functools
import json
import os
import shutil
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Callable, Dict, List, Literal, Optional, Tuple

import openai
from openai import AzureOpenAI, OpenAI
from ufo.llm.base import BaseService


class BaseOpenAIService(BaseService):
    def __init__(self, config: Dict[str, Any], agent_type: str, api_provider: str, api_base: str) -> None:
        """
        Create an OpenAI service instance.
        :param config: The configuration for the OpenAI service.
        :param agent_type: The type of the agent.
        :param api_type: The type of the API (e.g., "openai", "aoai", "azure_ad").
        :param api_base: The base URL of the API.
        """
        self.config_llm = config[agent_type]
        self.config = config
        self.api_type = self.config_llm["API_TYPE"].lower()
        self.max_retry = self.config["MAX_RETRY"]
        self.prices = self.config.get("PRICES", {})
        self.agent_type = agent_type
        assert api_provider in ["openai", "aoai", "azure_ad"], "Invalid API Provider"

        self.client: OpenAI = OpenAIService.get_openai_client(
            api_provider,
            api_base,
            self.max_retry,
            self.config["TIMEOUT"],
            self.config_llm.get("API_KEY", ""),
            self.config_llm.get("API_VERSION", ""),
            aad_api_scope_base=self.config_llm.get("AAD_API_SCOPE_BASE", ""),
            aad_tenant_id=self.config_llm.get("AAD_TENANT_ID", ""),
        )

    def _chat_completion(
        self,
        messages: List[Dict[str, str]],
        stream: bool = False,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        top_p: Optional[float] = None,
        **kwargs: Any,
    ) -> Tuple[Dict[str, Any], Optional[float]]:
        """
        Generates completions for a given conversation using the OpenAI Chat API.
        :param messages: The list of messages in the conversation.
        :param n: The number of completions to generate.
        :param stream: Whether to stream the API response.
        :param temperature: The temperature parameter for randomness in the output.
        :param max_tokens: The maximum number of tokens in the generated completion.
        :param top_p: The top-p parameter for nucleus sampling.
        :param kwargs: Additional keyword arguments to pass to the OpenAI API.
        :return: A tuple containing a list of generated completions and the estimated cost.
        :raises: Exception if there is an error in the OpenAI API request
        """

        model = self.config_llm["API_MODEL"]

        temperature = (
            temperature if temperature is not None else self.config["TEMPERATURE"]
        )
        max_tokens = max_tokens if max_tokens is not None else self.config["MAX_TOKENS"]
        top_p = top_p if top_p is not None else self.config["TOP_P"]

        try:
            if self.config_llm.get("REASONING_MODEL", False):
                response: Any = self.client.chat.completions.create(
                    model=model,
                    messages=messages,  # type: ignore
                    n=1,
                    stream=stream,
                    **kwargs,
                )
            else:
                if not stream:
                    response: Any = self.client.chat.completions.create(
                        model=model,
                        messages=messages,  # type: ignore
                        n=1,
                        temperature=temperature,
                        max_tokens=max_tokens,
                        top_p=top_p,
                        stream=stream,
                        **kwargs,
                    )
                else:
                    response: Any = self.client.chat.completions.create(
                        model=model,
                        messages=messages,  # type: ignore
                        n=1,
                        temperature=temperature,
                        max_tokens=max_tokens,
                        top_p=top_p,
                        stream=stream,
                        stream_options={
                            "include_usage": True,
                        },
                        **kwargs,
                    )
            # response: Any = self.client.chat.completions.create(
            #     model=model,
            #     messages=messages,  # type: ignore
            #     n=n,
            #     # temperature=temperature,
            #     # max_tokens=max_tokens,
            #     # top_p=top_p,
            #     stream=stream,
            #     **kwargs,
            # )

            if stream:
                collected_content = [""]

                for chunk in response:
                    if chunk.choices:
                        delta = chunk.choices[0].delta
                        if delta and delta.content:
                            collected_content[0] += delta.content
                    else:
                        usage = chunk.usage

                prompt_tokens = usage.prompt_tokens
                completion_tokens = usage.completion_tokens

                cost = self.get_cost_estimator(
                    self.api_type, model, self.prices, prompt_tokens, completion_tokens
                )
                return collected_content, cost
            else:
                usage = response.usage
                prompt_tokens = usage.prompt_tokens
                completion_tokens = usage.completion_tokens

                cost = self.get_cost_estimator(
                    self.api_type, model, self.prices, prompt_tokens, completion_tokens
                )

                return [response.choices[0].message.content], cost

        except openai.APITimeoutError as e:
            # Handle timeout error, e.g. retry or log
            raise Exception(f"OpenAI API request timed out: {e}")
        except openai.APIConnectionError as e:
            # Handle connection error, e.g. check network or log
            raise Exception(f"OpenAI API request failed to connect: {e}")
        except openai.BadRequestError as e:
            # Handle invalid request error, e.g. validate parameters or log
            raise Exception(f"OpenAI API request was invalid: {e}")
        except openai.AuthenticationError as e:
            # Handle authentication error, e.g. check credentials or log
            raise Exception(f"OpenAI API request was not authorized: {e}")
        except openai.PermissionDeniedError as e:
            # Handle permission error, e.g. check scope or log
            raise Exception(f"OpenAI API request was not permitted: {e}")
        except openai.RateLimitError as e:
            # Handle rate limit error, e.g. wait or log
            raise Exception(f"OpenAI API request exceeded rate limit: {e}")
        except openai.APIError as e:
            # Handle API error, e.g. retry or log
            raise Exception(f"OpenAI API returned an API Error: {e}")

    def _chat_completion_operator(
        self,
        message: Dict[str, Any] = None,
        **kwargs: Any,
    ) -> Tuple[Dict[str, Any], Optional[float]]:
        """
        Generates completions for a given conversation using the OpenAI Chat API.
        :param message: The message to send to the API.
        :param n: The number of completions to generate.
        :return: A tuple containing a list of generated completions and the estimated cost.
        """

        inputs = message.get("inputs", [])
        tools = message.get("tools", [])
        previous_response_id = message.get("previous_response_id", None)

        response = self.client.responses.create(
            model=self.config_llm.get("API_MODEL"),
            input=inputs,
            tools=tools,
            previous_response_id=previous_response_id,
            truncation="auto",
            temperature=self.config.get("TEMPERATURE", 0),
            top_p=self.config.get("TOP_P", 0),
            timeout=self.config.get("TIMEOUT", 20),
        ).model_dump()

        if "usage" in response:
            usage = response.get("usage")
            input_tokens = usage.get("input_tokens", 0)
            output_tokens = usage.get("output_tokens", 0)
        else:
            input_tokens = 0
            output_tokens = 0

        cost = self.get_cost_estimator(
            self.api_type,
            self.config_llm["API_MODEL"],
            self.prices,
            input_tokens,
            output_tokens,
        )

        return [response], cost

    @functools.lru_cache()
    @staticmethod
    def get_openai_client(
        api_type: str,
        api_base: str,
        max_retry: int,
        timeout: int,
        api_key: Optional[str] = None,
        api_version: Optional[str] = None,
        aad_api_scope_base: Optional[str] = None,
        aad_tenant_id: Optional[str] = None,
    ) -> OpenAI:
        """
        Create an OpenAI client based on the API type.
        :param api_type: The type of the API, one of "openai", "aoai", or "azure_ad".
        :param api_base: The base URL of the API.
        :param max_retry: The maximum number of retries for the API request.
        :param timeout: The timeout for the API request.
        :param api_key: The API key for the OpenAI API.
        :param api_version: The API version for the Azure OpenAI API.
        :param aad_api_scope_base: The AAD API scope base for the Azure OpenAI API.
        :param aad_tenant_id: The AAD tenant ID for the Azure OpenAI API.
        :return: The OpenAI client.
        """
        if api_type == "openai":
            assert api_key, "OpenAI API key must be specified"
            assert api_base, "OpenAI API base URL must be specified"
            client = OpenAI(
                base_url=api_base,
                api_key=api_key,
                max_retries=max_retry,
                timeout=timeout,
            )
        else:
            assert api_version, "Azure OpenAI API version must be specified"
            if api_type == "aoai":
                assert api_key, "Azure OpenAI API key must be specified"
                client = AzureOpenAI(
                    max_retries=max_retry,
                    timeout=timeout,
                    api_version=api_version,
                    azure_endpoint=api_base,
                    api_key=api_key,
                )
            else:
                assert (
                    aad_api_scope_base and aad_tenant_id
                ), "AAD API scope base and tenant ID must be specified"
                token_provider = OpenAIService.get_aad_token_provider(
                    aad_api_scope_base=aad_api_scope_base,
                    aad_tenant_id=aad_tenant_id,
                )
                client = AzureOpenAI(
                    max_retries=max_retry,
                    timeout=timeout,
                    api_version=api_version,
                    azure_endpoint=api_base,
                    azure_ad_token_provider=token_provider,
                )
        return client

    @functools.lru_cache()
    @staticmethod
    def get_aad_token_provider(
        aad_api_scope_base: str,
        aad_tenant_id: str,
        token_cache_file: str = "aoai-token-cache.bin",
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        use_azure_cli: Optional[bool] = None,
        use_broker_login: Optional[bool] = None,
        use_managed_identity: Optional[bool] = None,
        use_device_code: Optional[bool] = None,
        **kwargs,
    ) -> Callable[[], str]:
        """
        Acquire token from Azure AD for OpenAI.
        :param aad_api_scope_base: The base scope for the Azure AD API.
        :param aad_tenant_id: The tenant ID for the Azure AD API.
        :param token_cache_file: The path to the token cache file.
        :param client_id: The client ID for the AAD app.
        :param client_secret: The client secret for the AAD app.
        :param use_azure_cli: Use Azure CLI for authentication.
        :param use_broker_login: Use broker login for authentication.
        :param use_managed_identity: Use managed identity for authentication.
        :param use_device_code: Use device code for authentication.
        :return: The access token for OpenAI.
        """

        import msal
        from azure.identity import (
            AuthenticationRecord,
            AzureCliCredential,
            ClientSecretCredential,
            DeviceCodeCredential,
            ManagedIdentityCredential,
            TokenCachePersistenceOptions,
            get_bearer_token_provider,
        )
        from azure.identity.broker import InteractiveBrowserBrokerCredential

        api_scope_base = "api://" + aad_api_scope_base

        tenant_id = aad_tenant_id
        scope = api_scope_base + "/.default"

        token_cache_option = TokenCachePersistenceOptions(
            name=token_cache_file,
            enable_persistence=True,
            allow_unencrypted_storage=True,
        )

        def save_auth_record(auth_record: AuthenticationRecord):
            try:
                with open(token_cache_file, "w") as cache_file:
                    cache_file.write(auth_record.serialize())
            except Exception as e:
                print("failed to save auth record", e)

        def load_auth_record() -> Optional[AuthenticationRecord]:
            try:
                if not os.path.exists(token_cache_file):
                    return None
                with open(token_cache_file, "r") as cache_file:
                    return AuthenticationRecord.deserialize(cache_file.read())
            except Exception as e:
                print("failed to load auth record", e)
                return None

        auth_record: Optional[AuthenticationRecord] = load_auth_record()

        current_auth_mode: Literal[
            "client_secret",
            "managed_identity",
            "az_cli",
            "interactive",
            "device_code",
            "none",
        ] = "none"

        implicit_mode = not (
            use_managed_identity or use_azure_cli or use_broker_login or use_device_code
        )

        if use_managed_identity or (implicit_mode and client_id is not None):
            if not use_managed_identity and client_secret is not None:
                assert (
                    client_id is not None
                ), "client_id must be specified with client_secret"
                current_auth_mode = "client_secret"
                identity = ClientSecretCredential(
                    client_id=client_id,
                    client_secret=client_secret,
                    tenant_id=tenant_id,
                    cache_persistence_options=token_cache_option,
                    authentication_record=auth_record,
                )
            else:
                current_auth_mode = "managed_identity"
                if client_id is None:
                    # using default managed identity
                    identity = ManagedIdentityCredential(
                        cache_persistence_options=token_cache_option,
                    )
                else:
                    identity = ManagedIdentityCredential(
                        client_id=client_id,
                        cache_persistence_options=token_cache_option,
                    )
        elif use_azure_cli or (implicit_mode and shutil.which("az") is not None):
            current_auth_mode = "az_cli"
            identity = AzureCliCredential(tenant_id=tenant_id)
        else:
            if implicit_mode:
                # enable broker login for known supported envs if not specified using use_device_code
                if sys.platform.startswith("darwin") or sys.platform.startswith(
                    "win32"
                ):
                    use_broker_login = True
                elif os.environ.get("WSL_DISTRO_NAME", "") != "":
                    use_broker_login = True
                elif os.environ.get("TERM_PROGRAM", "") == "vscode":
                    use_broker_login = True
                else:
                    use_broker_login = False
            if use_broker_login:
                current_auth_mode = "interactive"
                identity = InteractiveBrowserBrokerCredential(
                    tenant_id=tenant_id,
                    cache_persistence_options=token_cache_option,
                    use_default_broker_account=True,
                    parent_window_handle=msal.PublicClientApplication.CONSOLE_WINDOW_HANDLE,
                    authentication_record=auth_record,
                )
            else:
                current_auth_mode = "device_code"
                identity = DeviceCodeCredential(
                    tenant_id=tenant_id,
                    cache_persistence_options=token_cache_option,
                    authentication_record=auth_record,
                )

            try:
                auth_record = identity.authenticate(scopes=[scope])
                if auth_record:
                    save_auth_record(auth_record)

            except Exception as e:
                print(
                    f"failed to acquire token from AAD for OpenAI using {current_auth_mode}",
                    e,
                )
                raise e

        try:
            return get_bearer_token_provider(identity, scope)
        except Exception as e:
            print("failed to acquire token from AAD for OpenAI", e)
            raise e

class OpenAIService(BaseOpenAIService):
    """
    The OpenAI service class to interact with the OpenAI API.
    """

    def __init__(self, config: Dict[str, Any], agent_type: str) -> None:
        """
        Create an OpenAI service instance.
        :param config: The configuration for the OpenAI service.
        :param agent_type: The type of the agent.
        """
        super().__init__(config, agent_type, config[agent_type]["API_TYPE"].lower(), config[agent_type]["API_BASE"])

    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        n: int,
        stream: bool = False,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        top_p: Optional[float] = None,
        **kwargs: Any,
    ) -> Tuple[Dict[str, Any], Optional[float]]:
        """
        Generates completions for a given conversation using the OpenAI Chat API.
        :param messages: The list of messages in the conversation.
        :param n: The number of completions to generate.
        :param stream: Whether to stream the API response.
        :param temperature: The temperature parameter for randomness in the output.
        :param max_tokens: The maximum number of tokens in the generated completion.
        :param top_p: The top-p parameter for nucleus sampling.
        :param kwargs: Additional keyword arguments to pass to the OpenAI API.
        :return: A tuple containing a list of generated completions and the estimated cost.
        :raises: Exception if there is an error in the OpenAI API request
        """

        if self.agent_type.lower() != "operator":
            # If the agent type is not "operator", use the OpenAI API directly
            return super()._chat_completion(
                messages,
                False,
                temperature,
                max_tokens,
                top_p,
                response_format={"type": "json_object"},
                **kwargs,
            )
        else:
            # If the agent type is "operator", use the OpenAI Operator API
            return super()._chat_completion_operator(
                messages,
            )


class OpenAIBetaClient:

    Json = Dict[str, Any]

    def __init__(self, endpoint: str, api_version: str):
        """
        The OpenAI Beta client class to interact with the OpenAI API.
        :param endpoint: The OpenAI API endpoint.
        :param api_key: The OpenAI API key.
        :param api_version: The OpenAI API version.
        """

        self.endpoint = endpoint
        self.base_url = endpoint.rstrip("/")

        self.api_version = api_version

    def get_responses(
        self,
        model: str,
        previous_response_id: Optional[str] = None,
        inputs: Optional[list[Json]] = None,  # pylint: disable=redefined-builtin
        tool_output: Optional[list[Json]] = None,
        include: Optional[list[str]] = None,
        tools: Optional[list[Json]] = None,
        metadata: Optional[Json] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        parallel_tool_calls: Optional[bool] = None,
        token_provider: Optional[Callable[[], str]] = None,
    ) -> Json:
        self,

        if self.base_url.endswith("openai.azure.com"):
            url = f"{self.base_url}/openai/responses?api-version={self.api_version}"
        else:
            url = f"{self.base_url}/v1/responses"

        api_key = (
            token_provider if isinstance(token_provider, str) else token_provider()
        )

        headers = {
            "Content-Type": "application/json",
            "x-ms-enable-preview": "true",
            "api-key": api_key,
            "x-ms-enable-preview": "true",
            "Authorization": f"Bearer {api_key}",  # OpenAI
            "OpenAI-Beta": "responses=v1",  # OpenAI
        }

        return self.post_request(
            url,
            data={
                "model": model,
                "previous_response_id": previous_response_id,
                "input": inputs,
                "tool_output": tool_output,
                "include": include,
                "tools": tools,
                "metadata": metadata,
                "temperature": temperature,
                "top_p": top_p,
                "parallel_tool_calls": parallel_tool_calls,
            },
            headers=headers,
        )

    def post_request(self, url: str, data: Json, headers: Json) -> Json:
        """
        Send a POST request to the OpenAI API.
        :param url: The URL of the API endpoint.
        :param data: The data to send in the request.
        :param headers: The headers to send in the request.
        :return: The response from the API.
        """

        headers = {**headers, "content-type": "application/json"}

        data = json.dumps(self.compact(data)).encode("utf-8")

        req = urllib.request.Request(url, data=data, headers=headers, method="POST")

        try:
            with urllib.request.urlopen(req, timeout=20) as response:
                content = response.read().decode("utf-8")
                return json.loads(content)
        except urllib.error.HTTPError as e:
            self._handle_exception(e)
            print("Error:", e)

        return None

    def _handle_exception(self, exception: urllib.error.HTTPError) -> None:
        """
        Handle an exception from the OpenAI API.
        :param exception: The exception from the OpenAI API.
        """
        body = json.loads(exception.file.read().decode("utf-8"))
        request_id = exception.headers.get("x-request-id")

        error = OpenAIError(
            request_id=request_id, status_code=exception.code, message=body
        )
        print("Error:", error)
        raise OpenAIError(
            request_id=request_id, status_code=exception.code, message=body
        )

    @staticmethod
    def compact(data: Json) -> Json:
        """
        Remove None values from a dictionary.
        """
        return {k: v for k, v in data.items() if v is not None}


class OperatorServicePreview(BaseService):
    """
    The Operator service class to interact with the Operator for Computer Using Agent (CUA) API.
    """

    def __init__(
        self, config: Dict[str, Any], agent_type: str = "operator", client=None
    ) -> None:
        """
        Create an Operator service instance.
        :param config: The configuration for the Operator service.
        :param agent_type: The type of the agent.

        """
        self.config_llm = config[agent_type]
        self.config = config
        self.api_type = self.config_llm["API_TYPE"].lower()
        self.api_model = self.config_llm["API_MODEL"].lower()
        self.max_retry = self.config["MAX_RETRY"]
        self.prices = self.config.get("PRICES", {})
        self._agent_type = agent_type

        if client is None:
            self.client = self.get_openai_client()

    def get_openai_client(self):
        """
        Create an OpenAI client based on the API type.
        :return: The OpenAI client.
        """

        # client = OpenAIBetaClient(
        #     endpoint=self.config_llm.get("API_BASE"),
        #     api_version=self.config_llm.get("API_VERSION", ""),
        # )

        token_provider = self.get_token_provider()
        api_key = token_provider()

        client = openai.AzureOpenAI(
            azure_endpoint=self.config_llm.get("API_BASE"),
            api_key=api_key,
            max_retries=self.max_retry,
            timeout=self.config.get("TIMEOUT", 20),
            api_version=self.config_llm.get("API_VERSION"),
            default_headers={"x-ms-enable-preview": "true"},
        )

        return client

    def chat_completion(
        self,
        message: Dict[str, Any] = None,
        n: int = 1,
    ) -> Tuple[Dict[str, Any], Optional[float]]:
        """
        Generates completions for a given conversation using the OpenAI Chat API.
        :param message: The message to send to the API.
        :param n: The number of completions to generate.
        :return: A tuple containing a list of generated completions and the estimated cost.
        """

        inputs = message.get("inputs", [])
        tools = message.get("tools", [])
        previous_response_id = message.get("previous_response_id", None)

        response = self.client.responses.create(
            model=self.config_llm.get("API_MODEL"),
            input=inputs,
            tools=tools,
            previous_response_id=previous_response_id,
            truncation="auto",
            temperature=self.config.get("TEMPERATURE", 0),
            top_p=self.config.get("TOP_P", 0),
            timeout=self.config.get("TIMEOUT", 20),
        ).model_dump()

        if "usage" in response:
            usage = response.get("usage")
            input_tokens = usage.get("input_tokens", 0)
            output_tokens = usage.get("output_tokens", 0)
        else:
            input_tokens = 0
            output_tokens = 0

        cost = self.get_cost_estimator(
            self.api_type,
            self.api_model,
            self.prices,
            input_tokens,
            output_tokens,
        )

        return [response], cost

    def get_token_provider(self):
        """
        Acquire token from Azure AD for OpenAI.
        :return: The access token for OpenAI.
        """

        from azure.identity import AzureCliCredential, get_bearer_token_provider

        tenant_id = self.config_llm.get("AAD_TENANT_ID", "")
        scope = self.config_llm.get("AAD_API_SCOPE", "")

        identity = AzureCliCredential(tenant_id=tenant_id)
        bearer_provider = get_bearer_token_provider(identity, scope)
        return bearer_provider


class OpenAIError(Exception):
    request_id: str
    status_code: int
    message: Dict[str, Any]

    def __init__(self, status_code: int, message: Dict[str, Any], request_id: str):
        """
        The OpenAI API error class.
        :param status_code: The status code of the API response.
        :param message: The error message from the API response.
        :param request_id: The request ID of the API response.
        """
        self.status_code = status_code
        self.message = message
        self.request_id = request_id
        super().__init__(f"OpenAI API error: {status_code} {message}")

    def __str__(self):
        return f"OpenAI API error: {self.request_id} {self.status_code} {json.dumps(self.message, indent=2)}"
