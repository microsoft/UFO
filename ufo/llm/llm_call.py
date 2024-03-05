# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import requests
import time
import datetime
from typing import Literal, Optional
from ..config.config import load_config
from ..utils import print_with_color


configs = load_config()
available_models = Literal[ #only GPT4V could be used 
    "gpt-4-visual-preview",
]

def encode_image(image_path: str, mime_type: Optional[str] = None) -> str:
    import base64
    import os
    import mimetypes
    file_name = os.path.basename(image_path)
    mime_type = mime_type if mime_type is not None else mimetypes.guess_type(file_name)[0]
    with open(image_path, "rb") as image_file:
        encoded_image = base64.b64encode(image_file.read()).decode('ascii')
        
    if mime_type is None or not mime_type.startswith("image/"):
        print("Warning: mime_type is not specified or not an image mime type. Defaulting to png.")
        mime_type = "image/png"
        
    image_url = f"data:{mime_type};base64," + encoded_image
    return image_url



def get_openai_token(
    token_cache_file: str = 'apim-token-cache.bin',
    client_id: Optional[str] = None,
    client_secret: Optional[str] = None,
) -> str:
    '''
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
    '''
    import msal
    import os

    cache = msal.SerializableTokenCache()

    def save_cache():
        if token_cache_file is not None and cache.has_state_changed:
            with open(token_cache_file, "w") as cache_file:
                cache_file.write(cache.serialize())
    if os.path.exists(token_cache_file):
        cache.deserialize(open(token_cache_file, "r").read())

    authority = "https://login.microsoftonline.com/" + configs["AAD_TENANT_ID"]
    api_scope_base = "api://" + configs["AAD_API_SCOPE_BASE"]

    if client_id is not None and client_secret is not None:
        app = msal.ConfidentialClientApplication(
            client_id=client_id,
            client_credential=client_secret,
            authority=authority,
            token_cache=cache
        )
        result = app.acquire_token_for_client(
            scopes=[
                api_scope_base + "/.default",
            ])
        if "access_token" in result:
            return result['access_token']
        else:
            print(result.get("error"))
            print(result.get("error_description"))
            raise Exception(
                "Authentication failed for acquiring AAD token for your organization")

    scopes = [api_scope_base + "/" + configs["AAD_API_SCOPE"]]
    app = msal.PublicClientApplication(
        configs["AAD_API_SCOPE_BASE"],
        authority=authority,
        token_cache=cache
    )
    result = None
    for account in app.get_accounts():
        try:
            result = app.acquire_token_silent(scopes, account=account)
            if result is not None and "access_token" in result:
                save_cache()
                return result['access_token']
            result = None
        except Exception:
            continue

    accounts_in_cache = cache.find(msal.TokenCache.CredentialType.ACCOUNT)
    for account in accounts_in_cache:
        try:
            refresh_token = cache.find(
                msal.CredentialType.REFRESH_TOKEN,
                query={
                    "home_account_id": account["home_account_id"]
                })[0]
            result = app.acquire_token_by_refresh_token(
                refresh_token["secret"], scopes=scopes)
            if result is not None and "access_token" in result:
                save_cache()
                return result['access_token']
            result = None
        except Exception:
            pass

    if result is None:
        print("no token available from cache, acquiring token from AAD")
        # The pattern to acquire a token looks like this.
        flow = app.initiate_device_flow(scopes=scopes)
        print(flow['message'])
        result = app.acquire_token_by_device_flow(flow=flow)
        if result is not None and "access_token" in result:
            save_cache()
            return result['access_token']
        else:
            print(result.get("error"))
            print(result.get("error_description"))
            raise Exception(
                "Authentication failed for acquiring AAD token for your organization")


def get_chat_completion(
    model: available_models = None,
    client_id: Optional[str] = None,
    client_secret: Optional[str] = None,
    *args,
    **kwargs
):
    """
    helper function for getting chat completion from your organization
    """
    import openai

    model_name: str = \
        model if model is not None else \
        kwargs.get("engine") if kwargs.get("engine") is not None else \
        None
    
    if "engine" in kwargs:
        del kwargs["engine"]

    client = openai.AzureOpenAI(
        api_version=configs["AAD_API_VERSION"],
        azure_endpoint=configs["OPENAI_API_BASE"],
        azure_ad_token=get_openai_token(client_id=client_id, client_secret=client_secret),
    )

    response = client.chat.completions.create(
        model=model_name,
        *args,
        **kwargs
    )
 
    return response

def auto_refresh_token(
    token_cache_file: str = 'apim-token-cache.bin',
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

        openai.api_type = configs["API_TYPE"]
        openai.base_url = configs["OPENAI_API_BASE"]
        openai.api_version = configs["AAD_API_VERSION"]
        openai.api_key = get_openai_token(
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
        raise Exception(
            "failed to acquire token from AAD for your organization", e)

    thread = threading.Thread(target=refresh_token_thread, daemon=True)
    thread.start()

    def stop():
        thread.stop()

    return stop


def get_gptv_completion(messages, headers):
    """
    Get GPT-V completion from messages.
    messages: The messages to be sent to GPT-V.
    headers: The headers of the request.
    endpoint: The endpoint of the request.
    max_tokens: The maximum number of tokens to generate.
    temperature: The sampling temperature.
    model: The model to use.
    max_retry: The maximum number of retries.
    return: The response of the request.
    """
    aad = configs['API_TYPE'].lower() == 'azure'
    if not aad:
        payload = {
            "messages": messages,
            "temperature": configs["TEMPERATURE"],
            "max_tokens": configs["MAX_TOKENS"],
            "top_p": configs["TOP_P"],
            "model": configs["OPENAI_API_MODEL"]
        }

    for _ in range(configs["MAX_RETRY"]):
        try:
            if not aad :
                response = requests.post(configs["OPENAI_API_BASE"], headers=headers, json=payload)

                response_json = response.json()
                response.raise_for_status()  # Will raise an HTTPError if the HTTP request returned an unsuccessful status code
                

                if "choices" not in response_json:
                    print_with_color(f"GPT Error: No Reply", "red")
                    continue

                if "error" not in response_json:
                    usage = response_json.get("usage", {})
                    prompt_tokens = usage.get("prompt_tokens", 0)
                    completion_tokens = usage.get("completion_tokens", 0)
            else:
                response = get_chat_completion(
                    engine=configs["OPENAI_API_MODEL"],
                    messages = messages,
                    max_tokens = configs["MAX_TOKENS"],
                    temperature = configs["TEMPERATURE"],
                    top_p = configs["TOP_P"],
                )
                
                if "error" not in response:
                    usage = response.usage
                    prompt_tokens = usage.prompt_tokens
                    completion_tokens = usage.completion_tokens
                response_json = response

            cost = prompt_tokens / 1000 * 0.01 + completion_tokens / 1000 * 0.03
             
            return response_json, cost
        except requests.RequestException as e:
            print_with_color(f"Error making API request: {e}", "red")
            print_with_color(str(response_json), "red")
            try:
                print_with_color(response.json(), "red")
            except:
                _ 
            time.sleep(3)
            continue
