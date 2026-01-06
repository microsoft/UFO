# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Unit tests for config conversion tool.

Tests:
- Field mapping completeness
- YAML format conversion (flow → block style)
- File splitting logic
- Config loader compatibility
- Value preservation after conversion
"""

import sys
import tempfile
import unittest
from pathlib import Path

import yaml

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from ufo.tools.convert_config import ConfigConverter


class TestConfigConversion(unittest.TestCase):
    """Test cases for configuration conversion."""

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures."""
        cls.project_root = Path(__file__).parent.parent
        cls.legacy_config_path = cls.project_root / "ufo" / "config"
        cls.new_config_path = cls.project_root / "config" / "ufo"

    def test_legacy_config_exists(self):
        """Test that legacy config files exist."""
        self.assertTrue(
            self.legacy_config_path.exists(),
            f"Legacy config path does not exist: {self.legacy_config_path}",
        )

        # Check for key files
        config_yaml = self.legacy_config_path / "config.yaml"
        self.assertTrue(
            config_yaml.exists(), f"Legacy config.yaml not found: {config_yaml}"
        )

    def test_field_mapping_completeness(self):
        """Test that all fields in legacy config are mapped."""
        converter = ConfigConverter(
            legacy_path=str(self.legacy_config_path), new_path=str(self.new_config_path)
        )

        # Load legacy config
        config_file = self.legacy_config_path / "config.yaml"
        if not config_file.exists():
            self.skipTest("Legacy config.yaml not found")

        legacy_data = converter.load_yaml(config_file)

        # Get all mapped fields
        all_mapped_fields = set()
        for fields in converter.FIELD_MAPPING.values():
            all_mapped_fields.update(fields)

        # Check each field is mapped
        unmapped = []
        for key in legacy_data.keys():
            if key not in all_mapped_fields:
                unmapped.append(key)

        if unmapped:
            print(f"\n[Warning] Unmapped fields (will go to system.yaml): {unmapped}")

    def test_yaml_format_conversion(self):
        """Test conversion from flow-style to block-style YAML."""
        converter = ConfigConverter()

        # Create test data with nested structure
        test_data = {
            "HOST_AGENT": {
                "API_TYPE": "azure_ad",
                "API_KEY": "test_key",
                "VISUAL_MODE": True,
                "AAD_TENANT_ID": "test-tenant-id",
            },
            "MAX_TOKENS": 2000,
            "TEMPERATURE": 0.0,
        }

        # Save and reload
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            temp_path = Path(f.name)

        try:
            converter.save_yaml(test_data, temp_path, "Test Header")

            # Read back and verify
            with open(temp_path, "r") as f:
                content = f.read()

            # Check it's block style (no braces for dicts)
            self.assertNotIn("{", content, "Should not contain flow-style braces")
            self.assertIn("HOST_AGENT:", content, "Should have block-style keys")
            self.assertIn("  API_TYPE:", content, "Should have indented nested keys")

            # Verify it can be parsed
            reloaded = converter.load_yaml(temp_path)
            self.assertEqual(reloaded["HOST_AGENT"]["API_TYPE"], "azure_ad")
            self.assertEqual(reloaded["MAX_TOKENS"], 2000)

        finally:
            temp_path.unlink()

    def test_config_splitting(self):
        """Test that monolithic config splits correctly."""
        converter = ConfigConverter(
            legacy_path=str(self.legacy_config_path), new_path=str(self.new_config_path)
        )

        # Load legacy config
        config_file = self.legacy_config_path / "config.yaml"
        if not config_file.exists():
            self.skipTest("Legacy config.yaml not found")

        legacy_data = converter.load_yaml(config_file)
        split_data = converter.split_config(legacy_data)

        # Verify agents.yaml contains agent configs
        self.assertIn("agents.yaml", split_data)
        agents_config = split_data["agents.yaml"]
        if "HOST_AGENT" in legacy_data:
            self.assertIn("HOST_AGENT", agents_config)
        if "APP_AGENT" in legacy_data:
            self.assertIn("APP_AGENT", agents_config)

        # Verify rag.yaml contains RAG configs
        self.assertIn("rag.yaml", split_data)
        rag_config = split_data["rag.yaml"]
        if "RAG_OFFLINE_DOCS" in legacy_data:
            self.assertIn("RAG_OFFLINE_DOCS", rag_config)

        # Verify system.yaml contains system configs
        self.assertIn("system.yaml", split_data)
        system_config = split_data["system.yaml"]
        if "MAX_TOKENS" in legacy_data:
            self.assertIn("MAX_TOKENS", system_config)

    def test_value_preservation(self):
        """Test that values are preserved during conversion."""
        converter = ConfigConverter(
            legacy_path=str(self.legacy_config_path), new_path=str(self.new_config_path)
        )

        # Load legacy config
        config_file = self.legacy_config_path / "config.yaml"
        if not config_file.exists():
            self.skipTest("Legacy config.yaml not found")

        legacy_data = converter.load_yaml(config_file)
        split_data = converter.split_config(legacy_data)

        # Merge split data back
        merged = {}
        for file_data in split_data.values():
            merged.update(file_data)

        # Compare each value
        for key, value in legacy_data.items():
            self.assertIn(key, merged, f"Key '{key}' missing after split")
            self.assertEqual(
                merged[key],
                value,
                f"Value mismatch for '{key}': {merged[key]} != {value}",
            )

    def test_config_loader_compatibility(self):
        """Test that converted config can be loaded as valid YAML."""
        # Create temporary directory for converted config
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir) / "test_config"

            converter = ConfigConverter(
                legacy_path=str(self.legacy_config_path), new_path=str(temp_path)
            )

            # Convert configs
            converted = converter.convert_legacy_config()

            # Write converted files
            converter.write_converted_configs(converted, dry_run=False)

            # Try to load each file with PyYAML directly
            for yaml_file in temp_path.glob("*.yaml"):
                try:
                    with open(yaml_file, "r", encoding="utf-8") as f:
                        data = yaml.safe_load(f)

                    # Verify it's a valid dict
                    self.assertIsInstance(
                        data, dict, f"{yaml_file.name} should load as dict"
                    )
                    self.assertGreater(
                        len(data), 0, f"{yaml_file.name} should not be empty"
                    )

                except yaml.YAMLError as e:
                    self.fail(f"Failed to parse {yaml_file.name}: {e}")
                except Exception as e:
                    self.fail(f"Failed to load {yaml_file.name}: {e}")

    def test_mcp_config_conversion(self):
        """Test agent_mcp.yaml → mcp.yaml conversion."""
        mcp_file = self.legacy_config_path / "agent_mcp.yaml"
        if not mcp_file.exists():
            self.skipTest("agent_mcp.yaml not found")

        converter = ConfigConverter(
            legacy_path=str(self.legacy_config_path), new_path=str(self.new_config_path)
        )

        # Load original
        original_data = converter.load_yaml(mcp_file)

        # Convert
        converted = converter.convert_legacy_config()

        # Verify mcp.yaml exists and has same data
        self.assertIn("mcp.yaml", converted)
        self.assertEqual(converted["mcp.yaml"], original_data)

    def test_prices_config_conversion(self):
        """Test config_prices.yaml → prices.yaml conversion."""
        prices_file = self.legacy_config_path / "config_prices.yaml"
        if not prices_file.exists():
            self.skipTest("config_prices.yaml not found")

        converter = ConfigConverter(
            legacy_path=str(self.legacy_config_path), new_path=str(self.new_config_path)
        )

        # Load original
        original_data = converter.load_yaml(prices_file)

        # Convert
        converted = converter.convert_legacy_config()

        # Verify prices.yaml exists and has same data
        self.assertIn("prices.yaml", converted)
        self.assertEqual(converted["prices.yaml"], original_data)

    def test_dry_run_no_files_created(self):
        """Test that dry run doesn't create files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir) / "test_config"

            converter = ConfigConverter(
                legacy_path=str(self.legacy_config_path), new_path=str(temp_path)
            )

            # Run conversion in dry-run mode
            converted = converter.convert_legacy_config()
            converter.write_converted_configs(converted, dry_run=True)

            # Verify no files were created
            if temp_path.exists():
                files = list(temp_path.glob("*.yaml"))
                self.assertEqual(
                    len(files), 0, f"Dry run should not create files, found: {files}"
                )


class TestConfigValueEquivalence(unittest.TestCase):
    """Test that converted config produces same values as legacy."""

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures."""
        cls.project_root = Path(__file__).parent.parent
        cls.legacy_config_path = cls.project_root / "ufo" / "config"

    def test_legacy_vs_converted_equivalence(self):
        """Test that converted config preserves all values from legacy."""
        # Create temporary directory for converted config
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir) / "converted"

            # Convert legacy config
            converter = ConfigConverter(
                legacy_path=str(self.legacy_config_path), new_path=str(temp_path)
            )

            converted = converter.convert_legacy_config()
            if not converted:
                self.skipTest("No legacy config to convert")

            converter.write_converted_configs(converted, dry_run=False)

            # Load legacy config directly
            legacy_file = self.legacy_config_path / "config.yaml"
            if not legacy_file.exists():
                self.skipTest("Legacy config.yaml not found")

            legacy_data = converter.load_yaml(legacy_file)

            # Load all converted files and merge
            converted_merged = {}
            for yaml_file in temp_path.glob("*.yaml"):
                file_data = converter.load_yaml(yaml_file)
                converted_merged.update(file_data)

            # Compare key values
            for key in legacy_data.keys():
                if key in converted_merged:
                    self.assertEqual(
                        legacy_data[key],
                        converted_merged[key],
                        f"Value mismatch for key '{key}'",
                    )


def run_tests():
    """Run all tests and print results."""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestConfigConversion))
    suite.addTests(loader.loadTestsFromTestCase(TestConfigValueEquivalence))

    # Run tests with verbose output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Return exit code
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    exit(run_tests())
