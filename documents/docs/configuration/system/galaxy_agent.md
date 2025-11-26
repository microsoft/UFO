# Galaxy Constellation Agent Configuration

**agent.yaml** configures the **Constellation Agent** - the AI agent responsible for creating constellations (task decomposition) and editing them based on execution results.

---

## Overview

The **agent.yaml** configuration file provides **LLM and API settings** for the Constellation Agent. This agent is responsible for:

- **Constellation Creation**: Breaking down user requests into device-specific tasks
- **Constellation Editing**: Adjusting task plans based on execution results
- **Device Selection**: Choosing appropriate devices for each sub-task
- **Task Orchestration**: Coordinating multi-device workflows

**Configuration Separation:**

- **agent.yaml** - LLM configuration for constellation agent (this document)
- **constellation.yaml** - Runtime settings for orchestrator ([Galaxy Constellation Configuration](./galaxy_constellation.md))
- **devices.yaml** - Device definitions ([Galaxy Devices Configuration](./galaxy_devices.md))

**Agent Role in System:**

```mermaid
graph TB
    A[User Request] -->|Natural Language| B[Constellation Agent]
    B -->|Uses LLM Config| C[agent.yaml]
    B -->|Creates/Edits| D[Constellation Plan]
    D -->|Tasks| E[Device Agent 1]
    D -->|Tasks| F[Device Agent 2]
    D -->|Tasks| G[Device Agent N]
    
    style B fill:#e1f5ff
    style C fill:#ffe1e1
    style D fill:#fff4e1
```

---

## File Location

**Standard Location:**

```
UFO2/
├── config/
│   └── galaxy/
│       ├── agent.yaml              # ← Constellation agent config (copy from template)
│       ├── agent.yaml.template     # ← Template for initial setup
│       ├── constellation.yaml      # ← Runtime settings
│       └── devices.yaml            # ← Device definitions
```

!!!warning "Setup Required"
    1. Copy `agent.yaml.template` to `agent.yaml`
    2. Fill in your API credentials (API_KEY, AAD_TENANT_ID, etc.)
    3. Never commit `agent.yaml` with real credentials to version control

**Loading in Code:**

```python
from config.config_loader import get_galaxy_config

# Load Galaxy configuration (includes agent settings)
config = get_galaxy_config()

# Access constellation agent settings
agent_config = config.constellation_agent
reasoning_model = agent_config.reasoning_model
api_type = agent_config.api_type
api_model = agent_config.api_model
```

---

## Configuration Schema

### Complete Schema

```yaml
# Galaxy Constellation Agent Configuration

CONSTELLATION_AGENT:
  # Reasoning
  REASONING_MODEL: bool          # Enable reasoning/chain-of-thought
  
  # API Connection
  API_TYPE: string               # API provider type
  API_BASE: string               # API base URL
  API_KEY: string                # API authentication key
  API_VERSION: string            # API version
  API_MODEL: string              # Model name/deployment
  
  # Azure AD Authentication (for azure_ad API_TYPE)
  AAD_TENANT_ID: string          # Azure AD tenant ID
  AAD_API_SCOPE: string          # API scope name
  AAD_API_SCOPE_BASE: string     # API scope base GUID
  
  # Prompt Configuration
  CONSTELLATION_CREATION_PROMPT: string         # Path to creation prompt template
  CONSTELLATION_EDITING_PROMPT: string          # Path to editing prompt template
  CONSTELLATION_CREATION_EXAMPLE_PROMPT: string # Path to creation examples
  CONSTELLATION_EDITING_EXAMPLE_PROMPT: string  # Path to editing examples
```

---

## Configuration Fields

### Reasoning Capabilities

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `REASONING_MODEL` | `bool` | No | `False` | Enable chain-of-thought reasoning for complex planning |

**Example:**

```yaml
CONSTELLATION_AGENT:
  REASONING_MODEL: False  # Standard LLM response (faster)
```

!!!tip "Reasoning Model"
    Set `REASONING_MODEL: True` for:
    - Complex multi-device workflows
    - Tasks requiring step-by-step planning
    - Debugging constellation failures
    
    **Trade-off:** Slower response time, higher token cost

---

