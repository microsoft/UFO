# Extending Configuration

This guide shows you how to add custom configuration options to UFO2.

**Three Ways to Extend:**

1. **Simple YAML files** - Quick custom settings in existing files
2. **New configuration files** - Organize new features separately  
3. **Typed configuration schemas** - Full type safety with Python dataclasses

## Method 1: Adding Fields to Existing Files

For simple customizations, add fields directly to existing configuration files.

```yaml
    # config/ufo/system.yaml
    MAX_STEP: 20
    SLEEP_TIME: 1.0

    # Your custom fields
    CUSTOM_TIMEOUT: 300
    DEBUG_MODE: true
    FEATURE_FLAGS:
      enable_telemetry: false
      use_experimental_api: true
```

### Accessing Custom Fields

```python
    from config.config_loader import get_ufo_config

    config = get_ufo_config()

    # Access custom fields dynamically
    timeout = config.system.CUSTOM_TIMEOUT  # 300
    debug = config.system.DEBUG_MODE         # True
    use_experimental = config.system.FEATURE_FLAGS['use_experimental_api']  # True
```

Custom fields are automatically discovered and loaded - no code modifications needed!

---

## Method 2: Creating New Configuration Files

For larger features, create dedicated configuration files.

```yaml
    # config/ufo/analytics.yaml
    ANALYTICS:
      enabled: true
      backend: "influxdb"
      endpoint: "http://localhost:8086"
      database: "ufo_metrics"
      retention: "30d"
      
      metrics:
        - name: "task_duration"
          type: "histogram"
        - name: "success_rate"
          type: "counter"
    ```

### Automatic Discovery

The config loader automatically discovers and loads all YAML files in `config/ufo/`:

```python
# No registration needed!
config = get_ufo_config()

# Your new file is automatically loaded
analytics_enabled = config.ANALYTICS['enabled']
metrics = config.ANALYTICS['metrics']
```

---

## Method 3: Typed Configuration Schemas

For production features requiring type safety and validation, define typed schemas.

```python
    # config/config_schemas.py
    from dataclasses import dataclass, field
    from typing import List, Literal

    @dataclass
    class MetricConfig:
        """Configuration for a single metric."""
        name: str
        type: Literal["counter", "histogram", "gauge"]
        tags: List[str] = field(default_factory=list)

    @dataclass
    class AnalyticsConfig:
        """Analytics system configuration."""
        
        # Required fields
        enabled: bool
        backend: Literal["influxdb", "prometheus", "datadog"]
        endpoint: str
        
        # Optional fields with defaults
        database: str = "ufo_metrics"
        retention: str = "30d"
        batch_size: int = 100
        flush_interval: float = 10.0
        
        # Nested configuration
        metrics: List[MetricConfig] = field(default_factory=list)
        
        def __post_init__(self):
            """Validate configuration after initialization."""
            if self.enabled and not self.endpoint:
                raise ValueError("endpoint required when analytics enabled")
            
            if self.batch_size <= 0:
                raise ValueError("batch_size must be positive")
```

### Step 2: Integrate into UFOConfig

```python
    # config/config_schemas.py
    from dataclasses import dataclass

    @dataclass
    class UFOConfig:
        """Main UFO configuration."""
        host_agent: AgentConfig
        app_agent: AgentConfig
        system: SystemConfig
        rag: RAGConfig
        analytics: AnalyticsConfig  # Add your new config
        
        # ... rest of implementation
```

### Step 3: Use Typed Configuration

```python
    from config.config_loader import get_ufo_config

    config = get_ufo_config()

    # Type-safe access with IDE autocomplete
    if config.analytics.enabled:
        for metric in config.analytics.metrics:
            print(f"Metric: {metric.name}, Type: {metric.type}")
        
        # Validation happens automatically
        batch_size = config.analytics.batch_size  # Guaranteed > 0
```

---

## Common Patterns

### Environment-Specific Overrides

```yaml
    # config/ufo/system.yaml (base)
    LOG_LEVEL: "INFO"
    DEBUG_MODE: false
    CACHE_SIZE: 1000

    # config/ufo/system.dev.yaml (development override)
    LOG_LEVEL: "DEBUG"
    DEBUG_MODE: true
    PROFILING_ENABLED: true

    # config/ufo/system.prod.yaml (production override)
    LOG_LEVEL: "WARNING"
    CACHE_SIZE: 10000
    MONITORING_ENABLED: true
```

