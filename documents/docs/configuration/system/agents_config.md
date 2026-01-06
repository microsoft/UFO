# Agent Configuration (agents.yaml)

Configure all LLM models and agent-specific settings for UFO². Each agent type can use different models and API configurations for optimal performance.

## Overview

The `agents.yaml` file defines LLM settings for all agents in UFO². This is the **most important configuration file** as it contains your API keys and model selections.

**File Location**: `config/ufo/agents.yaml`

**Initial Setup Required:**

1. **Copy the template file**:
   ```powershell
   Copy-Item config\ufo\agents.yaml.template config\ufo\agents.yaml
   ```

2. **Edit `config/ufo/agents.yaml`** with your API keys and settings

3. **Never commit `agents.yaml`** to version control (it contains secrets)

## Quick Start

### Step 1: Create Configuration File

```powershell
# Copy template to create your configuration
Copy-Item config\ufo\agents.yaml.template config\ufo\agents.yaml
```

### Step 2: Configure Your LLM Provider

Choose your LLM provider and edit `config/ufo/agents.yaml`:

**OpenAI:**
```yaml
HOST_AGENT:
  VISUAL_MODE: True
  API_TYPE: "openai"
  API_BASE: "https://api.openai.com/v1/chat/completions"
  API_KEY: "sk-YOUR_OPENAI_KEY_HERE"
  API_MODEL: "gpt-4o"
  API_VERSION: "2025-02-01-preview"
    
APP_AGENT:
  VISUAL_MODE: True
  API_TYPE: "openai"
  API_BASE: "https://api.openai.com/v1/chat/completions"
  API_KEY: "sk-YOUR_OPENAI_KEY_HERE"
  API_MODEL: "gpt-4o-mini"
  API_VERSION: "2025-02-01-preview"
```

**Azure OpenAI:**
```yaml
HOST_AGENT:
  VISUAL_MODE: True
  API_TYPE: "aoai"
  API_BASE: "https://YOUR_RESOURCE.openai.azure.com"
  API_KEY: "YOUR_AOAI_KEY"
  API_MODEL: "gpt-4o"
  API_VERSION: "2024-02-15-preview"
  API_DEPLOYMENT_ID: "gpt-4o-deployment"
    
APP_AGENT:
  VISUAL_MODE: True
  API_TYPE: "aoai"
  API_BASE: "https://YOUR_RESOURCE.openai.azure.com"
  API_KEY: "YOUR_AOAI_KEY"
  API_MODEL: "gpt-4o-mini"
  API_VERSION: "2024-02-15-preview"
  API_DEPLOYMENT_ID: "gpt-4o-mini-deployment"
```

**Google Gemini:**
```yaml
HOST_AGENT:
  VISUAL_MODE: True
  API_TYPE: "gemini"
  API_BASE: "https://generativelanguage.googleapis.com"
  API_KEY: "YOUR_GEMINI_API_KEY"
  API_MODEL: "gemini-2.0-flash-exp"
  API_VERSION: "v1beta"
```

**Anthropic Claude:**
```yaml
HOST_AGENT:
  VISUAL_MODE: True
  API_TYPE: "claude"
  API_BASE: "https://api.anthropic.com"
  API_KEY: "YOUR_CLAUDE_API_KEY"
  API_MODEL: "claude-3-5-sonnet-20241022"
  API_VERSION: "2023-06-01"
```

### Step 3: Verify Configuration

```python
from config.config_loader import get_ufo_config

config = get_ufo_config()
print(f"HOST_AGENT model: {config.host_agent.api_model}")
print(f"APP_AGENT model: {config.app_agent.api_model}")
```

---

## Agent Types

UFO² uses different agents for different purposes. Each can be configured with different models.

| Agent | Purpose | Recommended Model | Frequency |
|-------|---------|-------------------|-----------|
| **HOST_AGENT** | Task planning, app coordination | GPT-4o, GPT-4 | Low (planning) |
| **APP_AGENT** | Action execution, UI interaction | GPT-4o-mini, GPT-4o | High (every action) |
| **BACKUP_AGENT** | Fallback when others fail | GPT-4-vision-preview | Rare (errors) |
| **EVALUATION_AGENT** | Task completion evaluation | GPT-4o | Low (end of task) |
| **OPERATOR** | CUA-based automation | computer-use-preview | Optional |

**Cost Optimization Tips:**

- Use **GPT-4o** for HOST_AGENT (complex planning)
- Use **GPT-4o-mini** for APP_AGENT (frequent actions, 60% cheaper)
- Same model can be used for BACKUP_AGENT and EVALUATION_AGENT

