# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import datetime
import os
import shutil
import sys
from typing import Any, Callable, Literal, Optional

import openai
from openai import AzureOpenAI, OpenAI
import functools

from ufo.llm.base import BaseService


class OpenAIService(BaseService):
    """
    The OpenAI service class to interact with the OpenAI API.
    """

    def __init__(self, config, agent_type: str) -> None:
        """
        Create an OpenAI service instance.
        :param config: The configuration for the OpenAI service.
        :param agent_type: The type of the agent.
        """
        self.config_llm = config[agent_type]
        self.config = config
        self.api_type = self.config_llm["API_TYPE"].lower()
        self.max_retry = self.config["MAX_RETRY"]
        self.prices = self.config["PRICES"]
        assert self.api_type in ["openai", "aoai", "azure_ad"], "Invalid API type"

        self.client: OpenAI = OpenAIService.get_openai_client(
            self.api_type,
            self.config_llm["API_BASE"],
            self.max_retry,
            self.config["TIMEOUT"],
            self.config_llm.get("API_KEY", ""),
            self.config_llm.get("API_VERSION", ""),
            aad_api_scope_base=self.config_llm.get("AAD_API_SCOPE_BASE", ""),
            aad_tenant_id=self.config_llm.get("AAD_TENANT_ID", ""),
        )

    def chat_completion(
        self,
        messages,
        n,
        stream: bool = False,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        top_p: Optional[float] = None,
        **kwargs: Any,
    ):
        """
        Generates completions for a given conversation using the OpenAI Chat API.

        Args:
            messages (List[Dict[str, str]]): The list of messages in the conversation.
                Each message should have a 'role' (either 'system', 'user', or 'assistant')
                and 'content' (the content of the message).
            n (int): The number of completions to generate.
            stream (bool, optional): Whether to stream the API response. Defaults to False.
            temperature (float, optional): The temperature parameter for randomness in the output.
                Higher values (e.g., 0.8) make the output more random, while lower values (e.g., 0.2) make it more deterministic.
                If not provided, the default value from the configuration will be used.
            max_tokens (int, optional): The maximum number of tokens in the generated completion.
                If not provided, the default value from the configuration will be used.
            top_p (float, optional): The top-p parameter for nucleus sampling.
                It specifies the cumulative probability threshold for selecting the next token.
                If not provided, the default value from the configuration will be used.
            **kwargs: Additional keyword arguments to pass to the OpenAI API.

        Returns:
            Tuple[List[str], float]: A tuple containing a list of generated completions and the estimated cost.

        Raises:
            Exception: If there is an error in the OpenAI API request, such as a timeout, connection failure, invalid request, authentication error,
                permission error, rate limit error, or API error.
        """
        model = self.config_llm["API_MODEL"]

        temperature = (
            temperature if temperature is not None else self.config["TEMPERATURE"]
        )
        max_tokens = max_tokens if max_tokens is not None else self.config["MAX_TOKENS"]
        top_p = top_p if top_p is not None else self.config["TOP_P"]

        try:
            response: Any = self.client.chat.completions.create(
                model=model,
                messages=messages,  # type: ignore
                n=n,
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=top_p,
                stream=stream,
                **kwargs,
            )

            usage = response.usage
            prompt_tokens = usage.prompt_tokens
            completion_tokens = usage.completion_tokens

            cost = self.get_cost_estimator(
                self.api_type, model, self.prices, prompt_tokens, completion_tokens
            )

            return [response.choices[i].message.content for i in range(n)], cost

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
        acquire token from Azure AD for OpenAI

        Parameters
        ----------
        token_cache_file : str, optional
            path to the token cache file, by default 'aoai-token-cache.bin' in the current directory
        client_id : Optional[str], optional
            client id for AAD app, by default None
        client_secret : Optional[str], optional
            client secret for AAD app, by default None
        use_azure_cli : Optional[bool], optional
            use Azure CLI for authentication, by default None. If AzCli has been installed and logged in,
            it will be used for authentication. This is recommended for headless environments and AzCLI takes
            care of token cache and token refresh.
        use_broker_login : Optional[bool], optional
            use broker login for authentication, by default None.
            If not specified, it will be enabled for known supported environments (e.g. Windows, macOS, WSL, VSCode),
            but sometimes it may not always could cache the token for long-term usage.
            In such cases, you can disable it by setting it to False.
        use_managed_identity : Optional[bool], optional
            use managed identity for authentication, by default None.
            If not specified, it will use user assigned managed identity if client_id is specified,
            For use system assigned managed identity, client_id could be None but need to set use_managed_identity to True.
        use_device_code : Optional[bool], optional
            use device code for authentication, by default None. If not specified, it will use interactive login on supported platform.

        Returns
        -------
        str
            access token for OpenAI
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