### Feature Flags

```yaml
    # config/ufo/features.yaml
    FEATURES:
      experimental_actions: false
      multi_device_mode: true
      advanced_logging: false
      
      # Per-agent feature flags
      agent_features:
        host_agent:
          use_vision_model: true
          parallel_processing: false
        app_agent:
          speculative_execution: true
          action_batching: true
```

### Plugin Configuration

```yaml
    # config/ufo/plugins.yaml
    PLUGINS:
      enabled: true
      auto_discover: true
      load_order:
        - "core"
        - "analytics"
        - "custom"
      
      plugins:
        analytics:
          enabled: true
          config_file: "config/plugins/analytics.yaml"
        
        custom_processor:
          enabled: false
          class: "plugins.custom.MyProcessor"
          priority: 100
```

---

## Best Practices

**DO - Recommended Practices**

- ✅ **Group related settings** in dedicated files
- ✅ **Use typed schemas** for production features
- ✅ **Provide sensible defaults** for all optional fields
- ✅ **Add validation** in `__post_init__` methods
- ✅ **Document all fields** with docstrings
- ✅ **Use environment overrides** for deployment-specific settings
- ✅ **Version your config schemas** when making breaking changes
- ✅ **Test configuration loading** in CI/CD pipelines

**DON'T - Anti-Patterns**

- ❌ **Don't hardcode secrets** - use environment variables
- ❌ **Don't duplicate settings** across multiple files
- ❌ **Don't use dynamic field names** - breaks type safety
- ❌ **Don't skip validation** - catch errors early
- ❌ **Don't mix concerns** - keep configs focused
- ❌ **Don't ignore warnings** from config loader
- ❌ **Don't commit sensitive data** - use .env files

---

## Security Considerations

!!!warning "Secrets Management"
    Never commit sensitive data to configuration files:
    
    ```yaml
    # ? BAD - Hardcoded secrets
    DATABASE:
      password: "my-secret-password"
      api_key: "sk-1234567890"
    
    # ? GOOD - Environment variable references
    DATABASE:
      password: "${DB_PASSWORD}"
      api_key: "${API_KEY}"
    ```

### "Environment Variables"
Use environment variables for secrets:

```python
import os
from config.config_loader import get_ufo_config

config = get_ufo_config()

# Resolve environment variables
db_password = os.getenv('DB_PASSWORD')
api_key = os.getenv('API_KEY')
```

---

## Testing Your Configuration

```python
    import pytest
    from config.config_loader import ConfigLoader
    from config.ufo.schemas.analytics_config import AnalyticsConfig

    def test_analytics_config_defaults():
        """Test analytics configuration defaults."""
        config_data = {
            'enabled': True,
            'backend': 'influxdb',
            'endpoint': 'http://localhost:8086'
        }
        
        analytics = AnalyticsConfig(**config_data)
        
        assert analytics.enabled is True
        assert analytics.database == 'ufo_metrics'  # Default
        assert analytics.batch_size == 100          # Default

    def test_analytics_config_validation():
        """Test analytics configuration validation."""
        with pytest.raises(ValueError, match="endpoint required"):
            AnalyticsConfig(enabled=True, backend='influxdb', endpoint='')
        
        with pytest.raises(ValueError, match="batch_size must be positive"):
            AnalyticsConfig(
                enabled=True,
                backend='influxdb',
                endpoint='http://localhost',
                batch_size=-1
            )

    def test_config_loading():
        """Test full configuration loading."""
        loader = ConfigLoader()
        config = loader.load_ufo_config('config/ufo')
        
        # Verify custom configuration loaded
        assert hasattr(config, 'analytics')
        assert config.analytics.enabled in [True, False]
```

---

## Next Steps

- **[Agents Configuration](./agents_config.md)** - LLM and agent settings
- **[System Configuration](./system_config.md)** - Runtime and execution settings
- **[RAG Configuration](./rag_config.md)** - Knowledge retrieval settings
- **[Migration Guide](./migration.md)** - Migrate from legacy configuration
- **[Configuration Overview](./overview.md)** - Understand configuration system design
