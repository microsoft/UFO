# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Test suite for configuration loading with backward compatibility.

Tests cover:
- Configuration loading from new and legacy paths
- Priority chain (new > legacy > env)
- Conflict detection and warnings
- Configuration merging
- Type-safe and dynamic access
- Environment-specific overrides
"""

import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import yaml


class TestConfigLoader(unittest.TestCase):
    """Test ConfigLoader class."""

    def setUp(self):
        """Set up test environment."""
        self.test_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.test_dir)

        # Change to test directory
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)
        self.addCleanup(os.chdir, self.original_cwd)

    def create_config_file(self, path: str, content: dict):
        """Helper to create a config file."""
        file_path = Path(self.test_dir) / path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "w") as f:
            yaml.dump(content, f)
        return file_path

    def test_load_new_config_only(self):
        """Test loading from new config path only."""
        # Create new config
        new_config = {
            "HOST_AGENT": {"API_TYPE": "openai", "API_MODEL": "gpt-4o"},
            "MAX_STEP": 50,
        }
        self.create_config_file("config/ufo/test.yaml", new_config)

        # Load config
        from config.config_loader import ConfigLoader

        loader = ConfigLoader()
        config_data = loader._load_with_fallback("ufo")

        # Verify
        self.assertEqual(config_data["MAX_STEP"], 50)
        self.assertEqual(config_data["HOST_AGENT"]["API_TYPE"], "openai")

    def test_load_legacy_config_only(self):
        """Test loading from legacy config path only."""
        # Create legacy config
        legacy_config = {
            "HOST_AGENT": {"API_TYPE": "aoai", "API_MODEL": "gpt-4"},
            "MAX_STEP": 30,
        }
        self.create_config_file("ufo/config/test.yaml", legacy_config)

        # Load config
        from config.config_loader import ConfigLoader

        loader = ConfigLoader()
        config_data = loader._load_with_fallback("ufo")

        # Verify
        self.assertEqual(config_data["MAX_STEP"], 30)
        self.assertEqual(config_data["HOST_AGENT"]["API_TYPE"], "aoai")

    def test_load_both_configs_new_priority(self):
        """Test loading when both new and legacy configs exist (new has priority)."""
        # Create new config
        new_config = {"MAX_STEP": 50, "NEW_FIELD": "new_value"}
        self.create_config_file("config/ufo/test.yaml", new_config)

        # Create legacy config
        legacy_config = {"MAX_STEP": 30, "LEGACY_FIELD": "legacy_value"}
        self.create_config_file("ufo/config/test.yaml", legacy_config)

        # Load config
        from config.config_loader import ConfigLoader

        loader = ConfigLoader()
        config_data = loader._load_with_fallback("ufo")

        # Verify: new overrides legacy, but legacy fills missing keys
        self.assertEqual(config_data["MAX_STEP"], 50)  # From new
        self.assertEqual(config_data["NEW_FIELD"], "new_value")  # From new
        self.assertEqual(config_data["LEGACY_FIELD"], "legacy_value")  # From legacy

    def test_deep_merge_configs(self):
        """Test deep merging of nested configurations."""
        # Create new config
        new_config = {"HOST_AGENT": {"API_TYPE": "openai", "API_MODEL": "gpt-4o"}}
        self.create_config_file("config/ufo/test.yaml", new_config)

        # Create legacy config with additional fields
        legacy_config = {
            "HOST_AGENT": {
                "API_TYPE": "aoai",  # Will be overridden
                "API_KEY": "sk-123",  # Will be merged
            }
        }
        self.create_config_file("ufo/config/test.yaml", legacy_config)

        # Load config
        from config.config_loader import ConfigLoader

        loader = ConfigLoader()
        config_data = loader._load_with_fallback("ufo")

        # Verify deep merge
        self.assertEqual(config_data["HOST_AGENT"]["API_TYPE"], "openai")  # Overridden
        self.assertEqual(config_data["HOST_AGENT"]["API_MODEL"], "gpt-4o")  # From new
        self.assertEqual(config_data["HOST_AGENT"]["API_KEY"], "sk-123")  # From legacy

    def test_multiple_yaml_files_merge(self):
        """Test merging multiple YAML files in same directory."""
        # Create multiple config files
        config1 = {"HOST_AGENT": {"API_TYPE": "openai"}}
        config2 = {"APP_AGENT": {"API_TYPE": "aoai"}}
        config3 = {"MAX_STEP": 50}

        self.create_config_file("config/ufo/agents.yaml", config1)
        self.create_config_file("config/ufo/system.yaml", config3)
        self.create_config_file("config/ufo/backup.yaml", config2)

        # Load config
        from config.config_loader import ConfigLoader

        loader = ConfigLoader()
        config_data = loader._load_with_fallback("ufo")

        # Verify all files merged
        self.assertIn("HOST_AGENT", config_data)
        self.assertIn("APP_AGENT", config_data)
        self.assertEqual(config_data["MAX_STEP"], 50)

    def test_environment_overrides(self):
        """Test environment-specific configuration overrides."""
        # Create base config
        base_config = {"MAX_STEP": 50, "TIMEOUT": 60}
        self.create_config_file("config/ufo/config.yaml", base_config)

        # Create dev override
        dev_config = {"MAX_STEP": 100}  # Override MAX_STEP
        self.create_config_file("config/ufo/config_dev.yaml", dev_config)

        # Load with dev environment
        from config.config_loader import ConfigLoader

        loader = ConfigLoader()
        config_data = loader._load_with_fallback("ufo", env="dev")

        # Verify override
        self.assertEqual(config_data["MAX_STEP"], 100)  # Overridden
        self.assertEqual(config_data["TIMEOUT"], 60)  # Preserved

    def test_no_config_found_error(self):
        """Test error when no configuration is found."""
        from config.config_loader import ConfigLoader

        loader = ConfigLoader()

        # Should raise FileNotFoundError
        with self.assertRaises(FileNotFoundError) as context:
            loader._load_with_fallback("ufo")

        self.assertIn("No configuration found", str(context.exception))

    def test_yaml_parsing_error_handling(self):
        """Test handling of invalid YAML files."""
        # Create a valid YAML file and an invalid one
        valid_path = Path(self.test_dir) / "config/ufo/valid.yaml"
        valid_path.parent.mkdir(parents=True, exist_ok=True)
        with open(valid_path, "w") as f:
            yaml.dump({"VALID_KEY": "valid_value"}, f)

        invalid_path = Path(self.test_dir) / "config/ufo/invalid.yaml"
        with open(invalid_path, "w") as f:
            f.write("invalid: yaml: content: [")

        # Load should handle error gracefully - skip invalid, load valid
        from config.config_loader import ConfigLoader

        loader = ConfigLoader()
        # Should not crash, just skip invalid file and load valid one
        config_data = loader._load_with_fallback("ufo")
        # Should have loaded the valid file
        self.assertIsInstance(config_data, dict)
        self.assertEqual(config_data.get("VALID_KEY"), "valid_value")

    def test_cache_mechanism(self):
        """Test configuration caching."""
        # Create config
        config = {"MAX_STEP": 50}
        config_path = self.create_config_file("config/ufo/test.yaml", config)

        from config.config_loader import ConfigLoader

        loader = ConfigLoader()

        # Load twice
        config1 = loader._load_yaml(config_path)
        config2 = loader._load_yaml(config_path)

        # Should return same object from cache
        self.assertIs(config1, config2)

    def test_warning_on_duplicate_configs(self):
        """Test warning message when both configs exist."""
        # Create both configs
        self.create_config_file("config/ufo/test.yaml", {"MAX_STEP": 50})
        self.create_config_file("ufo/config/test.yaml", {"MAX_STEP": 30})

        from config.config_loader import ConfigLoader

        loader = ConfigLoader()

        # Should log warning (captured in _warnings_shown)
        with patch("config.config_loader.logger.warning") as mock_warning:
            loader._load_with_fallback("ufo")
            mock_warning.assert_called()
            # Check warning contains conflict message
            warning_msg = mock_warning.call_args[0][0]
            self.assertIn("CONFIG CONFLICT", warning_msg)

    def test_warning_on_legacy_config(self):
        """Test warning message when using legacy config."""
        # Create only legacy config
        self.create_config_file("ufo/config/test.yaml", {"MAX_STEP": 30})

        from config.config_loader import ConfigLoader

        loader = ConfigLoader()

        # Should log warning
        with patch("config.config_loader.logger.warning") as mock_warning:
            loader._load_with_fallback("ufo")
            mock_warning.assert_called()
            # Check warning contains legacy path message
            warning_msg = mock_warning.call_args[0][0]
            self.assertIn("LEGACY CONFIG PATH", warning_msg)


class TestUFOConfig(unittest.TestCase):
    """Test UFOConfig typed configuration."""

    def setUp(self):
        """Set up test environment."""
        self.test_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.test_dir)

        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)
        self.addCleanup(os.chdir, self.original_cwd)

    def create_config_file(self, path: str, content: dict):
        """Helper to create a config file."""
        file_path = Path(self.test_dir) / path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "w") as f:
            yaml.dump(content, f)
        return file_path

    def test_typed_access(self):
        """Test type-safe access to configuration."""
        # Create config
        config_data = {
            "HOST_AGENT": {"API_TYPE": "openai", "API_MODEL": "gpt-4o"},
            "APP_AGENT": {"API_TYPE": "aoai", "API_MODEL": "gpt-4"},
            "MAX_STEP": 50,
            "TIMEOUT": 60,
        }
        self.create_config_file("config/ufo/test.yaml", config_data)

        from config.config_loader import get_ufo_config, clear_config_cache

        clear_config_cache()
        config = get_ufo_config()

        # Test typed access
        self.assertEqual(config.host_agent.api_type, "openai")
        self.assertEqual(config.app_agent.api_model, "gpt-4")
        self.assertEqual(config.system.max_step, 50)

    def test_dict_access_backward_compatible(self):
        """Test backward-compatible dict-style access."""
        config_data = {
            "HOST_AGENT": {"API_TYPE": "openai"},
            "MAX_STEP": 50,
        }
        self.create_config_file("config/ufo/test.yaml", config_data)

        from config.config_loader import get_ufo_config, clear_config_cache

        clear_config_cache()
        config = get_ufo_config()

        # Test dict access
        self.assertEqual(config["MAX_STEP"], 50)
        self.assertEqual(config["HOST_AGENT"]["API_TYPE"], "openai")

    def test_dynamic_field_access(self):
        """Test access to dynamic fields not in schema."""
        config_data = {
            "HOST_AGENT": {"API_TYPE": "openai"},
            "NEW_CUSTOM_FIELD": "custom_value",
            "EXPERIMENTAL_FEATURE": True,
        }
        self.create_config_file("config/ufo/test.yaml", config_data)

        from config.config_loader import get_ufo_config, clear_config_cache

        clear_config_cache()
        config = get_ufo_config()

        # Test dynamic access
        self.assertEqual(config.NEW_CUSTOM_FIELD, "custom_value")
        self.assertTrue(config.EXPERIMENTAL_FEATURE)
        self.assertEqual(config["NEW_CUSTOM_FIELD"], "custom_value")

    def test_nested_dynamic_access(self):
        """Test nested dynamic field access."""
        config_data = {"CUSTOM_SECTION": {"nested_field": "nested_value", "count": 42}}
        self.create_config_file("config/ufo/test.yaml", config_data)

        from config.config_loader import get_ufo_config, clear_config_cache

        clear_config_cache()
        config = get_ufo_config()

        # Test nested access
        custom = config.CUSTOM_SECTION
        self.assertEqual(custom.nested_field, "nested_value")
        self.assertEqual(custom.count, 42)


class TestGalaxyConfig(unittest.TestCase):
    """Test GalaxyConfig configuration."""

    def setUp(self):
        """Set up test environment."""
        self.test_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.test_dir)

        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)
        self.addCleanup(os.chdir, self.original_cwd)

    def create_config_file(self, path: str, content: dict):
        """Helper to create a config file."""
        file_path = Path(self.test_dir) / path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "w") as f:
            yaml.dump(content, f)
        return file_path

    def test_galaxy_config_loading(self):
        """Test Galaxy configuration loading."""
        config_data = {
            "CONSTELLATION_AGENT": {
                "API_TYPE": "azure_ad",
                "API_MODEL": "gpt-4o",
            },
            "DEVICE_INFO": "config/galaxy/devices.yaml",
        }
        self.create_config_file("config/galaxy/agent.yaml", config_data)

        from config.config_loader import get_galaxy_config, clear_config_cache

        clear_config_cache()
        config = get_galaxy_config()

        # Test typed access
        self.assertEqual(config.constellation_agent.api_type, "azure_ad")
        self.assertEqual(config.constellation_agent.api_model, "gpt-4o")

        # Test dynamic access
        self.assertEqual(config.DEVICE_INFO, "config/galaxy/devices.yaml")

    def test_galaxy_no_legacy_fallback(self):
        """Test that Galaxy has no legacy path fallback."""
        # Galaxy should only check config/galaxy/, not galaxy/config/
        from config.config_loader import ConfigLoader

        loader = ConfigLoader()

        # Should raise error if no config found
        with self.assertRaises(FileNotFoundError):
            loader._load_with_fallback("galaxy")


class TestAPIBaseTransformations(unittest.TestCase):
    """Test API base URL transformations for different API types."""

    def test_aoai_api_base_transformation(self):
        """Test Azure OpenAI API base transformation."""
        from config.config_loader import ConfigLoader

        loader = ConfigLoader()
        config = {
            "HOST_AGENT": {
                "API_TYPE": "aoai",
                "API_BASE": "https://test.openai.azure.com",
                "API_DEPLOYMENT_ID": "gpt-4-deployment",
                "API_VERSION": "2024-02-15-preview",
            }
        }

        loader._apply_legacy_transforms(config)

        # Should have deployment URL constructed
        expected_base = (
            "https://test.openai.azure.com/openai/deployments/"
            "gpt-4-deployment/chat/completions?api-version=2024-02-15-preview"
        )
        self.assertEqual(config["HOST_AGENT"]["API_BASE"], expected_base)
        self.assertEqual(config["HOST_AGENT"]["API_MODEL"], "gpt-4-deployment")

    def test_openai_api_base_default(self):
        """Test OpenAI API base default value."""
        from config.config_loader import ConfigLoader

        loader = ConfigLoader()
        config = {"HOST_AGENT": {"API_TYPE": "openai"}}

        loader._apply_legacy_transforms(config)

        # Should have default OpenAI base
        self.assertEqual(
            config["HOST_AGENT"]["API_BASE"],
            "https://api.openai.com/v1/chat/completions",
        )

    def test_control_backend_list_conversion(self):
        """Test CONTROL_BACKEND string to list conversion."""
        from config.config_loader import ConfigLoader

        loader = ConfigLoader()
        config = {"CONTROL_BACKEND": "uia"}

        loader._apply_legacy_transforms(config)

        # Should be converted to list
        self.assertEqual(config["CONTROL_BACKEND"], ["uia"])


class TestConfigCaching(unittest.TestCase):
    """Test configuration caching mechanisms."""

    def test_global_config_cache(self):
        """Test global configuration caching."""
        from config.config_loader import (
            get_ufo_config,
            clear_config_cache,
            _global_ufo_config,
        )

        # Clear cache
        clear_config_cache()

        # First load
        config1 = get_ufo_config()

        # Second load should return same instance
        config2 = get_ufo_config()

        self.assertIs(config1, config2)

    def test_cache_reload(self):
        """Test configuration reload functionality."""
        from config.config_loader import get_ufo_config, clear_config_cache

        # Load once
        config1 = get_ufo_config()

        # Force reload
        config2 = get_ufo_config(reload=True)

        # Should be different instances after reload
        self.assertIsNot(config1, config2)


if __name__ == "__main__":
    unittest.main()
