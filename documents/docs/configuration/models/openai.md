# OpenAI

## Step 1: Obtain API Key

To use the OpenAI API, create an account on the [OpenAI website](https://platform.openai.com/signup). After creating an account, you can access your API key from the [API keys page](https://platform.openai.com/account/api-keys).

## Step 2: Configure Agent Settings

After obtaining the API key, configure the `HOST_AGENT` and `APP_AGENT` in the `config/ufo/agents.yaml` file to use the OpenAI API.

If the file doesn't exist, copy it from the template:

```powershell
Copy-Item config\ufo\agents.yaml.template config\ufo\agents.yaml
```

Edit `config/ufo/agents.yaml` with your OpenAI configuration:

```yaml
HOST_AGENT:
  VISUAL_MODE: True  # Enable visual mode to understand screenshots
  REASONING_MODEL: False  # Set to True for o-series models (o1, o3, o3-mini)
  API_TYPE: "openai"  # Use OpenAI API
  API_BASE: "https://api.openai.com/v1"  # OpenAI API endpoint
  API_KEY: "sk-YOUR_KEY_HERE"  # Your OpenAI API key (starts with sk-)
  API_VERSION: "2025-02-01-preview"  # API version
  API_MODEL: "gpt-4o"  # Model name (gpt-4o, gpt-4o-mini, etc.)

APP_AGENT:
  VISUAL_MODE: True
  REASONING_MODEL: False
  API_TYPE: "openai"
  API_BASE: "https://api.openai.com/v1"
  API_KEY: "sk-YOUR_KEY_HERE"
  API_VERSION: "2025-02-01-preview"
  API_MODEL: "gpt-4o-mini"  # Use gpt-4o-mini for cost efficiency
```

**Configuration Fields:**

- **`VISUAL_MODE`**: Set to `True` to enable vision capabilities. Ensure your selected model supports visual inputs (see [OpenAI models](https://platform.openai.com/docs/models))
- **`REASONING_MODEL`**: Set to `True` when using o-series models (o1, o3, o3-mini) which have different behavior
- **`API_TYPE`**: Use `"openai"` for OpenAI API
- **`API_BASE`**: OpenAI API base URL - `https://api.openai.com/v1`
- **`API_KEY`**: Your OpenAI API key from the API keys page
- **`API_VERSION`**: API version identifier
- **`API_MODEL`**: Model identifier (e.g., `gpt-4o`, `gpt-4o-mini`, `gpt-4-turbo`)

**For detailed configuration options, see:**

- [Agent Configuration Guide](../system/agents_config.md) - Complete agent settings reference
- [Model Configuration Overview](overview.md) - Compare different LLM providers
- [Azure OpenAI](azure_openai.md) - Alternative Azure-hosted OpenAI setup

## Step 3: Start Using UFO

After configuration, you can start using UFO with the OpenAI API. Refer to the [Quick Start Guide](../../getting_started/quick_start_ufo2.md) for detailed instructions on running your first tasks.