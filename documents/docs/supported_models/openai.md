# OpenAI

## Step 1

To use the OpenAI API, you need to create an account on the [OpenAI website](https://platform.openai.com/signup). After creating an account, you can access the API key from the [API keys page](https://platform.openai.com/account/api-keys).

## Step 2

After obtaining the API key, you can configure the `HOST_AGENT` and `APP_AGENT` in the `config.yaml` file (rename the `config_template.yaml` file to `config.yaml`) to use the OpenAI API. The following is an example configuration for the OpenAI API:

```yaml
VISUAL_MODE: True, # Whether to use visual mode to understand screenshots and take actions
API_TYPE: "openai" , # The API type, "openai" for the OpenAI API, "aoai" for the AOAI API, 'azure_ad' for the ad authority of the AOAI API.  
API_BASE: "https://api.openai.com/v1/chat/completions", # The the OpenAI API endpoint, "https://api.openai.com/v1/chat/completions" for the OpenAI API.
API_KEY: "sk-",  # The OpenAI API key, begin with sk-
API_VERSION: "2024-02-15-preview", # The version of the API, "2024-02-15-preview" by default
API_MODEL: "gpt-4-vision-preview",  # The OpenAI model name, "gpt-4-vision-preview" by default. You may also use "gpt-4o" for using the GPT-4O model.
```

!!! tip
    If you set `VISUAL_MODE` to `True`, make sure the `API_MODEL` supports visual inputs. You can find the list of models [here](https://platform.openai.com/docs/models).



## Step 3
After configuring the `HOST_AGENT` and `APP_AGENT` with the OpenAI API, you can start using UFO to interact with the OpenAI API for various tasks on Windows OS. Please refer to the [Quick Start Guide](../getting_started/quick_start.md) for more details on how to get started with UFO.