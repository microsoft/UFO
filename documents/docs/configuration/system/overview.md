# Configuration Architecture

UFO² features a modern, modular configuration system designed for flexibility, maintainability, and backward compatibility. This guide explains the overall architecture and design principles.

## Design Philosophy

The configuration system follows professional software engineering best practices:

### Separation of Concerns

Configuration files are organized by domain rather than monolithic structure:

- **Agent configurations** (`agents.yaml`) - LLM settings for different agents → [Agent Config Guide](./agents_config.md)
- **System configurations** (`system.yaml`) - Execution and runtime settings → [System Config Guide](./system_config.md)
- **RAG configurations** (`rag.yaml`) - Knowledge retrieval settings → [RAG Config Guide](./rag_config.md)
- **MCP configurations** (`mcp.yaml`) - Model Context Protocol servers → [MCP Config Guide](./mcp_reference.md)
- **Pricing configurations** (`prices.yaml`) - Cost tracking for different models → [Pricing Config Guide](./prices_config.md)
- **Third-party configurations** (`third_party.yaml`) - External agent integration (LinuxAgent, HardwareAgent) → [Third-Party Config Guide](./third_party_config.md)

### Type Safety + Flexibility

Hybrid approach combining:

- **Fixed typed fields** - IDE autocomplete, type checking, and IntelliSense
- **Dynamic YAML fields** - Add new settings without code changes

**Example:**

```python
# Type-safe access (recommended)
config = get_ufo_config()
max_step = config.system.max_step  # IDE autocomplete!
api_model = config.app_agent.api_model

# Dynamic access (for custom fields)
custom_value = config.CUSTOM_FEATURE_FLAG
new_setting = config["NEW_YAML_KEY"]

# Backward compatible (legacy code still works)
max_step_old = config["MAX_STEP"]
```

### Backward Compatibility

Zero breaking changes - existing code continues to work:

- Old configuration paths still supported (`ufo/config/`)
- Old access patterns still work (`config["MAX_STEP"]`)
- Automatic migration warnings guide users to new structure

Your existing code will continue to work without any modifications. The system automatically falls back to legacy paths and access patterns. See the [Migration Guide](./migration.md) for details on upgrading to the new structure.

### Auto-Discovery

No manual file registration needed:

- All `*.yaml` files in `config/ufo/` are automatically loaded
- Files are merged intelligently with deep merging
- Environment-specific overrides (`*_dev.yaml`, `*_test.yaml`) supported

## Directory Structure

```
UFO/
├── config/                          ← New Configuration Root (Recommended)
│   ├── ufo/                        ← UFO² Configurations
│   │   ├── agents.yaml             # LLM agent settings
│   │   ├── agents.yaml.template    # Template for setup
│   │   ├── system.yaml             # System and runtime settings
│   │   ├── rag.yaml                # RAG knowledge settings
│   │   ├── mcp.yaml                # MCP server configurations
│   │   ├── prices.yaml             # Model pricing
│   │   └── third_party.yaml        # Third-party agents (optional)
│   │
│   ├── galaxy/                     ← Galaxy Configurations
│   │   ├── agent.yaml              # Constellation agent settings
│   │   ├── agent.yaml.template     # Template for setup
│   │   ├── constellation.yaml      # Constellation runtime settings
│   │   └── devices.yaml            # Device/client configurations
│   │
│   ├── config_loader.py            # Modern config loader
│   └── config_schemas.py           # Type definitions
│
└── ufo/config/                      ← Legacy Path (Still Supported)
    └── config.yaml                 # Old monolithic config
```

---

## Galaxy Configuration Files

The Galaxy constellation system has its own set of configuration files in `config/galaxy/`:

| File | Purpose | Template | Documentation |
|------|---------|----------|---------------|
| **constellation.yaml** | Constellation runtime settings (heartbeat, concurrency, step limits) | No | [Galaxy Constellation Config](./galaxy_constellation.md) |
| **devices.yaml** | Device agent definitions (device_id, server_url, capabilities, metadata) | No | [Galaxy Devices Config](./galaxy_devices.md) |
| **agent.yaml** | Constellation agent LLM configuration (API settings, prompts) | **Yes** (.template) | [Galaxy Agent Config](./galaxy_agent.md) |

### Galaxy Configuration Structure

