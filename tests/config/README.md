# Configuration System Test Suite

Comprehensive test suite for the UFO³ configuration management system.

## Test Structure

```
tests/config/
├── __init__.py                  # Test runner
├── test_config_loader.py        # Core configuration loading tests
├── test_migration.py            # Migration tool tests
├── test_validation.py           # Validation tool tests
└── README.md                    # This file
```

## Running Tests

### Run All Tests

```bash
# Using unittest
python -m unittest discover tests/config

# Using pytest (if installed)
python -m pytest tests/config/

# Using test runner
python tests/config/__init__.py
```

### Run Specific Test File

```bash
# Configuration loader tests
python -m pytest tests/config/test_config_loader.py

# Migration tool tests
python -m pytest tests/config/test_migration.py

# Validation tool tests
python -m pytest tests/config/test_validation.py
```

### Run Specific Test Class or Method

```bash
# Run specific test class
python -m pytest tests/config/test_config_loader.py::TestConfigLoader

# Run specific test method
python -m pytest tests/config/test_config_loader.py::TestConfigLoader::test_load_new_config_only
```

### Run with Coverage

```bash
# Generate coverage report
python -m pytest tests/config/ --cov=config --cov-report=html

# View coverage report
open htmlcov/index.html
```

### Run with Verbose Output

```bash
python -m pytest tests/config/ -v
```

## Test Coverage

### test_config_loader.py

**TestConfigLoader** - Core configuration loading
- ✅ `test_load_new_config_only` - Load from new path only
- ✅ `test_load_legacy_config_only` - Load from legacy path only
- ✅ `test_load_both_configs_new_priority` - Priority when both exist
- ✅ `test_deep_merge_configs` - Deep merging of nested configs
- ✅ `test_multiple_yaml_files_merge` - Multiple YAML files merge
- ✅ `test_environment_overrides` - Environment-specific overrides
- ✅ `test_no_config_found_error` - Error when no config exists
- ✅ `test_yaml_parsing_error_handling` - Handle invalid YAML
- ✅ `test_cache_mechanism` - Configuration caching
- ✅ `test_warning_on_duplicate_configs` - Warning for conflicts
- ✅ `test_warning_on_legacy_config` - Warning for legacy usage

**TestUFOConfig** - UFO configuration functionality
- ✅ `test_typed_access` - Type-safe configuration access
- ✅ `test_dict_access_backward_compatible` - Dict-style access
- ✅ `test_dynamic_field_access` - Dynamic YAML field access
- ✅ `test_nested_dynamic_access` - Nested dynamic fields

**TestGalaxyConfig** - Galaxy configuration functionality
- ✅ `test_galaxy_config_loading` - Galaxy config loading
- ✅ `test_galaxy_no_legacy_fallback` - No legacy path for Galaxy

**TestAPIBaseTransformations** - API URL transformations
- ✅ `test_aoai_api_base_transformation` - Azure OpenAI URL construction
- ✅ `test_openai_api_base_default` - OpenAI default URL
- ✅ `test_control_backend_list_conversion` - Backend list conversion

**TestConfigCaching** - Caching mechanisms
- ✅ `test_global_config_cache` - Global cache functionality
- ✅ `test_cache_reload` - Configuration reload

### test_migration.py

**TestConfigMigrator** - Migration tool functionality
- ✅ `test_check_legacy_exists` - Detect legacy configuration
- ✅ `test_check_legacy_not_exists` - Handle missing legacy config
- ✅ `test_discover_files` - Discover YAML files
- ✅ `test_dry_run_migration` - Dry run mode (no changes)
- ✅ `test_actual_migration` - Actual file migration
- ✅ `test_backup_creation` - Automatic backup creation
- ✅ `test_migration_preserves_content` - Content preservation
- ✅ `test_no_overwrite_without_confirmation` - Safety checks

**TestMigrationScenarios** - Various migration scenarios
- ✅ `test_migration_with_subdirectories` - Handle subdirectories
- ✅ `test_migration_empty_legacy` - Handle empty legacy path
- ✅ `test_migration_preserves_file_permissions` - Preserve permissions

### test_validation.py

