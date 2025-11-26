# Configuration Migration Guide

This guide helps you migrate from the legacy configuration system (`ufo/config/config.yaml`) to the new modular configuration system (`config/ufo/`).

**Migration Overview:** Migrating to the new configuration system is **optional but recommended**. Your existing configuration will continue to work, but the new system offers better organization, type safety, and IDE support.

## Why Migrate?

The new configuration system offers several advantages:

| Feature | Legacy (`ufo/config/`) | New (`config/ufo/`) |
|---------|----------------------|-------------------|
| **Structure** | Single monolithic YAML | Modular domain-specific files |
| **Type Safety** | Dict access only | Typed + dynamic access |
| **IDE Support** | No autocomplete | Full IntelliSense |
| **Scalability** | Hard to maintain | Easy to extend |
| **Documentation** | External docs | Self-documenting structure |
| **Environment Support** | Manual | Built-in dev/test/prod |

## Migration Methods

### Option 1: Automatic Migration (Recommended)

Use the built-in migration tool:

**Automatic Migration Tool**:

```bash
# From UFO2 root directory
python -m ufo.tools.migrate_config

# Or with options
python -m ufo.tools.migrate_config --backup --validate
```

**What it does**:
1. ✅ Reads your legacy `ufo/config/config.yaml`
2. ✅ Splits into modular files by domain
3. ✅ Creates backup of original file
4. ✅ Validates the new configuration
5. ✅ Provides migration report

!!!warning "Backup Reminder"
    Always backup your configuration before migration! The tool creates a backup automatically, but it's good practice to keep your own copy.

### Option 2: Manual Migration

Step-by-step manual migration process.

#### Step 1: Create Directory Structure

```bash
# Create new config directories
mkdir -p config/ufo
mkdir -p config/galaxy  # If using Galaxy
```

#### Step 2: Copy Templates

```bash
# Copy template files
cp config/ufo/agents.yaml.template config/ufo/agents.yaml
cp config/galaxy/agent.yaml.template config/galaxy/agent.yaml  # If using Galaxy
```

#### Step 3: Split Configuration

Split your `ufo/config/config.yaml` into modular files:

**Legacy config.yaml**:
```yaml
# ufo/config/config.yaml (OLD - Monolithic)
HOST_AGENT:
  API_TYPE: "openai"
  API_KEY: "sk-..."
  API_MODEL: "gpt-4o"

APP_AGENT:
  API_TYPE: "openai"
  API_KEY: "sk-..."
  API_MODEL: "gpt-4o"

MAX_STEP: 50
MAX_RETRY: 20
TEMPERATURE: 0.0

RAG_OFFLINE_DOCS: False
RAG_EXPERIENCE: True
```

**New modular structure**:

`config/ufo/agents.yaml`:
```yaml
# Agent LLM configurations
HOST_AGENT:
  API_TYPE: "openai"
  API_KEY: "sk-..."
  API_MODEL: "gpt-4o"

APP_AGENT:
  API_TYPE: "openai"
  API_KEY: "sk-..."
  API_MODEL: "gpt-4o"
```

`config/ufo/system.yaml`:
```yaml
# System and runtime configurations
MAX_STEP: 50
MAX_RETRY: 20
TEMPERATURE: 0.0
```

`config/ufo/rag.yaml`:
```yaml
# RAG knowledge configurations
RAG_OFFLINE_DOCS: False
RAG_EXPERIENCE: True
```

#### Step 4: Verify Configuration

**Verification Script**:

```python
# Test your new configuration
from config.config_loader import get_ufo_config

config = get_ufo_config()

# Verify values loaded correctly
print(f"Max step: {config.system.max_step}")
print(f"Host agent model: {config.host_agent.api_model}")
print(f"RAG experience: {config.rag.experience}")
```

#### Step 5: Update Code (Optional)

Modernize configuration access patterns:

```python
# OLD (still works but deprecated)
config = Config()
max_step = config["MAX_STEP"]
api_model = config["HOST_AGENT"]["API_MODEL"]

# NEW (recommended)
config = get_ufo_config()
max_step = config.system.max_step              # Type-safe!
api_model = config.host_agent.api_model        # IDE autocomplete!
```

#### Step 6: Clean Up Legacy Config

