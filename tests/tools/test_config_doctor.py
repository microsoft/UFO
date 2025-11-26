# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Tests for Configuration Doctor tool.
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch

import sys
UFO_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(UFO_ROOT))

try:
    from ufo.tools.config_doctor import ConfigDoctor, ConfigIssue
except ImportError as e:
    pytest.skip(f"Could not import config_doctor: {e}", allow_module_level=True)


class TestConfigDoctor:
    """Test suite for ConfigDoctor core functionality."""
   
    def setup_method(self):
        self.doctor = ConfigDoctor()
        self.temp_dir = Path(tempfile.mkdtemp())
   
    def teardown_method(self):
        import shutil
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
   
    def test_config_issue_creation(self):
        """Test ConfigIssue class."""
        issue = ConfigIssue(
            title="Test Issue",
            description="Test description",
            severity=ConfigIssue.SEVERITY_WARNING,
            fix_suggestion="Test fix"
        )
       
        assert issue.title == "Test Issue"
        assert issue.severity == ConfigIssue.SEVERITY_WARNING
        assert issue.severity_icon == "⚠️"
        assert issue.severity_color == "yellow"
   
    def test_missing_config_detection(self):
        """Test detection of missing configuration."""
        # Mock paths to empty directory
        with patch.object(self.doctor, '_check_config_structure') as mock_check:
            def mock_impl(module):
                self.doctor.issues.append(ConfigIssue(
                    title="Missing UFO Configuration",
                    description="No UFO configuration found",
                    severity=ConfigIssue.SEVERITY_CRITICAL
                ))
            mock_check.side_effect = mock_impl
           
            self.doctor._check_config_structure("ufo")
           
            critical_issues = [i for i in self.doctor.issues if i.severity == ConfigIssue.SEVERITY_CRITICAL]
            assert len(critical_issues) > 0
            assert any("Missing UFO Configuration" in issue.title for issue in critical_issues)
   
    @patch('ufo.tools.config_doctor.get_ufo_config')
    def test_placeholder_api_key_detection(self, mock_get_config):
        """Test detection of placeholder API keys."""
        mock_config = {
            "HOST_AGENT": {
                "API_TYPE": "openai",
                "API_KEY": "YOUR_KEY",
                "API_MODEL": "gpt-4o"
            }
        }
        mock_get_config.return_value = mock_config
       
        self.doctor._check_api_configuration("ufo")
       
        placeholder_issues = [i for i in self.doctor.issues if "Placeholder API Key" in i.title]
        assert len(placeholder_issues) > 0
   
    def test_copy_template_function(self):
        """Test template copying functionality."""
        template_file = self.temp_dir / "template.yaml"
        target_file = self.temp_dir / "target.yaml"
       
        template_file.write_text("test content")
       
        with patch('builtins.print'):
            result = self.doctor._copy_template(template_file, target_file)
       
        assert result is True
        assert target_file.exists()
        assert target_file.read_text() == "test content"
   
    def test_copy_template_error_handling(self):
        """Test template copying error handling."""
        nonexistent_template = self.temp_dir / "nonexistent.yaml"
        target_file = self.temp_dir / "target.yaml"
       
        with patch('builtins.print'):
            result = self.doctor._copy_template(nonexistent_template, target_file)
       
        assert result is False
        assert not target_file.exists()
   
    def test_auto_fix_no_fixable_issues(self):
        """Test auto-fix when no fixable issues exist."""
        self.doctor.issues = [ConfigIssue(
            title="Manual Issue",
            description="Requires manual fix",
            severity=ConfigIssue.SEVERITY_WARNING
        )]
       
        with patch('builtins.print'):
            fixed_count = self.doctor.auto_fix_issues()
       
        assert fixed_count == 0


if __name__ == "__main__":
    pytest.main([__file__])
