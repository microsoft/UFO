# DeepSeek Model

## Step 1
DeepSeek is developed by Alibaba DAMO Academy. To use the DeepSeek models, Go to [DeepSeek](https://www.deepseek.com/) and register an account and get the API key.

## Step 2
Configure the `HOST_AGENT` and `APP_AGENT` in the `config.yaml` file (rename the `config_template.yaml` file to `config.yaml`) to use the DeepSeek model. The following is an example configuration for the DeepSeek model:

```yaml
    VISUAL_MODE: False, # Whether to use visual mode to understand screenshots and take actions
    API_TYPE: "deepseek" , # The API type, "deepseek" for the DeepSeek model.
    API_KEY: "YOUR_KEY",  # The DeepSeek API key
    API_MODEL: "YOUR_MODEL"  # The DeepSeek model name
```

!!! tip
    Most DeepSeek models don't support visual inputs, rembmer to set `VISUAL_MODE` to `False`.

## Step 3
After configuring the `HOST_AGENT` and `APP_AGENT` with the DeepSeek model, you can start using UFO to interact with the DeepSeek model for various tasks on Windows OS. Please refer to the [Quick Start Guide](../getting_started/quick_start.md) for more details on how to get started with UFO.