## Configuration Fields

### Common Fields (All Agents)

These fields are available for `HOST_AGENT`, `APP_AGENT`, `BACKUP_AGENT`, `EVALUATION_AGENT`, and `OPERATOR`.

#### Core Settings

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `VISUAL_MODE` | Boolean | ❌ | `True` | Enable vision capabilities (screenshot understanding) |
| `REASONING_MODEL` | Boolean | ❌ | `False` | Whether model is a reasoning model (o1, o3, o3-mini) |
| `API_TYPE` | String | ✅ | `"openai"` | LLM provider type |
| `API_BASE` | String | ✅ | varies | API endpoint URL |
| `API_KEY` | String | ✅ | `""` | API authentication key |
| `API_MODEL` | String | ✅ | varies | Model identifier |
| `API_VERSION` | String | ❌ | `"2025-02-01-preview"` | API version |

**Legend:** ✅ = Required (must be set), ❌ = Optional (has default value)

#### API_TYPE Options

| API_TYPE | Provider | Example API_BASE |
|----------|----------|------------------|
| `"openai"` | OpenAI | `https://api.openai.com/v1/chat/completions` |
| `"aoai"` | Azure OpenAI | `https://YOUR_RESOURCE.openai.azure.com` |
| `"azure_ad"` | Azure OpenAI (AD auth) | `https://YOUR_RESOURCE.openai.azure.com` |
| `"gemini"` | Google Gemini | `https://generativelanguage.googleapis.com` |
| `"claude"` | Anthropic Claude | `https://api.anthropic.com` |
| `"qwen"` | Alibaba Qwen | varies |
| `"ollama"` | Ollama (local) | `http://localhost:11434` |

#### Azure OpenAI Additional Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `API_DEPLOYMENT_ID` | String | ✅ (for AOAI) | Azure deployment name |

**Example**:
```yaml
HOST_AGENT:
  API_TYPE: "aoai"
  API_BASE: "https://myresource.openai.azure.com"
  API_KEY: "abc123..."
  API_MODEL: "gpt-4o"
  API_DEPLOYMENT_ID: "gpt-4o-deployment-name"
```

#### Azure AD Authentication Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `AAD_TENANT_ID` | String | ✅ (for azure_ad) | Azure AD tenant ID |
| `AAD_API_SCOPE` | String | ✅ (for azure_ad) | Azure AD API scope |
| `AAD_API_SCOPE_BASE` | String | ✅ (for azure_ad) | Scope base URL |

**Example**:
```yaml
HOST_AGENT:
  API_TYPE: "azure_ad"
  API_BASE: "https://myresource.openai.azure.com"
  AAD_TENANT_ID: "your-tenant-id"
  AAD_API_SCOPE: "your-scope"
  AAD_API_SCOPE_BASE: "API://your-scope-base"
  API_MODEL: "gpt-4o"
  API_DEPLOYMENT_ID: "gpt-4o-deployment"
```

#### Prompt Configuration

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `PROMPT` | String | ❌ | Path to main prompt template |
| `EXAMPLE_PROMPT` | String | ❌ | Path to example prompt template |
| `API_PROMPT` | String | ❌ | Path to API usage prompt (APP_AGENT only) |

**Default Prompt Paths:**
```yaml
HOST_AGENT:
  PROMPT: "ufo/prompts/share/base/host_agent.yaml"
  EXAMPLE_PROMPT: "ufo/prompts/examples/{mode}/host_agent_example.yaml"

APP_AGENT:
  PROMPT: "ufo/prompts/share/base/app_agent.yaml"
  EXAMPLE_PROMPT: "ufo/prompts/examples/{mode}/app_agent_example.yaml"
  API_PROMPT: "ufo/prompts/share/base/api.yaml"
```

You can customize prompts by creating your own YAML files and updating these paths. See the [Customization Guide](../../ufo2/advanced_usage/customization.md) for details.

#### OPERATOR-Specific Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `SCALER` | List[int] | ❌ | Screen dimensions for visual input `[width, height]`, default: `[1024, 768]` |

**Example:**
```yaml
OPERATOR:
  SCALER: [1920, 1080]  # Full HD resolution
  API_MODEL: "computer-use-preview-20250311"
  # ... other settings
```

## Complete Configuration Example

Here's a complete `agents.yaml` with all agent types configured:

