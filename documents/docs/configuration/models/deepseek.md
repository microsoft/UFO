# DeepSeek Model

## Step 1: Obtain API Key

DeepSeek is developed by DeepSeek AI. To use DeepSeek models, go to [DeepSeek Platform](https://www.deepseek.com/), register an account, and obtain your API key from the API management console.

## Step 2: Configure Agent Settings

Configure the `HOST_AGENT` and `APP_AGENT` in the `config/ufo/agents.yaml` file to use the DeepSeek model.

If the file doesn't exist, copy it from the template:

```powershell
Copy-Item config\ufo\agents.yaml.template config\ufo\agents.yaml
```

Edit `config/ufo/agents.yaml` with your DeepSeek configuration:

```yaml
HOST_AGENT:
  VISUAL_MODE: False  # DeepSeek models typically don't support visual inputs
  API_TYPE: "deepseek"  # Use DeepSeek API
  API_KEY: "YOUR_DEEPSEEK_API_KEY"  # Your DeepSeek API key
  API_MODEL: "deepseek-chat"  # Model name

APP_AGENT:
  VISUAL_MODE: False
  API_TYPE: "deepseek"
  API_KEY: "YOUR_DEEPSEEK_API_KEY"
  API_MODEL: "deepseek-chat"
```

**Configuration Fields:**

- **`VISUAL_MODE`**: Set to `False` - Most DeepSeek models don't support visual inputs
- **`API_TYPE`**: Use `"deepseek"` for DeepSeek API (case-sensitive in code: lowercase)
- **`API_KEY`**: Your DeepSeek API key
- **`API_MODEL`**: Model identifier (e.g., `deepseek-chat`, `deepseek-coder`)

**Available Models:**

- **DeepSeek-Chat**: `deepseek-chat` - General conversation model
- **DeepSeek-Coder**: `deepseek-coder` - Code-specialized model

**For detailed configuration options, see:**

- [Agent Configuration Guide](../system/agents_config.md) - Complete agent settings reference
- [Model Configuration Overview](overview.md) - Compare different LLM providers

## Step 3: Start Using UFO

After configuration, you can start using UFO with the DeepSeek model. Refer to the [Quick Start Guide](../../getting_started/quick_start_ufo2.md) for detailed instructions on running your first tasks.

**Note:** Since DeepSeek models don't support visual mode, UFO will operate in text-only mode, which may limit some UI automation capabilities that rely on screenshot understanding.