!!!danger "Remove Legacy Config Only After Verification"
    Only remove the legacy config after thoroughly testing that the new configuration works correctly!

```bash
# Backup legacy config
cp ufo/config/config.yaml ufo/config/config.yaml.backup

# Remove legacy config (after verifying new config works)
rm ufo/config/config.yaml
```

## Field Mapping Reference

### Agent Configurations

| Legacy Location | New Location | Notes |
|----------------|--------------|-------|
| `HOST_AGENT.*` | `config/ufo/agents.yaml` → `HOST_AGENT.*` | Same structure |
| `APP_AGENT.*` | `config/ufo/agents.yaml` → `APP_AGENT.*` | Same structure |
| `BACKUP_AGENT.*` | `config/ufo/agents.yaml` → `BACKUP_AGENT.*` | Same structure |
| `EVALUATION_AGENT.*` | `config/ufo/agents.yaml` → `EVALUATION_AGENT.*` | Same structure |
| `OPERATOR.*` | `config/ufo/agents.yaml` → `OPERATOR.*` | New in UFO² |

### System Configurations

| Legacy Field | New Location | New Access Pattern |
|-------------|--------------|-------------------|
| `MAX_STEP` | `config/ufo/system.yaml` | `config.system.max_step` |
| `MAX_RETRY` | `config/ufo/system.yaml` | `config.system.max_retry` |
| `TEMPERATURE` | `config/ufo/system.yaml` | `config.system.temperature` |
| `CONTROL_BACKEND` | `config/ufo/system.yaml` | `config.system.control_backend` |
| `ACTION_SEQUENCE` | `config/ufo/system.yaml` | `config.system.action_sequence` |

### RAG Configurations

| Legacy Field | New Location | New Access Pattern |
|-------------|--------------|-------------------|
| `RAG_OFFLINE_DOCS` | `config/ufo/rag.yaml` | `config.rag.offline_docs` |
| `RAG_EXPERIENCE` | `config/ufo/rag.yaml` | `config.rag.experience` |
| `RAG_DEMONSTRATION` | `config/ufo/rag.yaml` | `config.rag.demonstration` |
| `BING_API_KEY` | `config/ufo/rag.yaml` | `config.rag.BING_API_KEY` |

### MCP Configurations

| Legacy Field | New Location | Notes |
|-------------|--------------|-------|
| `USE_MCP` | `config/ufo/system.yaml` | Keep in system config |
| `MCP_SERVERS_CONFIG` | `config/ufo/system.yaml` | Points to `config/ufo/mcp.yaml` |
| MCP server definitions | `config/ufo/mcp.yaml` | New dedicated file |

## Common Migration Scenarios

### Scenario 1: Different Models for Different Agents

**Legacy approach** (duplicated config):
```yaml
# ufo/config/config.yaml
HOST_AGENT:
  API_MODEL: "gpt-4o"
  # ... other settings

APP_AGENT:
  API_MODEL: "gpt-4o-mini"  # Different model
  # ... other settings
```

**New approach** (clear separation):
```yaml
# config/ufo/agents.yaml
HOST_AGENT:
  API_MODEL: "gpt-4o"

APP_AGENT:
  API_MODEL: "gpt-4o-mini"
```

### Scenario 2: Environment-Specific Settings

**Legacy approach** (manual switching):
```yaml
# ufo/config/config.yaml
# Manually comment/uncomment for different environments
# MAX_STEP: 10  # Development
MAX_STEP: 50    # Production
```

**New approach** (automatic environment support):
```yaml
# config/ufo/system.yaml (base)
MAX_STEP: 50

# config/ufo/system_dev.yaml (development override)
MAX_STEP: 10
LOG_LEVEL: "DEBUG"
```

```bash
# Set environment
export UFO_ENV=dev  # Automatically uses system_dev.yaml overrides
```

### Scenario 3: Custom Experimental Features

**Legacy approach** (modify code):
```python
# Had to modify Config class
class Config:
    def __init__(self):
        self.MY_CUSTOM_FEATURE = True  # Added to code
```

**New approach** (just add to YAML):
```yaml
# config/ufo/custom.yaml (new file)
MY_CUSTOM_FEATURE: True
EXPERIMENTAL_SETTING: "value"
```

