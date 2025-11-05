# Qwen Model

## Step 1
Qwen (Tongyi Qianwen) is developed by Alibaba DAMO Academy. To use the Qwen model, Go to [QWen](https://dashscope.aliyun.com/) and register an account and get the API key. More details can be found [here](https://help.aliyun.com/zh/dashscope/developer-reference/activate-dashscope-and-create-an-api-key?spm=a2c4g.11186623.0.0.7b5749d72j3SYU) (in Chinese).

## Step 2
Configure the `HOST_AGENT` and `APP_AGENT` in the `config.yaml` file (rename the `config_template.yaml` file to `config.yaml`) to use the Qwen model. The following is an example configuration for the Qwen model:

```yaml
    VISUAL_MODE: True, # Whether to use visual mode to understand screenshots and take actions
    API_TYPE: "qwen" , # The API type, "qwen" for the Qwen model.
    API_KEY: "YOUR_KEY",  # The Qwen API key
    API_MODEL: "YOUR_MODEL"  # The Qwen model name
```

!!! tip
    If you set `VISUAL_MODE` to `True`, make sure the `API_MODEL` supports visual inputs.

!!! tip
    `API_MODEL` is the model name of Qwen LLM API. You can find the model name in the [Qwen LLM model](https://help.aliyun.com/zh/dashscope/developer-reference/model-square/?spm=a2c4g.11186623.0.0.35a36ffdt97ljI) list.

## Step 3
After configuring the `HOST_AGENT` and `APP_AGENT` with the Qwen model, you can start using UFO to interact with the Qwen model for various tasks on Windows OS. Please refer to the [Quick Start Guide](../getting_started/quick_start.md) for more details on how to get started with UFO.
