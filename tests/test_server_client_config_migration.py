"""
Test config migration for ufo/server and ufo/client directories.
Verifies that migrated config values match old config values and tests for AttributeError.
"""

import sys
import os
import pytest

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from config.config_loader import get_ufo_config
from ufo.config import Config


class TestServerClientConfigMigration:
    """Test migration of server and client config fields to new config system."""

    @classmethod
    def setup_class(cls):
        """Setup test fixtures."""
        cls.old_config = Config.get_instance().config_data
        cls.new_config = get_ufo_config()

    def test_server_eva_session(self):
        """Test eva_session migration (session_manager.py)."""
        old_value = self.old_config.get("EVA_SESSION", False)
        new_value = self.new_config.system.eva_session
        assert (
            new_value == old_value
        ), f"eva_session mismatch: {new_value} != {old_value}"

    def test_client_config_dict_compatibility(self):
        """Test that new config can be converted to dict for ComputerManager."""
        # ComputerManager expects a dict with 'mcp' key (uppercase in YAML)
        config_dict = self.new_config.to_dict()

        # Verify dict structure
        assert isinstance(config_dict, dict), "Config should be convertible to dict"

        # The raw config uses uppercase keys from YAML
        # Check if either 'mcp' or 'MCP' exists
        has_mcp_key = "mcp" in config_dict or "MCP" in config_dict
        assert has_mcp_key, "Config dict should contain 'mcp' or 'MCP' key"

        # Verify MCP config matches old config (both use uppercase keys)
        old_mcp = self.old_config.get("mcp", {})
        new_mcp = config_dict.get("mcp", {})

        assert new_mcp == old_mcp, f"MCP config mismatch: {new_mcp} != {old_mcp}"

    def test_attribute_error_prevention(self):
        """Test that all migrated attributes are accessible without AttributeError."""
        # Test system.eva_session attribute
        try:
            value = getattr(self.new_config.system, "eva_session")
            assert value is not None or hasattr(
                self.new_config.system, "eva_session"
            ), "Attribute eva_session not accessible"
        except AttributeError as e:
            pytest.fail(f"AttributeError for system.eva_session: {e}")

    def test_attribute_access_methods(self):
        """Test various attribute access methods work correctly."""
        # Test dot notation
        assert hasattr(self.new_config.system, "eva_session")

        # Test getattr with default
        value = getattr(self.new_config.system, "eva_session", None)
        assert value is not None or value == self.old_config.get("EVA_SESSION", False)

        # Test direct access
        try:
            _ = self.new_config.system.eva_session
        except AttributeError as e:
            pytest.fail(f"Direct attribute access failed: {e}")

    def test_config_to_dict_preserves_all_sections(self):
        """Test that to_dict() preserves all config sections needed by client/server."""
        config_dict = self.new_config.to_dict()

        # The raw config uses uppercase keys from YAML files
        # Check all major uppercase sections exist (as they appear in YAML)
        expected_uppercase_sections = [
            "HOST_AGENT",
            "APP_AGENT",
            "RAG_OFFLINE_DOCS",
            "mcp",
        ]
        for section in expected_uppercase_sections:
            assert (
                section in config_dict
            ), f"Section '{section}' missing from config dict"

        # Verify key sections match old config structure
        assert config_dict.get("mcp") == self.old_config.get(
            "mcp"
        ), "MCP config should match between old and new"

        # Verify all old config keys exist in new config
        for key in self.old_config.keys():
            assert key in config_dict, f"Old config key '{key}' missing in new config"

    def test_eva_session_uppercase_lowercase_mapping(self):
        """Test that EVA_SESSION can be accessed as eva_session (case mapping)."""
        # This tests the __getattr__ mapping from uppercase to lowercase
        try:
            # Should work with lowercase
            lowercase_value = self.new_config.system.eva_session

            # Compare with old uppercase
            old_value = self.old_config.get("EVA_SESSION", False)

            assert (
                lowercase_value == old_value
            ), f"Case mapping failed: {lowercase_value} != {old_value}"
        except AttributeError as e:
            pytest.fail(f"Case mapping for eva_session failed: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