### API Connection Settings

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `API_TYPE` | `string` | Yes | - | API provider: `"openai"`, `"azure"`, `"azure_ad"`, `"aoai"` |
| `API_BASE` | `string` | Yes* | - | API base URL (required for Azure) |
| `API_KEY` | `string` | Yes* | - | API authentication key (required for non-AAD auth) |
| `API_VERSION` | `string` | Yes* | - | API version (required for Azure) |
| `API_MODEL` | `string` | Yes | - | Model name or deployment name |

**Supported API Types:**

| API_TYPE | Provider | Authentication | Example API_BASE |
|----------|----------|----------------|------------------|
| `openai` | OpenAI | API Key | Not required (uses default) |
| `azure` | Azure OpenAI | API Key | `https://your-resource.openai.azure.com/` |
| `azure_ad` | Azure OpenAI | Azure AD (AAD) | `https://your-resource.azure-api.net/` |
| `aoai` | Azure OpenAI (alias) | API Key | `https://your-resource.openai.azure.com/` |

---

#### Example 1: OpenAI Configuration

```yaml
CONSTELLATION_AGENT:
  API_TYPE: "openai"
  API_KEY: "sk-proj-..."           # Your OpenAI API key
  API_MODEL: "gpt-4o"              # OpenAI model name
  API_VERSION: "2024-02-01"        # Optional for OpenAI
```

---

#### Example 2: Azure OpenAI (API Key Auth)

```yaml
CONSTELLATION_AGENT:
  API_TYPE: "azure"
  API_BASE: "https://my-resource.openai.azure.com/"
  API_KEY: "abc123..."             # Azure OpenAI API key
  API_VERSION: "2025-02-01-preview"
  API_MODEL: "gpt-4o-deployment"   # Your deployment name
```

---

#### Example 3: Azure OpenAI (Azure AD Auth)

```yaml
CONSTELLATION_AGENT:
  API_TYPE: "azure_ad"
  API_BASE: "https://cloudgpt-openai.azure-api.net/"
  API_VERSION: "2025-02-01-preview"
  API_MODEL: "gpt-5-chat-20251003"
  
  # Azure AD Configuration
  AAD_TENANT_ID: "72f988bf-86f1-41af-91ab-2d7cd011db47"
  AAD_API_SCOPE: "openai"
  AAD_API_SCOPE_BASE: "feb7b661-cac7-44a8-8dc1-163b63c23df2"
```

!!!warning "Azure AD Authentication"
    When using `API_TYPE: "azure_ad"`:
    - No `API_KEY` needed (uses Azure AD token)
    - Requires `AAD_TENANT_ID`, `AAD_API_SCOPE`, `AAD_API_SCOPE_BASE`
    - User must be authenticated with `az login` or have proper AAD credentials

---

### Azure AD Fields (azure_ad API_TYPE only)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `AAD_TENANT_ID` | `string` | Yes* | Azure AD tenant GUID |
| `AAD_API_SCOPE` | `string` | Yes* | API scope identifier (e.g., "openai") |
| `AAD_API_SCOPE_BASE` | `string` | Yes* | API scope base GUID |

*Required only when `API_TYPE: "azure_ad"`

---

### Prompt Configuration Paths

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `CONSTELLATION_CREATION_PROMPT` | `string` | Yes | - | Path to constellation creation prompt template |
| `CONSTELLATION_EDITING_PROMPT` | `string` | Yes | - | Path to constellation editing prompt template |
| `CONSTELLATION_CREATION_EXAMPLE_PROMPT` | `string` | Yes | - | Path to creation examples (few-shot learning) |
| `CONSTELLATION_EDITING_EXAMPLE_PROMPT` | `string` | Yes | - | Path to editing examples (few-shot learning) |

**Default Prompt Paths:**

```yaml
CONSTELLATION_AGENT:
  CONSTELLATION_CREATION_PROMPT: "galaxy/prompts/constellation/share/constellation_creation.yaml"
  CONSTELLATION_EDITING_PROMPT: "galaxy/prompts/constellation/share/constellation_editing.yaml"
  CONSTELLATION_CREATION_EXAMPLE_PROMPT: "galaxy/prompts/constellation/examples/constellation_creation_example.yaml"
  CONSTELLATION_EDITING_EXAMPLE_PROMPT: "galaxy/prompts/constellation/examples/constellation_editing_example.yaml"
```

