# Configuration Management Guide

## 📁 Configuration Structure

### Modern Structure (v3.0+) - **Recommended**

```bash
config/
├── ufo/              # UFO² Windows Agent configurations
│   ├── agents.yaml   # Agent configurations (HOST, APP, BACKUP, etc.)
│   ├── system.yaml   # System settings (max_step, timeout, etc.)
│   ├── rag.yaml      # RAG configurations (offline docs, online search, etc.)
│   ├── prices.yaml   # Model pricing information
│   └── third_party.yaml  # Third-party service configs
│
└── galaxy/           # Galaxy multi-device configurations
    ├── agent.yaml    # Constellation agent configuration
    ├── constellation.yaml  # Constellation settings
    └── devices.yaml  # Device configurations
```

### Legacy Structure (Still Supported)

```bash
ufo/config/           # Old UFO configurations
├── config.yaml       # ⚠️ Monolithic config (deprecated)
├── config_dev.yaml   # Development overrides
└── ...
```

---

## 🎯 Quick Start

### For New Users

1. **Copy configuration templates:**
   ```bash
   # UFO configuration
   cp config/ufo/agents.yaml.template config/ufo/agents.yaml
   
   # Galaxy configuration
   cp config/galaxy/agent.yaml.template config/galaxy/agent.yaml
   ```

2. **Edit your API keys:**
   ```bash
   # Edit UFO config
   notepad config/ufo/agents.yaml
   
   # Edit Galaxy config
   notepad config/galaxy/agent.yaml
   ```

3. **Validate configuration:**
   ```bash
   python -m ufo.tools.validate_config ufo
   python -m ufo.tools.validate_config galaxy
   ```

### For Existing Users

If you're using the old `ufo/config/` structure:

**Option 1: Automatic Migration (Recommended)**
```bash
# Preview migration
python -m ufo.tools.migrate_config --dry-run

# Perform migration
python -m ufo.tools.migrate_config
```

**Option 2: Manual Migration**
```bash
# Create new directory
mkdir -p config/ufo

# Copy configuration files
cp ufo/config/*.yaml config/ufo/

# Verify it works
python -m ufo.tools.validate_config ufo

# Remove old config (after verification)
rm -rf ufo/config/*.yaml
```

**Option 3: Keep Using Legacy (No Changes Needed)**
- Your old configuration continues to work
- System automatically detects and uses legacy path
- You'll see a migration warning (can be ignored)

---

## 🔧 Configuration Loading Behavior

### Priority Chain

When loading configuration, the system follows this priority:

```
1. config/{module}/     ← Highest priority (new path)
2. {module}/config/     ← Fallback (legacy path)
3. Environment vars     ← Override mechanism
```

### Scenario Behaviors

#### ✅ Scenario A: Only New Config
```bash
config/ufo/agents.yaml  ✓ exists
ufo/config/config.yaml  ✗ does not exist
```
**Behavior:** Uses new config, no warnings

---

#### ⚠️ Scenario B: Only Legacy Config
```bash
config/ufo/agents.yaml  ✗ does not exist
ufo/config/config.yaml  ✓ exists
```
**Behavior:** 
- Uses legacy config (works normally)
- Shows migration warning once per session
- Suggests running migration tool

**Warning Message:**
```
⚠️  LEGACY CONFIG PATH DETECTED: UFO
======================================================================
Using legacy config: ufo/config/
Please migrate to:   config/ufo/

Quick migration:
  mkdir -p config/ufo
  cp ufo/config/*.yaml config/ufo/

Or use migration tool:
  python -m ufo.tools.migrate_config
======================================================================
```

---

#### 🔔 Scenario C: Both Exist (Conflict)
```bash
config/ufo/agents.yaml  ✓ exists
ufo/config/config.yaml  ✓ exists
```
**Behavior:**
- New config takes priority
- Legacy values fill in missing keys
- Conflict warning shown

