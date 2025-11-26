# OpenAI CUA (Operator)

The [Operator](https://openai.com/index/computer-using-agent/) is a specialized agentic model tailored for Computer-Using Agents (CUA). It's currently available via the Azure OpenAI API (AOAI) using the [Response API](https://learn.microsoft.com/en-us/azure/ai-services/openai/how-to/responses?tabs=python-secure).

## Step 1: Create Azure OpenAI Resource

To use the Operator model, create an account on the [Azure OpenAI website](https://azure.microsoft.com/en-us/products/ai-services/openai-service). After creating an account, deploy the Operator model and access your API key.

## Step 2: Configure Operator Agent

Configure the `OPERATOR` in the `config/ufo/agents.yaml` file to use the Azure OpenAI Operator model.

If the file doesn't exist, copy it from the template:

```powershell
Copy-Item config\ufo\agents.yaml.template config\ufo\agents.yaml
```

Edit `config/ufo/agents.yaml` with your Operator configuration:

```yaml
OPERATOR:
  SCALER: [1024, 768]  # Visual input resolution [width, height]
  API_TYPE: "azure_ad"  # Use Azure AD authentication
  API_MODEL: "computer-use-preview-20250311"  # Operator model name
  API_VERSION: "2025-03-01-preview"  # API version for Operator
  API_BASE: "https://YOUR_RESOURCE.openai.azure.com"  # Your Azure endpoint
  
  # Azure AD Authentication (required)
  AAD_TENANT_ID: "YOUR_TENANT_ID"  # Your Azure tenant ID
  AAD_API_SCOPE: "YOUR_SCOPE"  # Your API scope
  AAD_API_SCOPE_BASE: "YOUR_SCOPE_BASE"  # Scope base (without api:// prefix)
```

**Configuration Fields:**

- **`SCALER`**: Resolution for visual input `[width, height]` (recommended: `[1024, 768]`)
- **`API_TYPE`**: Use `"azure_ad"` for Azure AD authentication (or `"aoai"` for API key auth)
- **`API_MODEL`**: Operator model identifier (e.g., `computer-use-preview-20250311`)
- **`API_VERSION`**: API version for Operator (e.g., `2025-03-01-preview`)
- **`API_BASE`**: Your Azure OpenAI endpoint URL
- **`AAD_TENANT_ID`**: Azure tenant ID (required for Azure AD auth)
- **`AAD_API_SCOPE`**: Azure AD API scope (required for Azure AD auth)
- **`AAD_API_SCOPE_BASE`**: Scope base without `api://` prefix (required for Azure AD auth)

**For API Key Authentication (Development):**

If you prefer API key authentication instead of Azure AD:

```yaml
OPERATOR:
  SCALER: [1024, 768]
  API_TYPE: "aoai"  # Use API key authentication
  API_MODEL: "computer-use-preview-20250311"
  API_VERSION: "2025-03-01-preview"
  API_BASE: "https://YOUR_RESOURCE.openai.azure.com"
  API_KEY: "YOUR_AOAI_KEY"  # Your Azure OpenAI API key
  API_DEPLOYMENT_ID: "YOUR_DEPLOYMENT_ID"  # Your deployment name
```

## Step 3: Run Operator in UFO

UFO supports running Operator in two modes:

1. **Standalone Agent**: Run Operator as a single agent
2. **As AppAgent**: Call Operator as a separate `AppAgent` from the `HostAgent`

Operator uses a specialized visual-only workflow different from other models and currently does not support the standard `AppAgent` workflow.

**For detailed usage instructions, see:**

- [Operator as AppAgent](../../ufo2/advanced_usage/operator_as_app_agent.md) - How to integrate Operator into UFO workflows
- [Agent Configuration Guide](../system/agents_config.md) - Complete agent settings reference
- [Azure OpenAI](azure_openai.md) - General Azure OpenAI setup

**Important Notes:**

- Operator is a visual-only model optimized for computer control tasks
- It uses a different workflow from standard text-based models
- Best suited for direct UI manipulation and visual understanding tasks
- Requires Azure OpenAI deployment (not available via standard OpenAI API)

