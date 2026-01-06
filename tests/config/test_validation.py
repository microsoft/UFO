# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Integration tests for configuration validation tool.

Tests cover:
- Configuration validation
- Path detection
- Field validation
- API configuration validation
- Error reporting
"""

import os
import shutil
import tempfile
import unittest
from pathlib import Path

import yaml


class TestConfigValidator(unittest.TestCase):
    """Test ConfigValidator class."""

    def setUp(self):
        """Set up test environment."""
        self.test_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.test_dir)

        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)
        self.addCleanup(os.chdir, self.original_cwd)

        import sys

        sys.path.insert(0, self.original_cwd)

    def create_config_file(self, path: str, content: dict):
        """Helper to create a config file."""
        file_path = Path(self.test_dir) / path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "w") as f:
            yaml.dump(content, f)
        return file_path

    def test_valid_ufo_config(self):
        """Test validation of valid UFO configuration."""
        from ufo.tools.validate_config import ConfigValidator

        # Create valid config
        config = {
            "HOST_AGENT": {
                "API_TYPE": "openai",
                "API_KEY": "sk-real-key",
                "API_MODEL": "gpt-4o",
            },
            "APP_AGENT": {
                "API_TYPE": "openai",
                "API_KEY": "sk-real-key",
                "API_MODEL": "gpt-4o",
            },
        }
        self.create_config_file("config/ufo/agents.yaml", config)

        validator = ConfigValidator("ufo")
        result = validator.validate_structure()

        self.assertTrue(result)
        self.assertEqual(len(validator.errors), 0)

    def test_missing_required_section(self):
        """Test detection of missing required sections."""
        from ufo.tools.validate_config import ConfigValidator

        # Create config missing HOST_AGENT
        config = {
            "APP_AGENT": {
                "API_TYPE": "openai",
                "API_KEY": "sk-key",
                "API_MODEL": "gpt-4o",
            }
        }
        self.create_config_file("config/ufo/agents.yaml", config)

        validator = ConfigValidator("ufo")
        validator.validate_structure()

        # Load config to validate fields
        from config.config_loader import get_ufo_config, clear_config_cache

        clear_config_cache()
        config_obj = get_ufo_config()
        validator.validate_fields(config_obj._raw)

        # Should have error about missing HOST_AGENT
        self.assertGreater(len(validator.errors), 0)
        self.assertTrue(any("HOST_AGENT" in error for error in validator.errors))

    def test_placeholder_value_detection(self):
        """Test detection of placeholder values."""
        from ufo.tools.validate_config import ConfigValidator

        # Create config with placeholders
        config = {
            "HOST_AGENT": {
                "API_TYPE": "openai",
                "API_KEY": "YOUR_KEY",  # Placeholder
                "API_MODEL": "gpt-4o",
            },
            "APP_AGENT": {
                "API_TYPE": "openai",
                "API_KEY": "sk-",  # Placeholder
                "API_MODEL": "gpt-4o",
            },
        }
        self.create_config_file("config/ufo/agents.yaml", config)

        validator = ConfigValidator("ufo")
        validator.validate_structure()

        from config.config_loader import get_ufo_config, clear_config_cache

        clear_config_cache()
        config_obj = get_ufo_config()
        validator.validate_fields(config_obj._raw)

        # Should have warnings about placeholders
        self.assertGreater(len(validator.warnings), 0)
        self.assertTrue(any("Placeholder" in warning for warning in validator.warnings))

    def test_azure_ad_validation(self):
        """Test Azure AD specific validation."""
        from ufo.tools.validate_config import ConfigValidator

        # Create config with Azure AD but missing required fields
        config = {
            "HOST_AGENT": {
                "API_TYPE": "azure_ad",
                "API_KEY": "key",
                "API_MODEL": "gpt-4o",
                # Missing AAD_TENANT_ID, AAD_API_SCOPE, AAD_API_SCOPE_BASE
            },
            "APP_AGENT": {
                "API_TYPE": "openai",
                "API_KEY": "sk-key",
                "API_MODEL": "gpt-4o",
            },
        }
        self.create_config_file("config/ufo/agents.yaml", config)

        validator = ConfigValidator("ufo")
        validator.validate_structure()

        from config.config_loader import get_ufo_config, clear_config_cache

        clear_config_cache()
        config_obj = get_ufo_config()
        validator.validate_api_config(config_obj._raw)

        # Should have errors about missing Azure AD fields
        self.assertGreater(len(validator.errors), 0)
        self.assertTrue(any("AAD_" in error for error in validator.errors))

    def test_aoai_deployment_id_warning(self):
        """Test warning for missing AOAI deployment ID."""
        from ufo.tools.validate_config import ConfigValidator

        # Create config with AOAI but no deployment ID
        config = {
            "HOST_AGENT": {
                "API_TYPE": "aoai",
                "API_KEY": "key",
                "API_MODEL": "gpt-4o",
                # Missing API_DEPLOYMENT_ID
            },
            "APP_AGENT": {
                "API_TYPE": "openai",
                "API_KEY": "sk-key",
                "API_MODEL": "gpt-4o",
            },
        }
        self.create_config_file("config/ufo/agents.yaml", config)

        validator = ConfigValidator("ufo")
        validator.validate_structure()

        from config.config_loader import get_ufo_config, clear_config_cache

        clear_config_cache()
        config_obj = get_ufo_config()
        validator.validate_api_config(config_obj._raw)

        # Should have warning about deployment ID
        self.assertGreater(len(validator.warnings), 0)

    def test_path_detection_new_only(self):
        """Test path detection when only new config exists."""
        from ufo.tools.validate_config import ConfigValidator

        # Create only new config
        config = {
            "HOST_AGENT": {"API_TYPE": "openai"},
            "APP_AGENT": {"API_TYPE": "openai"},
        }
        self.create_config_file("config/ufo/agents.yaml", config)

        validator = ConfigValidator("ufo")
        new_exists, legacy_exists = validator.check_paths()

        self.assertTrue(new_exists)
        self.assertFalse(legacy_exists)
        self.assertEqual(len(validator.warnings), 0)  # No warnings for new path

    def test_path_detection_legacy_only(self):
        """Test path detection when only legacy config exists."""
        from ufo.tools.validate_config import ConfigValidator

        # Create only legacy config
        config = {
            "HOST_AGENT": {"API_TYPE": "openai"},
            "APP_AGENT": {"API_TYPE": "openai"},
        }
        self.create_config_file("ufo/config/config.yaml", config)

        validator = ConfigValidator("ufo")
        new_exists, legacy_exists = validator.check_paths()

        self.assertFalse(new_exists)
        self.assertTrue(legacy_exists)

        # Validate structure should add warning
        validator.validate_structure()
        self.assertGreater(len(validator.warnings), 0)

    def test_path_detection_both(self):
        """Test path detection when both configs exist."""
        from ufo.tools.validate_config import ConfigValidator

        # Create both configs
        config = {
            "HOST_AGENT": {"API_TYPE": "openai"},
            "APP_AGENT": {"API_TYPE": "openai"},
        }
        self.create_config_file("config/ufo/agents.yaml", config)
        self.create_config_file("ufo/config/config.yaml", config)

        validator = ConfigValidator("ufo")
        new_exists, legacy_exists = validator.check_paths()

        self.assertTrue(new_exists)
        self.assertTrue(legacy_exists)

        # Validate structure should add warning about conflict
        validator.validate_structure()
        self.assertGreater(len(validator.warnings), 0)
        self.assertTrue(any("both" in w.lower() for w in validator.warnings))

    def test_no_config_error(self):
        """Test error when no configuration exists."""
        from ufo.tools.validate_config import ConfigValidator

        validator = ConfigValidator("ufo")
        result = validator.validate_structure()

        self.assertFalse(result)
        self.assertGreater(len(validator.errors), 0)
        self.assertTrue(
            any("No configuration found" in error for error in validator.errors)
        )


class TestGalaxyValidator(unittest.TestCase):
    """Test Galaxy configuration validation."""

    def setUp(self):
        """Set up test environment."""
        self.test_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.test_dir)

        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)
        self.addCleanup(os.chdir, self.original_cwd)

        import sys

        sys.path.insert(0, self.original_cwd)

    def create_config_file(self, path: str, content: dict):
        """Helper to create a config file."""
        file_path = Path(self.test_dir) / path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "w") as f:
            yaml.dump(content, f)
        return file_path

    def test_valid_galaxy_config(self):
        """Test validation of valid Galaxy configuration."""
        from ufo.tools.validate_config import ConfigValidator

        # Create valid config
        config = {
            "CONSTELLATION_AGENT": {
                "API_TYPE": "azure_ad",
                "API_KEY": "key",
                "API_MODEL": "gpt-4o",
                "AAD_TENANT_ID": "tenant",
                "AAD_API_SCOPE": "scope",
                "AAD_API_SCOPE_BASE": "base",
            }
        }
        self.create_config_file("config/galaxy/agent.yaml", config)

        validator = ConfigValidator("galaxy")
        result = validator.validate_structure()

        self.assertTrue(result)

    def test_galaxy_no_legacy_path(self):
        """Test that Galaxy validator doesn't check legacy path."""
        from ufo.tools.validate_config import ConfigValidator

        validator = ConfigValidator("galaxy")

        # Galaxy should not have legacy path
        self.assertIsNone(validator.legacy_path)


if __name__ == "__main__":
    unittest.main()