**Warning Message:**
```
⚠️  CONFIG CONFLICT DETECTED: UFO
======================================================================
Found configurations in BOTH locations:
  1. config/ufo/     ← ACTIVE (using this)
  2. ufo/config/     ← IGNORED (legacy)

Recommendation:
  Remove legacy config to avoid confusion:
  rm -rf ufo/config/*.yaml
======================================================================
```

---

## 🛠️ Configuration Tools

### 1. Migration Tool

Migrate from legacy to modern structure:

```bash
# Interactive migration (recommended)
python -m ufo.tools.migrate_config

# Preview changes (dry run)
python -m ufo.tools.migrate_config --dry-run

# Force migration without confirmation
python -m ufo.tools.migrate_config --force

# Custom paths
python -m ufo.tools.migrate_config \
  --legacy-path ufo/config \
  --new-path config/ufo
```

**Features:**
- ✅ Automatic backup creation
- ✅ Dry run mode (preview)
- ✅ Safety confirmations
- ✅ Detailed migration report

---

### 2. Validation Tool

Validate configuration and detect issues:

```bash
# Validate UFO configuration
python -m ufo.tools.validate_config ufo

# Validate Galaxy configuration
python -m ufo.tools.validate_config galaxy

# Validate both
python -m ufo.tools.validate_config all

# Show detailed configuration
python -m ufo.tools.validate_config ufo --show-config
```

**Checks:**
- ✅ Required fields present
- ✅ Placeholder values detection
- ✅ API configuration validation
- ✅ Path structure validation

---

## 📝 Configuration Best Practices

### 1. Modular Configuration Files

**Good:** Separate concerns into different files
```yaml
# config/ufo/agents.yaml - Only agent configs
HOST_AGENT:
  API_TYPE: "azure_ad"
  API_MODEL: "gpt-4o"

# config/ufo/system.yaml - Only system configs
MAX_STEP: 50
TIMEOUT: 60
```

**Avoid:** Monolithic config files
```yaml
# config/ufo/config.yaml - Everything mixed (harder to maintain)
HOST_AGENT: {...}
APP_AGENT: {...}
MAX_STEP: 50
TIMEOUT: 60
RAG_OFFLINE_DOCS: true
...
```

---

### 2. Environment-Specific Overrides

Use environment-specific files for different setups:

```bash
config/ufo/
├── agents.yaml          # Base configuration
├── agents_dev.yaml      # Development overrides
├── agents_test.yaml     # Test environment overrides
└── agents_prod.yaml     # Production overrides
```

**Usage:**
```bash
# Development
export UFO_ENV=dev
python -m ufo --task test

# Production
export UFO_ENV=prod
python -m ufo --task production_task
```

---

### 3. Sensitive Information

**Never commit API keys to version control!**

**Good:**
```yaml
# config/ufo/agents.yaml - Use environment variables
HOST_AGENT:
  API_KEY: "${UFO_API_KEY}"  # Loaded from environment
```

```bash
# Set in environment
export UFO_API_KEY="your-actual-key"
```

**Also Good:**
```yaml
# config/ufo/agents_local.yaml - Git-ignored file
HOST_AGENT:
  API_KEY: "your-actual-key"
```

```bash
# .gitignore
config/**/agents_local.yaml
config/**/*_local.yaml
```

---

### 4. Configuration Templates

Create templates for team sharing:

```bash
config/ufo/
├── agents.yaml.template     # Template with placeholders
├── agents.yaml              # Actual config (git-ignored)
└── README.md               # Configuration instructions
```

**Template example:**
```yaml
# agents.yaml.template
HOST_AGENT:
  API_TYPE: "azure_ad"  # or "openai" or "aoai"
  API_BASE: "YOUR_ENDPOINT_HERE"
  API_KEY: "YOUR_KEY_HERE"
  API_MODEL: "gpt-4o"
```

---

## 🔍 Troubleshooting

### Issue: "No configuration found"