```
config/galaxy/
├── constellation.yaml          # Runtime settings for orchestrator
│   ├── CONSTELLATION_ID       # Constellation identifier
│   ├── HEARTBEAT_INTERVAL     # Health check frequency
│   ├── RECONNECT_DELAY        # Reconnection delay
│   ├── MAX_CONCURRENT_TASKS   # Task concurrency limit
│   ├── MAX_STEP               # Step limit per session
│   ├── DEVICE_INFO            # Path to devices.yaml
│   └── LOG_TO_MARKDOWN        # Markdown logging flag
│
├── devices.yaml                # Device definitions
│   └── devices: []            # Array of device configurations
│       ├── device_id          # Unique device identifier
│       ├── server_url         # WebSocket endpoint
│       ├── os                 # Operating system
│       ├── capabilities       # Device capabilities
│       ├── metadata           # Custom metadata
│       ├── max_retries        # Connection retry limit
│       └── auto_connect       # Auto-connect flag
│
└── agent.yaml                  # Constellation agent LLM config
    └── CONSTELLATION_AGENT:
        ├── REASONING_MODEL    # Enable reasoning mode
        ├── API_TYPE           # API provider (openai, azure, azure_ad)
        ├── API_BASE           # API base URL
        ├── API_KEY            # API authentication key
        ├── API_VERSION        # API version
        ├── API_MODEL          # Model name/deployment
        ├── AAD_*              # Azure AD auth settings
        └── *_PROMPT           # Prompt template paths
```

### Galaxy Configuration Loading

```python
# Load Galaxy configurations
from config.config_loader import get_galaxy_config

# Load Galaxy configuration (includes agent and constellation settings)
galaxy_config = get_galaxy_config()

# Access agent configuration (LLM settings)
agent_config = galaxy_config.agent.constellation_agent

# Access constellation runtime settings
constellation_settings = galaxy_config.constellation

# Or use raw dict access for backward compatibility
constellation_id = galaxy_config["CONSTELLATION_ID"]
```

**Galaxy vs UFO Configuration:**

- **UFO Configurations** (`config/ufo/`) - Single-agent automation settings
- **Galaxy Configurations** (`config/galaxy/`) - Multi-device constellation settings
- Both systems can coexist in the same project

---

## Configuration Loading Process

### Priority Chain

The configuration system uses a clear priority chain (highest to lowest):

1. **New modular configs** - `config/{module}/*.yaml`
2. **Legacy monolithic config** - `{module}/config/config.yaml`  
3. **Environment variables** - Runtime overrides

When the same setting exists in multiple locations, the **new modular config** takes precedence over legacy configs. Values are merged with later sources overriding earlier ones.

### Loading Algorithm

```python
def load_config():
    # Step 1: Start with environment variables (lowest priority)
    config_data = dict(os.environ)
    
    # Step 2: Load legacy config if exists (middle priority)
    if exists("ufo/config/config.yaml"):
        legacy_data = load_yaml("ufo/config/config.yaml")
        merge(config_data, legacy_data)
    
    # Step 3: Load new modular configs (highest priority)
    for yaml_file in discover("config/ufo/*.yaml"):
        new_data = load_yaml(yaml_file)
        merge(config_data, new_data)
    
    # Step 4: Create typed config object
    return UFOConfig.from_dict(config_data)
```

### Deep Merging

Configuration files are merged recursively, allowing you to split configurations across multiple files without duplication:

```yaml
# config/ufo/agents.yaml
HOST_AGENT:
  API_TYPE: "openai"
  API_MODEL: "gpt-4o"

# config/ufo/custom.yaml (added later)
HOST_AGENT:
  TEMPERATURE: 0.5  # Added to HOST_AGENT

# Result: HOST_AGENT has all three fields
```

Fields from later files are added to (not replacing) earlier configurations.

## File Organization Patterns

### Split by Domain (Current Approach)

```
config/ufo/
├── agents.yaml      # All agent LLM configs
├── system.yaml      # All system settings
├── rag.yaml         # All RAG settings
├── mcp.yaml         # All MCP servers
└── prices.yaml      # Model pricing
```

**Advantages:** Easy to find related settings, clear separation of concerns, good for documentation.

### Alternative: Split by Agent

```
config/ufo/
├── host_agent.yaml       # HOST_AGENT config
├── app_agent.yaml        # APP_AGENT config
├── system.yaml           # Shared system config
└── rag.yaml              # Shared RAG config
```

**Advantages:** Agent-specific settings isolated, easy to customize per agent, good for multi-agent scenarios.

Both patterns work! The loader auto-discovers and merges all YAML files.

## Environment-Specific Overrides

Support for development, testing, and production environments:

