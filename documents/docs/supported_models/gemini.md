# Google Gemini

## Step 1
To use the Google Gemini API, you need to create an account on the [Google Gemini website](https://ai.google.dev/) and access the API key.

## Step 2
You may need to install additional dependencies to use the Google Gemini API. You can install the dependencies using the following command:

```bash
pip install -U google-genai==1.12.1
```

## Step 3
Configure the `HOST_AGENT` and `APP_AGENT` in the `config.yaml` file (rename the `config_template.yaml` file to `config.yaml`) to use the Google Gemini API. The following is an example configuration for the Google Gemini API:

```yaml
VISUAL_MODE: True, # Whether to use visual mode to understand screenshots and take actions
API_TYPE: "Gemini" ,
API_KEY: "YOUR_KEY",  
API_MODEL: "YOUR_MODEL"
```

!!! tip
    If you set `VISUAL_MODE` to `True`, make sure the `API_MODEL` supports visual inputs.
!!! tip
    `API_MODEL` is the model name of Gemini LLM API. You can find the model name in the [Gemini LLM model](https://ai.google.dev/gemini-api) list. If you meet the `429` Resource has been exhausted (e.g. check quota)., it may because the rate limit of your Gemini API.

## Step 4
After configuring the `HOST_AGENT` and `APP_AGENT` with the Gemini API, you can start using UFO to interact with the Gemini API for various tasks on Windows OS. Please refer to the [Quick Start Guide](../getting_started/quick_start.md) for more details on how to get started with UFO.