**Error:**
```
FileNotFoundError: No configuration found for 'ufo'.
Expected at:
  - config/ufo/ (recommended)
  - ufo/config/ (legacy)
```

**Solution:**
1. Check if configuration files exist:
   ```bash
   ls config/ufo/
   ls ufo/config/
   ```

2. Copy from template:
   ```bash
   cp config/ufo/agents.yaml.template config/ufo/agents.yaml
   ```

3. Or migrate from legacy:
   ```bash
   python -m ufo.tools.migrate_config
   ```

---

### Issue: "Placeholder value detected"

**Warning:**
```
⚠️  Placeholder value detected: HOST_AGENT.API_KEY = 'YOUR_KEY'
    Please update with actual value
```

**Solution:**
Edit the configuration file and replace placeholders:
```yaml
# Before
API_KEY: "YOUR_KEY"

# After
API_KEY: "sk-your-actual-openai-key"
```

---

### Issue: Configuration not loading changes

**Symptom:** Changes to YAML files not reflected

**Solution:**
Clear configuration cache:
```python
from config.config_loader import clear_config_cache
clear_config_cache()
```

Or restart the application.

---

## 📚 Advanced Topics

### Custom Configuration Paths

Override default paths programmatically:

```python
from config.config_loader import ConfigLoader

# Custom base path
loader = ConfigLoader(base_path="custom/config")
config = loader.load_ufo_config()
```

---

### Dynamic Configuration Access

Access any YAML field without code changes:

```python
from config.config_loader import get_ufo_config

config = get_ufo_config()

# Type-safe access (recommended)
max_step = config.system.max_step

# Dynamic access (for new fields)
if hasattr(config, 'NEW_FEATURE'):
    enabled = config.NEW_FEATURE

# Dict-style access (backward compatible)
timeout = config["TIMEOUT"]
agent = config["HOST_AGENT"]
```

---

### Configuration Merging

When multiple YAML files exist, they are deep-merged:

```yaml
# config/ufo/agents.yaml
HOST_AGENT:
  API_TYPE: "openai"
  API_KEY: "sk-..."

# config/ufo/agents_dev.yaml (UFO_ENV=dev)
HOST_AGENT:
  API_TYPE: "azure_ad"  # Overrides
  # API_KEY inherited from base
```

**Result:**
```yaml
HOST_AGENT:
  API_TYPE: "azure_ad"  # From dev override
  API_KEY: "sk-..."     # From base config
```

---

## 🎓 Migration Timeline

### Current (v3.0)
- ✅ Both new and legacy paths supported
- ✅ Automatic fallback with warnings
- ✅ Migration tools available

### Future (v3.1 - v3.5)
- 📢 Continued migration warnings
- 📚 Enhanced documentation
- 🛠️ Improved migration tools

### Long-term (v4.0+)
- 🔄 Legacy path may be deprecated
- 📅 Minimum 1-year transition period
- 📢 Advance notice before removal

---

## 💡 FAQ

**Q: Do I need to migrate immediately?**  
A: No! Legacy configuration continues to work. Migrate when convenient.

**Q: What if migration fails?**  
A: Migration tool creates automatic backups. You can rollback anytime.

**Q: Can I use both structures?**  
A: Yes, but not recommended. New path takes priority if both exist.

**Q: Will migration break my workflows?**  
A: No! Both paths load the same configuration. Thoroughly tested for compatibility.

**Q: How do I know which path is being used?**  
A: Run validation tool:
```bash
python -m ufo.tools.validate_config ufo
```

---

## 📞 Get Help

- 📖 **Documentation:** [https://microsoft.github.io/UFO/](https://microsoft.github.io/UFO/)
- 🐛 **Issues:** [GitHub Issues](https://github.com/microsoft/UFO/issues)
- 💬 **Discussions:** [GitHub Discussions](https://github.com/microsoft/UFO/discussions)
- 📧 **Email:** ufo-agent@microsoft.com

---

<sub>© Microsoft 2025 | UFO³ Configuration Management</sub>