```bash
# Base configuration
config/ufo/agents.yaml          # All environments

# Environment-specific overrides
config/ufo/agents_dev.yaml      # Development only
config/ufo/agents_test.yaml     # Testing only
config/ufo/agents_prod.yaml     # Production only
```

**Activation**:
```bash
# Set environment
export UFO_ENV=dev              # Linux/Mac
$env:UFO_ENV = "dev"            # Windows PowerShell

# Configuration loads:
# 1. agents.yaml (base)
# 2. agents_dev.yaml (overrides)
```

## Type System

### Fixed Types (Recommended)

Provides IDE autocomplete and type safety:

```python
@dataclass
class SystemConfig:
    max_step: int = 50
    max_retry: int = 20
    temperature: float = 0.0
    # ...

# Usage - IDE knows the types!
config.system.max_step        # int
config.system.temperature     # float
```

### Dynamic Types (Flexible)

For custom or experimental settings. Learn more about adding custom fields in the [Extending Configuration guide](./extending.md).

**Example:**

```python
# In YAML
MY_CUSTOM_FEATURE: True
NEW_EXPERIMENTAL_SETTING: "value"

# In code - dynamic access
if config.MY_CUSTOM_FEATURE:
    setting = config.NEW_EXPERIMENTAL_SETTING
```

### Hybrid Approach

Best of both worlds:

```python
class SystemConfig:
    # Fixed fields
    max_step: int = 50
    
    # Dynamic extras
    _extras: Dict[str, Any]
    
    def __getattr__(self, name):
        # Try extras for unknown fields
        return self._extras.get(name)
```

## Migration Warnings

The system provides clear warnings when using legacy paths:

```
⚠️  LEGACY CONFIG PATH DETECTED: UFO

Using legacy config: ufo/config/
Please migrate to:   config/ufo/

Quick migration:
  mkdir -p config/ufo
  cp ufo/config/*.yaml config/ufo/

Or use migration tool:
  python -m ufo.tools.migrate_config
```

These warnings appear once per session and guide you to migrate to the new structure.

## Best Practices

**Recommended Practices:**

- **Use modular files** - Split by domain or agent
- **Use typed access** - `config.system.max_step` over `config["MAX_STEP"]`
- **Add templates** - Provide `.template` files for sensitive data
- **Document custom fields** - Add comments in YAML
- **Use environment overrides** - For dev/test/prod differences

**Anti-Patterns to Avoid:**

- **Mix old and new** - Migrate fully to new structure
- **Put secrets in YAML** - Use environment variables instead
- **Duplicate settings** - Leverage deep merging
- **Break backward compat** - Keep `config["OLD_KEY"]` working
- **Hardcode paths** - Use config system

## Configuration Lifecycle

```mermaid
graph LR
    A[Application Start] --> B[Load Environment Vars]
    B --> C[Check for Legacy Config]
    C --> D[Load New Modular Configs]
    D --> E[Deep Merge All Sources]
    E --> F[Apply Transformations]
    F --> G[Create Typed Config Object]
    G --> H[Cache for Reuse]
    H --> I[Application Running]
```

## Next Steps

### UFO Configuration Guides
- **[Agent Configuration](./agents_config.md)** - LLM and API settings for all agents
- **[System Configuration](./system_config.md)** - Runtime and execution settings
- **[RAG Configuration](./rag_config.md)** - Knowledge retrieval and learning settings
- **[MCP Configuration](./mcp_reference.md)** - Model Context Protocol servers
- **[Pricing Configuration](./prices_config.md)** - LLM cost tracking
- **[Third-Party Configuration](./third_party_config.md)** - External agent integration (LinuxAgent, HardwareAgent)
- **[Migration Guide](./migration.md)** - How to migrate from old to new config
- **[Extending Configuration](./extending.md)** - How to add new configuration options

### Galaxy Configuration Guides
- **[Galaxy Constellation Configuration](./galaxy_constellation.md)** - Runtime settings for constellation orchestrator
- **[Galaxy Devices Configuration](./galaxy_devices.md)** - Device definitions and capabilities
- **[Galaxy Agent Configuration](./galaxy_agent.md)** - LLM configuration for constellation agent

## API Reference

For detailed API documentation of configuration classes and methods, see:

- `config.config_loader.ConfigLoader` - Configuration loading and caching
- `config.config_schemas.UFOConfig` - UFO configuration schema
- `config.config_schemas.GalaxyConfig` - Galaxy configuration schema
- `config.config_loader.get_ufo_config()` - Get UFO configuration instance
- `config.config_loader.get_galaxy_config()` - Get Galaxy configuration instance
