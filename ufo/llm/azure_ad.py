
import datetime
from typing import Literal, Optional
from ..config.config import load_config

configs = load_config()
available_models = Literal[ #only GPT4V could be used 
    "gpt-4-visual-preview",
]

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

        openai.api_type = "azure" if configs["API_TYPE"] == "azure_ad" else configs["API_TYPE"]
        openai.base_url = configs["OPENAI_API_BASE"]
        openai.api_version = configs["API_VERSION"]
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
        api_version=configs["API_VERSION"],
        azure_endpoint=configs["OPENAI_API_BASE"],
        azure_ad_token=get_openai_token(client_id=client_id, client_secret=client_secret),
    )

    response = client.chat.completions.create(
        model=model_name,
        *args,
        **kwargs
    )
 
    return response
