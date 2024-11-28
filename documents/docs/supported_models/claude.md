# Anthropic Claude

## Step 1
To use the Claude API, you need to create an account on the [Claude website](https://www.anthropic.com/) and access the API key.

## Step 2
You may need to install additional dependencies to use the Claude API. You can install the dependencies using the following command:

```bash
pip install -U anthropic==0.37.1
```

## Step 3
Configure the `HOST_AGENT` and `APP_AGENT` in the `config.yaml` file (rename the `config_template.yaml` file to `config.yaml`) to use the Claude API. The following is an example configuration for the Claude API:

```yaml
VISUAL_MODE: True, # Whether to use visual mode to understand screenshots and take actions
API_TYPE: "Claude" ,
API_KEY: "YOUR_KEY",  
API_MODEL: "YOUR_MODEL"
```

!!! tip
    If you set `VISUAL_MODE` to `True`, make sure the `API_MODEL` supports visual inputs.
!!! tip
    `API_MODEL` is the model name of Claude LLM API. You can find the model name in the [Claude LLM model](https://www.anthropic.com/pricing#anthropic-api) list. 

## Step 4
After configuring the `HOST_AGENT` and `APP_AGENT` with the Claude API, you can start using UFO to interact with the Claude API for various tasks on Windows OS. Please refer to the [Quick Start Guide](../getting_started/quick_start.md) for more details on how to get started with UFO.