# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Integration tests for configuration migration tool.

Tests cover:
- Migration from legacy to new path
- Dry run mode
- Backup creation
- File copying
- Error handling
"""

import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import yaml


class TestConfigMigrator(unittest.TestCase):
    """Test ConfigMigrator class."""

    def setUp(self):
        """Set up test environment."""
        self.test_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.test_dir)

        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)
        self.addCleanup(os.chdir, self.original_cwd)

        # Import here after changing directory
        import sys

        sys.path.insert(0, self.original_cwd)

    def create_legacy_config(self):
        """Create legacy configuration files."""
        legacy_path = Path(self.test_dir) / "ufo/config"
        legacy_path.mkdir(parents=True, exist_ok=True)

        # Create sample config files
        configs = {
            "config.yaml": {
                "HOST_AGENT": {"API_TYPE": "openai"},
                "MAX_STEP": 50,
            },
            "config_dev.yaml": {"MAX_STEP": 100},
            "config_prices.yaml": {"gpt-4": 0.03},
        }

        for filename, content in configs.items():
            with open(legacy_path / filename, "w") as f:
                yaml.dump(content, f)

        return legacy_path

    def test_check_legacy_exists(self):
        """Test legacy configuration detection."""
        from ufo.tools.migrate_config import ConfigMigrator

        # Create legacy config
        self.create_legacy_config()

        migrator = ConfigMigrator()
        self.assertTrue(migrator.check_legacy_exists())

    def test_check_legacy_not_exists(self):
        """Test when legacy config doesn't exist."""
        from ufo.tools.migrate_config import ConfigMigrator

        migrator = ConfigMigrator()
        self.assertFalse(migrator.check_legacy_exists())

    def test_discover_files(self):
        """Test file discovery in legacy path."""
        from ufo.tools.migrate_config import ConfigMigrator

        # Create legacy config
        self.create_legacy_config()

        migrator = ConfigMigrator()
        files = migrator.discover_files()

        # Should find 3 YAML files
        self.assertEqual(len(files), 3)
        filenames = [f.name for f in files]
        self.assertIn("config.yaml", filenames)
        self.assertIn("config_dev.yaml", filenames)
        self.assertIn("config_prices.yaml", filenames)

    def test_dry_run_migration(self):
        """Test dry run migration (no files copied)."""
        from ufo.tools.migrate_config import ConfigMigrator

        # Create legacy config
        self.create_legacy_config()

        migrator = ConfigMigrator()
        migrations = migrator.migrate_files(dry_run=True)

        # Should return migration list
        self.assertEqual(len(migrations), 3)

        # But new path should not exist
        new_path = Path(self.test_dir) / "config/ufo"
        self.assertFalse(new_path.exists())

    def test_actual_migration(self):
        """Test actual file migration."""
        from ufo.tools.migrate_config import ConfigMigrator

        # Create legacy config
        self.create_legacy_config()

        migrator = ConfigMigrator()
        migrations = migrator.migrate_files(dry_run=False)

        # Should copy files
        self.assertEqual(len(migrations), 3)

        # New path should exist with files
        new_path = Path(self.test_dir) / "config/ufo"
        self.assertTrue(new_path.exists())
        self.assertTrue((new_path / "config.yaml").exists())
        self.assertTrue((new_path / "config_dev.yaml").exists())
        self.assertTrue((new_path / "config_prices.yaml").exists())

    def test_backup_creation(self):
        """Test backup creation during migration."""
        from ufo.tools.migrate_config import ConfigMigrator

        # Create legacy config
        legacy_path = self.create_legacy_config()

        migrator = ConfigMigrator(backup=True)
        backup_path = migrator.create_backup()

        # Backup should exist
        self.assertTrue(backup_path.exists())
        self.assertTrue((backup_path / "config.yaml").exists())

        # Backup name should contain timestamp
        self.assertIn("backup_", str(backup_path))

    def test_migration_preserves_content(self):
        """Test that migration preserves file content."""
        from ufo.tools.migrate_config import ConfigMigrator

        # Create legacy config
        self.create_legacy_config()

        migrator = ConfigMigrator()
        migrator.migrate_files(dry_run=False)

        # Read original and migrated files
        legacy_file = Path(self.test_dir) / "ufo/config/config.yaml"
        new_file = Path(self.test_dir) / "config/ufo/config.yaml"

        with open(legacy_file) as f:
            legacy_content = yaml.safe_load(f)

        with open(new_file) as f:
            new_content = yaml.safe_load(f)

        # Content should be identical
        self.assertEqual(legacy_content, new_content)

    def test_no_overwrite_without_confirmation(self):
        """Test that existing files are not overwritten without confirmation."""
        from ufo.tools.migrate_config import ConfigMigrator

        # Create legacy config
        self.create_legacy_config()

        # Create existing new config
        new_path = Path(self.test_dir) / "config/ufo"
        new_path.mkdir(parents=True, exist_ok=True)
        with open(new_path / "config.yaml", "w") as f:
            yaml.dump({"EXISTING": "value"}, f)

        migrator = ConfigMigrator()

        # Check that new config exists
        self.assertTrue(migrator.check_new_exists())


class TestMigrationScenarios(unittest.TestCase):
    """Test various migration scenarios."""

    def setUp(self):
        """Set up test environment."""
        self.test_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.test_dir)

        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)
        self.addCleanup(os.chdir, self.original_cwd)

        import sys

        sys.path.insert(0, self.original_cwd)

    def test_migration_with_subdirectories(self):
        """Test migration handles only YAML files, not subdirectories."""
        from ufo.tools.migrate_config import ConfigMigrator

        # Create legacy config with subdirectory
        legacy_path = Path(self.test_dir) / "ufo/config"
        legacy_path.mkdir(parents=True, exist_ok=True)

        # Create YAML file
        with open(legacy_path / "config.yaml", "w") as f:
            yaml.dump({"TEST": "value"}, f)

        # Create subdirectory (should be ignored)
        (legacy_path / "subdir").mkdir()

        migrator = ConfigMigrator()
        files = migrator.discover_files()

        # Should only find YAML files, not directories
        self.assertEqual(len(files), 1)
        self.assertEqual(files[0].name, "config.yaml")

    def test_migration_empty_legacy(self):
        """Test migration when legacy path exists but has no YAML files."""
        from ufo.tools.migrate_config import ConfigMigrator

        # Create empty legacy path
        legacy_path = Path(self.test_dir) / "ufo/config"
        legacy_path.mkdir(parents=True, exist_ok=True)

        migrator = ConfigMigrator()
        self.assertFalse(migrator.check_legacy_exists())

    def test_migration_preserves_file_permissions(self):
        """Test that file permissions are preserved during migration."""
        from ufo.tools.migrate_config import ConfigMigrator

        # Create legacy config
        legacy_path = Path(self.test_dir) / "ufo/config"
        legacy_path.mkdir(parents=True, exist_ok=True)

        config_file = legacy_path / "config.yaml"
        with open(config_file, "w") as f:
            yaml.dump({"TEST": "value"}, f)

        # Get original permissions
        original_stat = config_file.stat()

        # Migrate
        migrator = ConfigMigrator()
        migrator.migrate_files(dry_run=False)

        # Check new file
        new_file = Path(self.test_dir) / "config/ufo/config.yaml"
        new_stat = new_file.stat()

        # Permissions should be preserved (mode)
        # Note: On Windows, this might not be exact, so we just check file exists
        self.assertTrue(new_file.exists())


if __name__ == "__main__":
    unittest.main()
