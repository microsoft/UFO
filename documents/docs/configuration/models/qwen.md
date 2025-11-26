# Qwen Model

## Step 1: Obtain API Key

Qwen (Tongyi Qianwen) is developed by Alibaba DAMO Academy. To use Qwen models, go to [DashScope](https://dashscope.aliyun.com/), register an account, and obtain your API key. Detailed instructions are available in the [DashScope documentation](https://help.aliyun.com/zh/dashscope/developer-reference/activate-dashscope-and-create-an-api-key) (Chinese).

## Step 2: Configure Agent Settings

Configure the `HOST_AGENT` and `APP_AGENT` in the `config/ufo/agents.yaml` file to use the Qwen model.

If the file doesn't exist, copy it from the template:

```powershell
Copy-Item config\ufo\agents.yaml.template config\ufo\agents.yaml
```

Edit `config/ufo/agents.yaml` with your Qwen configuration:

```yaml
HOST_AGENT:
  VISUAL_MODE: True  # Enable visual mode for vision-capable models
  API_TYPE: "qwen"  # Use Qwen API
  API_KEY: "YOUR_QWEN_API_KEY"  # Your DashScope API key
  API_MODEL: "qwen-vl-max"  # Model name (e.g., qwen-vl-max, qwen-max)

APP_AGENT:
  VISUAL_MODE: True
  API_TYPE: "qwen"
  API_KEY: "YOUR_QWEN_API_KEY"
  API_MODEL: "qwen-vl-max"
```

**Configuration Fields:**

- **`VISUAL_MODE`**: Set to `True` for vision-capable models (qwen-vl-*). Set to `False` for text-only models
- **`API_TYPE`**: Use `"qwen"` for Qwen API (case-sensitive in code: lowercase)
- **`API_KEY`**: Your DashScope API key
- **`API_MODEL`**: Model identifier (see [Qwen model list](https://help.aliyun.com/zh/dashscope/developer-reference/model-square/))

**Available Models:**

- **Qwen-VL-Max**: `qwen-vl-max` - Vision and language model
- **Qwen-Max**: `qwen-max` - Text-only advanced model
- **Qwen-Plus**: `qwen-plus` - Balanced performance model

**For detailed configuration options, see:**

- [Agent Configuration Guide](../system/agents_config.md) - Complete agent settings reference
- [Model Configuration Overview](overview.md) - Compare different LLM providers

## Step 3: Start Using UFO

After configuration, you can start using UFO with the Qwen model. Refer to the [Quick Start Guide](../../getting_started/quick_start_ufo2.md) for detailed instructions on running your first tasks.