```python
# Automatically available
config = get_ufo_config()
if config.MY_CUSTOM_FEATURE:
    value = config.EXPERIMENTAL_SETTING
```

## Validation After Migration

### 1. Test Configuration Loading

```python
from config.config_loader import get_ufo_config

# Load configuration
config = get_ufo_config()

# Verify critical settings
assert config.system.max_step > 0
assert config.host_agent.api_key != ""
assert config.app_agent.api_model != ""

print("✅ Configuration loaded successfully!")
```

### 2. Test Backward Compatibility

```python
# Old access patterns should still work
config = get_ufo_config()

# Dict-style access (legacy)
max_step_old = config["MAX_STEP"]
host_agent_old = config["HOST_AGENT"]

# Verify they match new access
assert max_step_old == config.system.max_step
assert host_agent_old["API_MODEL"] == config.host_agent.api_model

print("✅ Backward compatibility verified!")
```

### 3. Run Application Tests

```bash
# Test with simple task
python -m ufo --task "Open Notepad"

# Check logs for configuration warnings
# Should not see "LEGACY CONFIG PATH DETECTED" after migration
```

## Troubleshooting

### Issue: "No configuration found"

**Cause**: Configuration files not in expected locations

!!!bug "Solution"
    Verify file locations and permissions

```bash
# Verify file locations
ls config/ufo/agents.yaml
ls config/ufo/system.yaml

# Check file permissions
chmod 644 config/ufo/*.yaml
```

### Issue: "Configuration conflicts detected"

**Cause**: Both legacy and new configs exist

!!!warning "Conflict Resolution"
    Choose one of these options to resolve conflicts

```bash
# Option 1: Remove legacy config (after backup)
mv ufo/config/config.yaml ufo/config/config.yaml.backup

# Option 2: Disable automatic fallback (in code)
config = get_ufo_config()  # Will warn but use new path
```

### Issue: "Missing required fields"

**Cause**: Required fields not present in new configuration

!!!failure "Required Fields Missing"
    Ensure all required agent fields are present

```yaml
# config/ufo/agents.yaml
# Ensure all required agent fields present:
HOST_AGENT:
  API_TYPE: "openai"        # Required
  API_BASE: "..."           # Required
  API_KEY: "..."            # Required
  API_MODEL: "..."          # Required
```
    ```

### Issue: "Type errors in code"

**Cause**: Using old dict-style access with new typed config

**Solution**:
```python
# OLD (can cause type issues)
config["HOST_AGENT"]["API_MODEL"]

# NEW (type-safe)
config.host_agent.api_model

# Or keep old style for now
config["HOST_AGENT"]["API_MODEL"]  # Still works!
```

## Migration Checklist

- [ ] Backup legacy configuration
- [ ] Create `config/ufo/` directory
- [ ] Copy and customize template files
- [ ] Split monolithic config into modular files
- [ ] Test configuration loading
- [ ] Verify backward compatibility
- [ ] Update code to use new access patterns (optional)
- [ ] Run application tests
- [ ] Remove legacy configuration (after verification)
- [ ] Update documentation/README
- [ ] Commit changes to version control

## Rollback Procedure

If migration causes issues:

!!!danger "Emergency Rollback"
    Your application will immediately fall back to the legacy configuration without any code changes.

```bash
# 1. Restore legacy config from backup
cp ufo/config/config.yaml.backup ufo/config/config.yaml

# 2. Remove new config files
rm -rf config/ufo/*.yaml

# 3. Restart application
# Old configuration will be used automatically
```

## Getting Help

If you encounter issues during migration:

1. **Check the logs** for detailed error messages
2. **Review configuration guides** ([Agents Config](./agents_config.md), [System Config](./system_config.md), [RAG Config](./rag_config.md)) for correct field names
3. **Consult [Configuration Overview](./overview.md)** for system design
4. **Open an issue** on GitHub with:
   - Your legacy config (redacted sensitive data)
   - Error messages
   - Steps you've tried

## Next Steps

After successful migration:

- **[Agents Configuration](./agents_config.md)** - Configure LLM and agent settings
- **[System Configuration](./system_config.md)** - Configure runtime and execution settings
- **[RAG Configuration](./rag_config.md)** - Configure knowledge retrieval
- **[Extending Configuration](./extending.md)** - Learn how to add custom settings