**TestConfigValidator** - Validation tool functionality
- ✅ `test_valid_ufo_config` - Validate valid configuration
- ✅ `test_missing_required_section` - Detect missing sections
- ✅ `test_placeholder_value_detection` - Detect placeholder values
- ✅ `test_azure_ad_validation` - Azure AD specific validation
- ✅ `test_aoai_deployment_id_warning` - AOAI deployment ID check
- ✅ `test_path_detection_new_only` - Detect new path only
- ✅ `test_path_detection_legacy_only` - Detect legacy path only
- ✅ `test_path_detection_both` - Detect both paths (conflict)
- ✅ `test_no_config_error` - Error when no config exists

**TestGalaxyValidator** - Galaxy validation
- ✅ `test_valid_galaxy_config` - Validate Galaxy configuration
- ✅ `test_galaxy_no_legacy_path` - No legacy path for Galaxy

## Test Statistics

- **Total Test Files:** 3
- **Total Test Classes:** 10
- **Total Test Methods:** 40+
- **Code Coverage Target:** >85%

## Test Scenarios Covered

### Configuration Loading Scenarios
1. ✅ New config only (ideal path)
2. ✅ Legacy config only (backward compatibility)
3. ✅ Both configs (conflict handling with priority)
4. ✅ No config (error handling)
5. ✅ Multiple YAML files (merging)
6. ✅ Environment overrides (dev/test/prod)
7. ✅ Invalid YAML (error handling)
8. ✅ Nested configuration (deep merge)

### Migration Scenarios
1. ✅ Dry run (preview only)
2. ✅ Actual migration (file copying)
3. ✅ Backup creation
4. ✅ Content preservation
5. ✅ Permission preservation
6. ✅ Empty legacy path
7. ✅ Existing new config (no overwrite)

### Validation Scenarios
1. ✅ Valid configuration
2. ✅ Missing required sections
3. ✅ Missing required fields
4. ✅ Placeholder value detection
5. ✅ API-specific validation (OpenAI, AOAI, Azure AD)
6. ✅ Path conflict detection
7. ✅ Legacy path warning

### Access Pattern Scenarios
1. ✅ Typed access (config.system.max_step)
2. ✅ Dict access (config["MAX_STEP"])
3. ✅ Dynamic access (config.NEW_FIELD)
4. ✅ Nested access (config.host_agent.api_key)
5. ✅ Attribute access (config.CUSTOM_SETTING)

## Quick Test Commands

```bash
# Fast test (skip slow tests)
pytest tests/config/ -m "not slow"

# Test specific functionality
pytest tests/config/ -k "migration"
pytest tests/config/ -k "validation"
pytest tests/config/ -k "loader"

# Test with markers
pytest tests/config/ -m "unit"
pytest tests/config/ -m "integration"

# Stop on first failure
pytest tests/config/ -x

# Show test durations
pytest tests/config/ --durations=10
```

## Debugging Tests

```bash
# Run with pdb debugger on failure
pytest tests/config/ --pdb

# Verbose output with print statements
pytest tests/config/ -s

# Show local variables on failure
pytest tests/config/ -l
```

## CI/CD Integration

Tests are designed to run in CI/CD pipelines:

```yaml
# Example GitHub Actions
- name: Run Config Tests
  run: |
    python -m pytest tests/config/ \
      --cov=config \
      --cov-report=xml \
      --junitxml=test-results.xml
```

## Contributing

When adding new features to the configuration system:

1. **Write tests first** (TDD approach)
2. **Cover edge cases** (error handling, invalid input)
3. **Test backward compatibility** (legacy path support)
4. **Update this README** with new test descriptions

## Test Dependencies

Required packages for testing:
- `pytest` - Test framework
- `pytest-cov` - Coverage reporting
- `pyyaml` - YAML parsing
- `rich` - CLI output (for migration/validation tools)

Install with:
```bash
pip install pytest pytest-cov pyyaml rich
```

## Known Issues

- Windows path handling may differ from Unix in some tests
- File permission tests may not work identically on all OS platforms
- Temporary directory cleanup may fail if files are in use

## Contact

For test-related questions:
- **Issues:** https://github.com/microsoft/UFO/issues
- **Email:** ufo-agent@microsoft.com