!!!tip "Custom Prompts"
    You can customize prompts for your use case:
    ```yaml
    CONSTELLATION_CREATION_PROMPT: "custom_prompts/my_constellation_creation.yaml"
    ```

---

## Complete Examples

### Example 1: Production (Azure AD)

```yaml
# Galaxy Constellation Agent Configuration - Production
# Uses Azure OpenAI with Azure AD authentication

CONSTELLATION_AGENT:
  # Capabilities
  REASONING_MODEL: False
  
  # Azure OpenAI (Azure AD Auth)
  API_TYPE: "azure_ad"
  API_BASE: "https://cloudgpt-openai.azure-api.net/"
  API_VERSION: "2025-02-01-preview"
  API_MODEL: "gpt-5-chat-20251003"
  
  # Azure AD Configuration
  AAD_TENANT_ID: "72f988bf-86f1-41af-91ab-2d7cd011db47"
  AAD_API_SCOPE: "openai"
  AAD_API_SCOPE_BASE: "feb7b661-cac7-44a8-8dc1-163b63c23df2"
  
  # Prompt Configurations
  CONSTELLATION_CREATION_PROMPT: "galaxy/prompts/constellation/share/constellation_creation.yaml"
  CONSTELLATION_EDITING_PROMPT: "galaxy/prompts/constellation/share/constellation_editing.yaml"
  CONSTELLATION_CREATION_EXAMPLE_PROMPT: "galaxy/prompts/constellation/examples/constellation_creation_example.yaml"
  CONSTELLATION_EDITING_EXAMPLE_PROMPT: "galaxy/prompts/constellation/examples/constellation_editing_example.yaml"
```

---

### Example 2: Development (OpenAI)

```yaml
# Galaxy Constellation Agent Configuration - Development
# Uses OpenAI API for quick testing

CONSTELLATION_AGENT:
  # Capabilities
  REASONING_MODEL: True   # Enable for debugging
  
  # OpenAI API
  API_TYPE: "openai"
  API_KEY: "sk-proj-..."  # Your OpenAI API key (DO NOT COMMIT!)
  API_MODEL: "gpt-4o"
  API_VERSION: "2024-02-01"
  
  # Prompt Configurations (default paths)
  CONSTELLATION_CREATION_PROMPT: "galaxy/prompts/constellation/share/constellation_creation.yaml"
  CONSTELLATION_EDITING_PROMPT: "galaxy/prompts/constellation/share/constellation_editing.yaml"
  CONSTELLATION_CREATION_EXAMPLE_PROMPT: "galaxy/prompts/constellation/examples/constellation_creation_example.yaml"
  CONSTELLATION_EDITING_EXAMPLE_PROMPT: "galaxy/prompts/constellation/examples/constellation_editing_example.yaml"
```

---

### Example 3: Azure OpenAI (API Key)

```yaml
# Galaxy Constellation Agent Configuration - Azure (API Key Auth)
# Uses Azure OpenAI with API key authentication

CONSTELLATION_AGENT:
  # Capabilities
  REASONING_MODEL: False
  
  # Azure OpenAI (API Key Auth)
  API_TYPE: "azure"
  API_BASE: "https://my-openai-resource.openai.azure.com/"
  API_KEY: "abc123..."    # Azure OpenAI API key (DO NOT COMMIT!)
  API_VERSION: "2025-02-01-preview"
  API_MODEL: "gpt-4o-deployment-name"
  
  # Prompt Configurations
  CONSTELLATION_CREATION_PROMPT: "galaxy/prompts/constellation/share/constellation_creation.yaml"
  CONSTELLATION_EDITING_PROMPT: "galaxy/prompts/constellation/share/constellation_editing.yaml"
  CONSTELLATION_CREATION_EXAMPLE_PROMPT: "galaxy/prompts/constellation/examples/constellation_creation_example.yaml"
  CONSTELLATION_EDITING_EXAMPLE_PROMPT: "galaxy/prompts/constellation/examples/constellation_editing_example.yaml"
```

---

## Security Best Practices

!!!danger "Never Commit Credentials"
    **DO NOT commit `agent.yaml` with real credentials to version control!**
    
    ✅ **Recommended Workflow:**
    ```bash
    # 1. Copy template
    cp config/galaxy/agent.yaml.template config/galaxy/agent.yaml
    
    # 2. Edit agent.yaml with your credentials
    # (This file is .gitignored)
    
    # 3. Commit only the template
    git add config/galaxy/agent.yaml.template
    git commit -m "Update agent template"
    ```