```yaml
# HOST_AGENT - Task planning and coordination
HOST_AGENT:
  VISUAL_MODE: True
  REASONING_MODEL: False
  API_TYPE: "openai"
  API_BASE: "https://api.openai.com/v1/chat/completions"
  API_KEY: "sk-YOUR_KEY_HERE"
  API_MODEL: "gpt-4o"
  API_VERSION: "2025-02-01-preview"
  PROMPT: "ufo/prompts/share/base/host_agent.yaml"
  EXAMPLE_PROMPT: "ufo/prompts/examples/{mode}/host_agent_example.yaml"

# APP_AGENT - Action execution
APP_AGENT:
  VISUAL_MODE: True
  REASONING_MODEL: False
  API_TYPE: "openai"
  API_BASE: "https://api.openai.com/v1/chat/completions"
  API_KEY: "sk-YOUR_KEY_HERE"
  API_MODEL: "gpt-4o-mini"  # Cheaper for frequent actions
  API_VERSION: "2025-02-01-preview"
  PROMPT: "ufo/prompts/share/base/app_agent.yaml"
  EXAMPLE_PROMPT: "ufo/prompts/examples/{mode}/app_agent_example.yaml"
  API_PROMPT: "ufo/prompts/share/base/api.yaml"

# BACKUP_AGENT - Fallback agent
BACKUP_AGENT:
  VISUAL_MODE: True
  REASONING_MODEL: False
  API_TYPE: "openai"
  API_BASE: "https://api.openai.com/v1/chat/completions"
  API_KEY: "sk-YOUR_KEY_HERE"
  API_MODEL: "gpt-4-vision-preview"
  API_VERSION: "2025-02-01-preview"

# EVALUATION_AGENT - Task evaluation
EVALUATION_AGENT:
  VISUAL_MODE: True
  REASONING_MODEL: False
  API_TYPE: "openai"
  API_BASE: "https://api.openai.com/v1/chat/completions"
  API_KEY: "sk-YOUR_KEY_HERE"
  API_MODEL: "gpt-4o"
  API_VERSION: "2025-02-01-preview"

# OPERATOR - OpenAI Operator (optional)
OPERATOR:
  SCALER: [1024, 768]  # Screen resolution for visual input
  VISUAL_MODE: True
  REASONING_MODEL: False
  API_TYPE: "openai"
  API_BASE: "https://api.openai.com/v1/chat/completions"
  API_KEY: "sk-YOUR_KEY_HERE"
  API_MODEL: "computer-use-preview-20250311"
  API_VERSION: "2025-03-01-preview"
```

## Multi-Provider Configuration

You can use different providers for different agents:

```yaml
# Use OpenAI for planning
HOST_AGENT:
  API_TYPE: "openai"
  API_BASE: "https://api.openai.com/v1/chat/completions"
  API_KEY: "sk-YOUR_OPENAI_KEY"
  API_MODEL: "gpt-4o"

# Use Azure OpenAI for actions (cost control)
APP_AGENT:
  API_TYPE: "aoai"
  API_BASE: "https://mycompany.openai.azure.com"
  API_KEY: "YOUR_AZURE_KEY"
  API_MODEL: "gpt-4o-mini"
  API_DEPLOYMENT_ID: "gpt-4o-mini-deploy"

# Use Claude for evaluation
EVALUATION_AGENT:
  API_TYPE: "claude"
  API_BASE: "https://api.anthropic.com"
  API_KEY: "YOUR_CLAUDE_KEY"
  API_MODEL: "claude-3-5-sonnet-20241022"
```

## Model Recommendations

### For HOST_AGENT (Planning)

| Model | Provider | Pros | Cons |
|-------|----------|------|------|
| **gpt-4o** | OpenAI | Best overall, fast, multimodal | $$ |
| **gpt-4-turbo** | OpenAI | Good quality, cheaper than GPT-4 | Slower |
| **claude-3-5-sonnet** | Anthropic | Excellent reasoning | No vision API yet |
| **gemini-2.0-flash** | Google | Fast, cheap, multimodal | New, less tested |

### For APP_AGENT (Execution)

| Model | Provider | Pros | Cons |
|-------|----------|------|------|
| **gpt-4o-mini** | OpenAI | 60% cheaper, fast, good quality | Slightly less capable |
| **gpt-4o** | OpenAI | Best quality | More expensive |
| **gemini-1.5-flash** | Google | Very cheap, fast | Less accurate |

### For OPERATOR (CUA Mode)

| Model | Provider | Notes |
|-------|----------|-------|
| **computer-use-preview-20250311** | OpenAI | Supported model for Operator mode (Computer Use Agent) |

## Reasoning Models

