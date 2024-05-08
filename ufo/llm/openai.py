# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import datetime
from typing import Any, Optional

import openai
from openai import AzureOpenAI, OpenAI

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
        self.client: OpenAI = (
            OpenAI(
                base_url=self.config_llm["API_BASE"],
                api_key=self.config_llm["API_KEY"],
                max_retries=self.max_retry,
                timeout=self.config["TIMEOUT"],
            )
            if self.api_type == "openai"
            else AzureOpenAI(
                max_retries=self.max_retry,
                timeout=self.config["TIMEOUT"],
                api_version=self.config_llm["API_VERSION"],
                azure_endpoint=self.config_llm["API_BASE"],
                api_key=(
                    self.config_llm["API_KEY"]
                    if self.api_type == "aoai"
                    else self.get_openai_token()
                ),
            )
        )
        if self.api_type == "azure_ad":
            self.auto_refresh_token()

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

    def get_openai_token(
        self,
        token_cache_file: str = "apim-token-cache.bin",
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
    ) -> str:
        """
        acquire token from Azure AD for your organization

        Parameters
        ----------
        token_cache_file : str, optional
            path to the token cache file, by default 'apim-token-cache.bin' in the current directory
        client_id : Optional[str], optional
            client id for AAD app, by default None
        client_secret : Optional[str], optional
            client secret for AAD app, by default None

        Returns
        -------
        str
            access token for your own organization
        """
        import os

        import msal

        cache = msal.SerializableTokenCache()

        def save_cache():
            if token_cache_file is not None and cache.has_state_changed:
                with open(token_cache_file, "w") as cache_file:
                    cache_file.write(cache.serialize())

        if os.path.exists(token_cache_file):
            cache.deserialize(open(token_cache_file, "r").read())

        authority = (
            "https://login.microsoftonline.com/" + self.config_llm["AAD_TENANT_ID"]
        )
        api_scope_base = "api://" + self.config_llm["AAD_API_SCOPE_BASE"]

        if client_id is not None and client_secret is not None:
            app = msal.ConfidentialClientApplication(
                client_id=client_id,
                client_credential=client_secret,
                authority=authority,
                token_cache=cache,
            )
            result = app.acquire_token_for_client(
                scopes=[
                    api_scope_base + "/.default",
                ]
            )
            if "access_token" in result:
                return result["access_token"]
            else:
                print(result.get("error"))
                print(result.get("error_description"))
                raise Exception(
                    "Authentication failed for acquiring AAD token for your organization"
                )

        scopes = [api_scope_base + "/" + self.config_llm["AAD_API_SCOPE"]]
        app = msal.PublicClientApplication(
            self.config_llm["AAD_API_SCOPE_BASE"],
            authority=authority,
            token_cache=cache,
        )
        result = None
        for account in app.get_accounts():
            try:
                result = app.acquire_token_silent(scopes, account=account)
                if result is not None and "access_token" in result:
                    save_cache()
                    return result["access_token"]
                result = None
            except Exception:
                continue

        accounts_in_cache = cache.find(msal.TokenCache.CredentialType.ACCOUNT)
        for account in accounts_in_cache:
            try:
                refresh_token = cache.find(
                    msal.CredentialType.REFRESH_TOKEN,
                    query={"home_account_id": account["home_account_id"]},
                )[0]
                result = app.acquire_token_by_refresh_token(
                    refresh_token["secret"], scopes=scopes
                )
                if result is not None and "access_token" in result:
                    save_cache()
                    return result["access_token"]
                result = None
            except Exception:
                pass

        if result is None:
            print("no token available from cache, acquiring token from AAD")
            # The pattern to acquire a token looks like this.
            flow = app.initiate_device_flow(scopes=scopes)
            print(flow["message"])
            result = app.acquire_token_by_device_flow(flow=flow)
            if result is not None and "access_token" in result:
                save_cache()
                return result["access_token"]
            else:
                print(result.get("error"))
                print(result.get("error_description"))
                raise Exception(
                    "Authentication failed for acquiring AAD token for your organization"
                )

    def auto_refresh_token(
        self,
        token_cache_file: str = "apim-token-cache.bin",
        interval: datetime.timedelta = datetime.timedelta(minutes=15),
        on_token_update: callable = None,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
    ) -> callable:
        """
        helper function for auto refreshing token from your organization

        Parameters
        ----------
        token_cache_file : str, optional
            path to the token cache file, by default 'apim-token-cache.bin' in the current directory
        interval : datetime.timedelta, optional
            interval for refreshing token, by default 15 minutes
        on_token_update : callable, optional
            callback function to be called when token is updated, by default None. In the callback function, you can get token from openai.api_key

        Returns
        -------
        callable
            a callable function that can be used to stop the auto refresh thread
        """

        import threading

        def update_token():
            import openai

            openai.api_type = (
                "azure"
                if self.config_llm["API_TYPE"] == "azure_ad"
                else self.config_llm["API_TYPE"]
            )
            openai.base_url = self.config_llm["API_BASE"]
            openai.api_version = self.config_llm["API_VERSION"]
            openai.api_key = self.get_openai_token(
                token_cache_file=token_cache_file,
                client_id=client_id,
                client_secret=client_secret,
            )

            if on_token_update is not None:
                on_token_update()

        def refresh_token_thread():
            import time

            while True:
                try:
                    update_token()
                except Exception as e:
                    print("failed to acquire token from AAD for your organization", e)
                time.sleep(interval.total_seconds())

        try:
            update_token()
        except Exception as e:
            raise Exception("failed to acquire token from AAD for your organization", e)

        thread = threading.Thread(target=refresh_token_thread, daemon=True)
        thread.start()

        def stop():
            thread.stop()

        return stop
