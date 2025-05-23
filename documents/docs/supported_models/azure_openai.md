# Azure OpenAI (AOAI)

## Step 1
To use the Azure OpenAI API, you need to create an account on the [Azure OpenAI website](https://azure.microsoft.com/en-us/products/ai-services/openai-service). After creating an account, you can deploy the AOAI API and access the API key.

## Step 2
After obtaining the API key, you can configure the `HOST_AGENT` and `APP_AGENT` in the `config.yaml` file (rename the `config_template.yaml` file to `config.yaml`) to use the Azure OpenAI API. The following is an example configuration for the Azure OpenAI API:

```yaml
VISUAL_MODE: True, # Whether to use visual mode to understand screenshots and take actions
API_TYPE: "aoai" , # The API type, "openai" for the OpenAI API, "aoai" for the AOAI API, 'azure_ad' for the ad authority of the AOAI API.  
API_BASE: "YOUR_ENDPOINT", #  The AOAI API address. Format: https://{your-resource-name}.openai.azure.com
API_KEY: "YOUR_KEY",  # The aoai API key
API_VERSION: "2024-02-15-preview", # The version of the API, "2024-02-15-preview" by default
API_MODEL: "gpt-4-vision-preview",  # The OpenAI model name, "gpt-4-vision-preview" by default. You may also use "gpt-4o" for using the GPT-4O model.
API_DEPLOYMENT_ID: "YOUR_AOAI_DEPLOYMENT", # The deployment id for the AOAI API
```

If you want to use AAD for authentication, you should also set the following configuration:

```yaml
    AAD_TENANT_ID: "YOUR_TENANT_ID", # Set the value to your tenant id for the llm model
    AAD_API_SCOPE: "YOUR_SCOPE", # Set the value to your scope for the llm model
    AAD_API_SCOPE_BASE: "YOUR_SCOPE_BASE" # Set the value to your scope base for the llm model, whose format is API://YOUR_SCOPE_BASE, and the only need is the YOUR_SCOPE_BASE
```

!!! tip
    If you set `VISUAL_MODE` to `True`, make sure the `API_DEPLOYMENT_ID` supports visual inputs.

## Step 3
After configuring the `HOST_AGENT` and `APP_AGENT` with the OpenAI API, you can start using UFO to interact with the AOAI API for various tasks on Windows OS. Please refer to the [Quick Start Guide](../getting_started/quick_start.md) for more details on how to get started with UFO.