For models like OpenAI o1, o3, o3-mini, set `REASONING_MODEL: True`:

```yaml
HOST_AGENT:
  REASONING_MODEL: True  # Enable for o1/o3/o3-mini
  API_TYPE: "openai"
  API_MODEL: "o3-mini"
  # ... other settings
```

**Note:** Reasoning models have different behavior including no streaming responses, different token limits, and may have different pricing.

## Environment Variables

Instead of hardcoding API keys, you can use environment variables:

```yaml
HOST_AGENT:
  API_KEY: "${OPENAI_API_KEY}"  # Reads from environment variable

APP_AGENT:
  API_KEY: "${AZURE_OPENAI_KEY}"
```

**Setting environment variables**:

**Windows (PowerShell):**
```powershell
$env:OPENAI_API_KEY = "sk-your-key"
$env:AZURE_OPENAI_KEY = "your-azure-key"
```

**Windows (Persistent):**
```powershell
[System.Environment]::SetEnvironmentVariable('OPENAI_API_KEY', 'sk-your-key', 'User')
```

**Linux/macOS:**
```bash
export OPENAI_API_KEY="sk-your-key"
export AZURE_OPENAI_KEY="your-azure-key"
```

## Programmatic Access

```python
from config.config_loader import get_ufo_config

config = get_ufo_config()

# Access HOST_AGENT settings
host_model = config.host_agent.api_model
host_type = config.host_agent.api_type
host_visual = config.host_agent.visual_mode

# Access APP_AGENT settings
app_model = config.app_agent.api_model
app_key = config.app_agent.api_key

# Check if agent is configured
if config.host_agent.api_key:
    print("HOST_AGENT is configured")
else:
    print("Warning: HOST_AGENT API key not set")
```

## Troubleshooting

### Issue 1: "agents.yaml not found"

**Error Message:**
```
FileNotFoundError: config/ufo/agents.yaml not found
```

**Solution:** Copy the template file
```powershell
Copy-Item config\ufo\agents.yaml.template config\ufo\agents.yaml
```

### Issue 2: API Authentication Errors

**Error Message:**
```
openai.AuthenticationError: Invalid API key
```

**Solutions:**
1. Verify API key is correct
2. Check for extra spaces or quotes
3. Ensure API_TYPE matches your provider
4. For Azure, verify API_DEPLOYMENT_ID is set

### Issue 3: Model Not Found

**Error Message:**
```
openai.NotFoundError: The model 'gpt-4o' does not exist
```

**Solutions:**
1. Verify model name is correct (check provider's documentation)
2. For Azure, ensure deployment exists and API_DEPLOYMENT_ID matches
3. Check if you have access to the model

### Issue 4: Rate Limits

**Error Message:**
```
openai.RateLimitError: Rate limit exceeded
```

**Solutions:**
1. Add delays between requests (configure in `system.yaml`)
2. Upgrade your API plan
3. Use different API keys for different agents

## Security Best Practices

**API Key Security Guidelines:**

1. ✅ **Never commit `agents.yaml` to Git**
   - Add to `.gitignore`
   - Only commit `agents.yaml.template`

2. ✅ **Use environment variables** for production
   ```yaml
   API_KEY: "${OPENAI_API_KEY}"
   ```

3. ✅ **Rotate keys regularly**

4. ✅ **Use separate keys** for dev/prod environments

5. ✅ **Restrict key permissions** (e.g., read-only for evaluation agents)

## Related Documentation

- **[Third-Party Agent Configuration](third_party_config.md)** - Configure external agents like LinuxAgent and HardwareAgent
- **[Creating Custom Third-Party Agents](../../tutorials/creating_third_party_agents.md)** - Build your own specialized agents
- **[System Configuration](system_config.md)** - Runtime and execution settings
- **[MCP Configuration](mcp_reference.md)** - Tool server configuration
- **[RAG Configuration](rag_config.md)** - Knowledge retrieval settings
- **[Model Setup Guide](../models/overview.md)** - Provider-specific setup
- **[Migration Guide](migration.md)** - Migrating from legacy config

## Summary

**Key Takeaways:**

✅ **Copy template first**: `Copy-Item config\ufo\agents.yaml.template config\ufo\agents.yaml`  
✅ **Add your API keys**: Edit `agents.yaml` with your credentials  
✅ **Choose models wisely**: GPT-4o for planning, GPT-4o-mini for actions  
✅ **Never commit secrets**: Keep `agents.yaml` out of version control  
✅ **Use environment variables**: For production deployments

**Your agents are now ready to work!** 🚀
