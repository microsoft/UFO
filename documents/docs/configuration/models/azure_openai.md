# Azure OpenAI (AOAI)

## Step 1: Create Azure OpenAI Resource

To use the Azure OpenAI API, create an account on the [Azure OpenAI website](https://azure.microsoft.com/en-us/products/ai-services/openai-service). After creating an account, deploy a model and obtain your API key and endpoint.

## Step 2: Configure Agent Settings

Configure the `HOST_AGENT` and `APP_AGENT` in the `config/ufo/agents.yaml` file to use the Azure OpenAI API.

If the file doesn't exist, copy it from the template:

```powershell
Copy-Item config\ufo\agents.yaml.template config\ufo\agents.yaml
```

Edit `config/ufo/agents.yaml` with your Azure OpenAI configuration:

### Option 1: API Key Authentication (Recommended for Development)

```yaml
HOST_AGENT:
  VISUAL_MODE: True  # Enable visual mode to understand screenshots
  REASONING_MODEL: False  # Set to True for o-series models
  API_TYPE: "aoai"  # Use Azure OpenAI API
  API_BASE: "https://YOUR_RESOURCE.openai.azure.com"  # Your Azure endpoint
  API_KEY: "YOUR_AOAI_KEY"  # Your Azure OpenAI API key
  API_VERSION: "2024-02-15-preview"  # API version
  API_MODEL: "gpt-4o"  # Model name
  API_DEPLOYMENT_ID: "YOUR_DEPLOYMENT_ID"  # Your deployment name

APP_AGENT:
  VISUAL_MODE: True
  REASONING_MODEL: False
  API_TYPE: "aoai"
  API_BASE: "https://YOUR_RESOURCE.openai.azure.com"
  API_KEY: "YOUR_AOAI_KEY"
  API_VERSION: "2024-02-15-preview"
  API_MODEL: "gpt-4o-mini"  # Use gpt-4o-mini for cost efficiency
  API_DEPLOYMENT_ID: "YOUR_DEPLOYMENT_ID"
```

### Option 2: Azure AD Authentication (Recommended for Production)

For Azure Active Directory authentication, use `API_TYPE: "azure_ad"`:

```yaml
HOST_AGENT:
  VISUAL_MODE: True
  REASONING_MODEL: False
  API_TYPE: "azure_ad"  # Use Azure AD authentication
  API_BASE: "https://YOUR_RESOURCE.openai.azure.com"  # Your Azure endpoint
  API_VERSION: "2024-02-15-preview"
  API_MODEL: "gpt-4o"
  API_DEPLOYMENT_ID: "YOUR_DEPLOYMENT_ID"
  
  # Azure AD Configuration
  AAD_TENANT_ID: "YOUR_TENANT_ID"  # Your Azure tenant ID
  AAD_API_SCOPE: "YOUR_SCOPE"  # Your API scope
  AAD_API_SCOPE_BASE: "YOUR_SCOPE_BASE"  # Scope base (without api:// prefix)

APP_AGENT:
  VISUAL_MODE: True
  REASONING_MODEL: False
  API_TYPE: "azure_ad"
  API_BASE: "https://YOUR_RESOURCE.openai.azure.com"
  API_VERSION: "2024-02-15-preview"
  API_MODEL: "gpt-4o-mini"
  API_DEPLOYMENT_ID: "YOUR_DEPLOYMENT_ID"
  AAD_TENANT_ID: "YOUR_TENANT_ID"
  AAD_API_SCOPE: "YOUR_SCOPE"
  AAD_API_SCOPE_BASE: "YOUR_SCOPE_BASE"
```

**Configuration Fields:**

- **`VISUAL_MODE`**: Set to `True` to enable vision capabilities. Ensure your deployment supports visual inputs
- **`API_TYPE`**: Use `"aoai"` for API key auth or `"azure_ad"` for Azure AD auth
- **`API_BASE`**: Your Azure OpenAI endpoint URL (format: `https://{resource-name}.openai.azure.com`)
- **`API_KEY`**: Your Azure OpenAI API key (not needed for Azure AD auth)
- **`API_VERSION`**: Azure API version (e.g., `"2024-02-15-preview"`)
- **`API_MODEL`**: Model identifier (e.g., `gpt-4o`, `gpt-4o-mini`)
- **`API_DEPLOYMENT_ID`**: Your Azure deployment name (required for AOAI)
- **`AAD_TENANT_ID`**: Azure tenant ID (required for Azure AD auth)
- **`AAD_API_SCOPE`**: Azure AD API scope (required for Azure AD auth)
- **`AAD_API_SCOPE_BASE`**: Scope base without `api://` prefix (required for Azure AD auth)

**For detailed configuration options, see:**

- [Agent Configuration Guide](../system/agents_config.md) - Complete agent settings reference
- [Model Configuration Overview](overview.md) - Compare different LLM providers
- [OpenAI](openai.md) - Standard OpenAI API setup

## Step 3: Start Using UFO

After configuration, you can start using UFO with the Azure OpenAI API. Refer to the [Quick Start Guide](../../getting_started/quick_start_ufo2.md) for detailed instructions on running your first tasks.