# Anthropic Claude

## Step 1: Obtain API Key

To use the Claude API, create an account on the [Anthropic Console](https://console.anthropic.com/) and access your API key from the API keys section.

## Step 2: Install Dependencies

Install the required Anthropic Python package:

```bash
pip install -U anthropic==0.37.1
```

## Step 3: Configure Agent Settings

Configure the `HOST_AGENT` and `APP_AGENT` in the `config/ufo/agents.yaml` file to use the Claude API.

If the file doesn't exist, copy it from the template:

```powershell
Copy-Item config\ufo\agents.yaml.template config\ufo\agents.yaml
```

Edit `config/ufo/agents.yaml` with your Claude configuration:

```yaml
HOST_AGENT:
  VISUAL_MODE: True  # Enable visual mode to understand screenshots
  API_TYPE: "claude"  # Use Claude API
  API_BASE: "https://api.anthropic.com"  # Claude API endpoint
  API_KEY: "YOUR_CLAUDE_API_KEY"  # Your Claude API key
  API_MODEL: "claude-3-5-sonnet-20241022"  # Model name
  API_VERSION: "2023-06-01"  # API version

APP_AGENT:
  VISUAL_MODE: True
  API_TYPE: "claude"
  API_BASE: "https://api.anthropic.com"
  API_KEY: "YOUR_CLAUDE_API_KEY"
  API_MODEL: "claude-3-5-sonnet-20241022"
  API_VERSION: "2023-06-01"
```

**Configuration Fields:**

- **`VISUAL_MODE`**: Set to `True` to enable vision capabilities. Most Claude 3+ models support visual inputs (see [Claude models](https://www.anthropic.com/pricing#anthropic-api))
- **`API_TYPE`**: Use `"claude"` for Claude API (case-sensitive in code: lowercase)
- **`API_BASE`**: Claude API endpoint - `https://api.anthropic.com`
- **`API_KEY`**: Your Anthropic API key from the console
- **`API_MODEL`**: Model identifier (e.g., `claude-3-5-sonnet-20241022`, `claude-3-opus-20240229`)
- **`API_VERSION`**: API version identifier

**Available Models:**

- **Claude 3.5 Sonnet**: `claude-3-5-sonnet-20241022` - Best balance of intelligence and speed
- **Claude 3 Opus**: `claude-3-opus-20240229` - Most capable model
- **Claude 3 Sonnet**: `claude-3-sonnet-20240229` - Balanced performance
- **Claude 3 Haiku**: `claude-3-haiku-20240307` - Fast and cost-effective

**For detailed configuration options, see:**

- [Agent Configuration Guide](../system/agents_config.md) - Complete agent settings reference
- [Model Configuration Overview](overview.md) - Compare different LLM providers
- [Anthropic Documentation](https://docs.anthropic.com/) - Official Claude API docs

## Step 4: Start Using UFO

After configuration, you can start using UFO with the Claude API. Refer to the [Quick Start Guide](../../getting_started/quick_start_ufo2.md) for detailed instructions on running your first tasks.