**Use Environment Variables for Sensitive Data:**

```yaml
# In agent.yaml
CONSTELLATION_AGENT:
  API_KEY: ${GALAXY_API_KEY}  # Read from environment variable
```

```bash
# In your shell
export GALAXY_API_KEY="sk-proj-..."
```

---

## Integration with Other Configurations

The agent configuration works together with other Galaxy configs:

**agent.yaml** (LLM config) + **constellation.yaml** (runtime) + **devices.yaml** (devices) → **Complete Galaxy System**

### Complete Initialization Example

```python
from config.config_loader import get_galaxy_config
from galaxy.agents.constellation_agent import ConstellationAgent
from galaxy.client.device_manager import ConstellationDeviceManager
import yaml

# 1. Load all Galaxy configurations
galaxy_config = get_galaxy_config()

# 2. Initialize Constellation Agent with LLM config
agent = ConstellationAgent(
    reasoning_model=galaxy_config.constellation_agent.reasoning_model,
    api_type=galaxy_config.constellation_agent.api_type,
    api_base=galaxy_config.constellation_agent.api_base,
    api_key=galaxy_config.constellation_agent.api_key,
    api_version=galaxy_config.constellation_agent.api_version,
    api_model=galaxy_config.constellation_agent.api_model
)

# 3. Load constellation runtime settings
with open("config/galaxy/constellation.yaml", "r") as f:
    constellation_config = yaml.safe_load(f)

# 4. Initialize Device Manager with runtime settings
device_manager = ConstellationDeviceManager(
    task_name=constellation_config["CONSTELLATION_ID"],
    heartbeat_interval=constellation_config["HEARTBEAT_INTERVAL"],
    reconnect_delay=constellation_config["RECONNECT_DELAY"]
)

# 5. Load and register devices
device_config_path = constellation_config["DEVICE_INFO"]
with open(device_config_path, "r") as f:
    devices_config = yaml.safe_load(f)

for device in devices_config["devices"]:
    await device_manager.register_device(**device)

print("✅ Galaxy Constellation System Initialized")
print(f"   Agent Model: {galaxy_config.constellation_agent.api_model}")
print(f"   Constellation ID: {constellation_config['CONSTELLATION_ID']}")
print(f"   Devices: {len(devices_config['devices'])}")
```

---

## Best Practices

**Configuration Best Practices:**

1. **Use Templates for Team Collaboration**
   ```bash
   # Share template, not credentials
   config/galaxy/agent.yaml.template  # ✅ Commit this
   config/galaxy/agent.yaml           # ❌ Never commit this
   ```

2. **Test with OpenAI, Deploy with Azure**
   ```yaml
   # Development: OpenAI (fast iteration)
   API_TYPE: "openai"
   
   # Production: Azure (enterprise features)
   API_TYPE: "azure_ad"
   ```

3. **Use Reasoning Mode Selectively**
   ```yaml
   # For complex workflows
   REASONING_MODEL: True
   
   # For simple tasks
   REASONING_MODEL: False  # Faster
   ```

---

## Related Documentation

| Topic | Document | Description |
|-------|----------|-------------|
| **Constellation Runtime** | [Galaxy Constellation Configuration](./galaxy_constellation.md) | Runtime settings for orchestrator |
| **Device Configuration** | [Galaxy Devices Configuration](./galaxy_devices.md) | Device definitions |
| **System Configuration** | [Configuration Overview](./overview.md) | Overall configuration architecture |

---

## Next Steps

1. **Copy Template**: `cp agent.yaml.template agent.yaml`
2. **Configure Credentials**: Fill in API_KEY or AAD settings
3. **Configure Runtime**: See [Galaxy Constellation Configuration](./galaxy_constellation.md)
4. **Configure Devices**: See [Galaxy Devices Configuration](./galaxy_devices.md)
5. **Test Constellation**: Run Galaxy orchestrator

---

## Source Code References

- **ConstellationAgent**: `galaxy/agents/constellation_agent.py`
- **Configuration Loading**: `config/config_loader.py`
- **Configuration Schemas**: `config/config_schemas.py`
- **Prompt Templates**: `galaxy/prompts/constellation/`
