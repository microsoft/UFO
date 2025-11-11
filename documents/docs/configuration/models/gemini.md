# Google Gemini

## Step 1: Obtain API Key

To use the Google Gemini API, create an account on [Google AI Studio](https://ai.google.dev/) and generate your API key from the API keys section.

## Step 2: Install Dependencies

Install the required Google GenAI Python package:

```bash
pip install -U google-genai==1.12.1
```

## Step 3: Configure Agent Settings

Configure the `HOST_AGENT` and `APP_AGENT` in the `config/ufo/agents.yaml` file to use the Google Gemini API.

If the file doesn't exist, copy it from the template:

```powershell
Copy-Item config\ufo\agents.yaml.template config\ufo\agents.yaml
```

Edit `config/ufo/agents.yaml` with your Gemini configuration:

```yaml
HOST_AGENT:
  VISUAL_MODE: True  # Enable visual mode to understand screenshots
  JSON_SCHEMA: True  # Enable JSON schema for structured responses
  API_TYPE: "gemini"  # Use Gemini API
  API_BASE: "https://generativelanguage.googleapis.com"  # Gemini API endpoint
  API_KEY: "YOUR_GEMINI_API_KEY"  # Your Gemini API key
  API_MODEL: "gemini-2.0-flash-exp"  # Model name
  API_VERSION: "v1beta"  # API version

APP_AGENT:
  VISUAL_MODE: True
  JSON_SCHEMA: True
  API_TYPE: "gemini"
  API_BASE: "https://generativelanguage.googleapis.com"
  API_KEY: "YOUR_GEMINI_API_KEY"
  API_MODEL: "gemini-2.0-flash-exp"
  API_VERSION: "v1beta"
```

**Configuration Fields:**

- **`VISUAL_MODE`**: Set to `True` to enable vision capabilities. Most Gemini models support visual inputs (see [Gemini models](https://ai.google.dev/gemini-api/docs/models/gemini))
- **`JSON_SCHEMA`**: Set to `True` to enable structured JSON output formatting
- **`API_TYPE`**: Use `"gemini"` for Google Gemini API (case-sensitive in code: lowercase)
- **`API_BASE`**: Gemini API endpoint - `https://generativelanguage.googleapis.com`
- **`API_KEY`**: Your Google AI API key
- **`API_MODEL`**: Model identifier (e.g., `gemini-2.0-flash-exp`, `gemini-1.5-pro`)
- **`API_VERSION`**: API version (typically `v1beta`)

**Available Models:**

- **Gemini 2.0 Flash**: `gemini-2.0-flash-exp` - Latest experimental model with multimodal capabilities
- **Gemini 1.5 Pro**: `gemini-1.5-pro` - Advanced reasoning and long context
- **Gemini 1.5 Flash**: `gemini-1.5-flash` - Fast and efficient

**Rate Limits:**

If you encounter `429 Resource has been exhausted` errors, you've hit the rate limit of your Gemini API quota. Consider:
- Reducing request frequency
- Upgrading your API tier
- Using exponential backoff for retries

**For detailed configuration options, see:**

- [Agent Configuration Guide](../system/agents_config.md) - Complete agent settings reference
- [Model Configuration Overview](overview.md) - Compare different LLM providers
- [Gemini API Documentation](https://ai.google.dev/gemini-api) - Official Gemini API docs

## Step 4: Start Using UFO

After configuration, you can start using UFO with the Gemini API. Refer to the [Quick Start Guide](../../getting_started/quick_start_ufo2.md) for detailed instructions on running your first tasks.