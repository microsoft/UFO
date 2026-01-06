"""
Test config migration for ufo/prompter, ufo/automator, ufo/experience, ufo/rag directories.
Verifies that migrated config values match old config values and tests for AttributeError.
"""

import sys
import os
import pytest

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from config.config_loader import get_ufo_config
from ufo.config import Config


class TestMiscConfigMigration:
    """Test migration of misc config fields to new config system."""

    @classmethod
    def setup_class(cls):
        """Setup test fixtures."""
        cls.old_config = Config.get_instance().config_data
        cls.new_config = get_ufo_config()

    def test_prompter_enabled_third_party_agents(self):
        """Test enabled_third_party_agents migration (agent_prompter.py)."""
        old_value = self.old_config.get("ENABLED_THIRD_PARTY_AGENTS", [])
        new_value = self.new_config.system.enabled_third_party_agents
        assert (
            new_value == old_value
        ), f"enabled_third_party_agents mismatch: {new_value} != {old_value}"

    def test_prompter_third_party_agent_config(self):
        """Test third_party_agent_config migration (agent_prompter.py)."""
        old_value = self.old_config.get("THIRD_PARTY_AGENT_CONFIG", {})
        new_value = self.new_config.system.third_party_agent_config
        assert (
            new_value == old_value
        ), f"third_party_agent_config mismatch: {new_value} != {old_value}"

    def test_prompter_action_sequence(self):
        """Test action_sequence migration (agent_prompter.py)."""
        old_value = self.old_config.get("ACTION_SEQUENCE", False)
        new_value = self.new_config.system.action_sequence
        assert (
            new_value == old_value
        ), f"action_sequence mismatch: {new_value} != {old_value}"

    def test_prompter_eva_all_screenshots(self):
        """Test eva_all_screenshots migration (eva_prompter.py)."""
        old_value = self.old_config.get("EVA_ALL_SCREENSHOTS", False)
        new_value = self.new_config.system.eva_all_screenshots
        assert (
            new_value == old_value
        ), f"eva_all_screenshots mismatch: {new_value} != {old_value}"

    def test_prompter_evaluation_prompt(self):
        """Test evaluation_prompt migration (eva_prompter.py)."""
        old_value = self.old_config.get("EVALUATION_PROMPT", "")
        new_value = self.new_config.system.evaluation_prompt
        assert (
            new_value == old_value
        ), f"evaluation_prompt mismatch: {new_value} != {old_value}"

    def test_automator_after_click_wait(self):
        """Test after_click_wait migration (controller.py)."""
        old_value = self.old_config.get("AFTER_CLICK_WAIT", None)
        new_value = self.new_config.system.after_click_wait
        assert (
            new_value == old_value
        ), f"after_click_wait mismatch: {new_value} != {old_value}"

    def test_automator_click_api(self):
        """Test click_api migration (controller.py)."""
        old_value = self.old_config.get("CLICK_API", "click_input")
        new_value = self.new_config.system.click_api
        assert new_value == old_value, f"click_api mismatch: {new_value} != {old_value}"

    def test_automator_input_text_inter_key_pause(self):
        """Test input_text_inter_key_pause migration (controller.py)."""
        old_value = self.old_config.get("INPUT_TEXT_INTER_KEY_PAUSE", 0.1)
        new_value = self.new_config.system.input_text_inter_key_pause
        assert (
            new_value == old_value
        ), f"input_text_inter_key_pause mismatch: {new_value} != {old_value}"

    def test_automator_input_text_api(self):
        """Test input_text_api migration (controller.py)."""
        old_value = self.old_config.get("INPUT_TEXT_API", "type_keys")
        new_value = self.new_config.system.input_text_api
        assert (
            new_value == old_value
        ), f"input_text_api mismatch: {new_value} != {old_value}"

    def test_automator_input_text_enter(self):
        """Test input_text_enter migration (controller.py)."""
        old_value = self.old_config.get("INPUT_TEXT_ENTER", False)
        new_value = self.new_config.system.input_text_enter
        assert (
            new_value == old_value
        ), f"input_text_enter mismatch: {new_value} != {old_value}"

    def test_automator_default_png_compress_level(self):
        """Test default_png_compress_level migration (screenshot.py)."""
        old_value = int(self.old_config.get("DEFAULT_PNG_COMPRESS_LEVEL", 0))
        new_value = self.new_config.system.default_png_compress_level
        assert (
            new_value == old_value
        ), f"default_png_compress_level mismatch: {new_value} != {old_value}"

    def test_automator_annotation_colors(self):
        """Test annotation_colors migration (screenshot.py)."""
        old_value = self.old_config.get("ANNOTATION_COLORS", {})
        new_value = self.new_config.system.annotation_colors
        assert (
            new_value == old_value
        ), f"annotation_colors mismatch: {new_value} != {old_value}"

    def test_automator_annotation_font_size(self):
        """Test annotation_font_size migration (screenshot.py)."""
        old_value = self.old_config.get("ANNOTATION_FONT_SIZE", 25)
        new_value = self.new_config.system.annotation_font_size
        assert (
            new_value == old_value
        ), f"annotation_font_size mismatch: {new_value} != {old_value}"

    def test_experience_visual_mode(self):
        """Test APP_AGENT.VISUAL_MODE migration (summarizer.py)."""
        old_value = self.old_config.get("APP_AGENT", {}).get("VISUAL_MODE", False)
        new_value = self.new_config.app_agent.visual_mode
        assert (
            new_value == old_value
        ), f"app_agent.visual_mode mismatch: {new_value} != {old_value}"

    def test_experience_prompt(self):
        """Test experience_prompt migration (summarizer.py)."""
        old_value = self.old_config.get("EXPERIENCE_PROMPT", "")
        new_value = self.new_config.system.experience_prompt
        assert (
            new_value == old_value
        ), f"experience_prompt mismatch: {new_value} != {old_value}"

    def test_experience_appagent_example_prompt(self):
        """Test appagent_example_prompt migration (summarizer.py)."""
        old_value = self.old_config.get("APPAGENT_EXAMPLE_PROMPT", "")
        new_value = self.new_config.system.appagent_example_prompt
        assert (
            new_value == old_value
        ), f"appagent_example_prompt mismatch: {new_value} != {old_value}"

    def test_experience_api_prompt(self):
        """Test api_prompt migration (summarizer.py)."""
        old_value = self.old_config.get("API_PROMPT", "")
        new_value = self.new_config.system.api_prompt
        assert (
            new_value == old_value
        ), f"api_prompt mismatch: {new_value} != {old_value}"

    def test_rag_bing_api_key(self):
        """Test bing_api_key migration (web_search.py)."""
        old_value = self.old_config.get("BING_API_KEY", "")
        new_value = self.new_config.rag.bing_api_key
        assert (
            new_value == old_value
        ), f"bing_api_key mismatch: {new_value} != {old_value}"

    def test_attribute_error_prevention(self):
        """Test that all migrated attributes are accessible without AttributeError."""
        # Test all system attributes
        system_attrs = [
            "enabled_third_party_agents",
            "third_party_agent_config",
            "action_sequence",
            "eva_all_screenshots",
            "evaluation_prompt",
            "after_click_wait",
            "click_api",
            "input_text_inter_key_pause",
            "input_text_api",
            "input_text_enter",
            "default_png_compress_level",
            "annotation_colors",
            "annotation_font_size",
            "experience_prompt",
            "appagent_example_prompt",
            "api_prompt",
        ]

        for attr in system_attrs:
            try:
                value = getattr(self.new_config.system, attr)
                assert value is not None or hasattr(
                    self.new_config.system, attr
                ), f"Attribute {attr} not accessible"
            except AttributeError as e:
                pytest.fail(f"AttributeError for system.{attr}: {e}")

        # Test app_agent attributes
        try:
            value = getattr(self.new_config.app_agent, "visual_mode")
            assert value is not None or hasattr(
                self.new_config.app_agent, "visual_mode"
            ), "Attribute visual_mode not accessible"
        except AttributeError as e:
            pytest.fail(f"AttributeError for app_agent.visual_mode: {e}")

        # Test rag attributes
        try:
            value = getattr(self.new_config.rag, "bing_api_key")
            assert value is not None or hasattr(
                self.new_config.rag, "bing_api_key"
            ), "Attribute bing_api_key not accessible"
        except AttributeError as e:
            pytest.fail(f"AttributeError for rag.bing_api_key: {e}")

    def test_attribute_access_methods(self):
        """Test various attribute access methods work correctly."""
        # Test dot notation
        assert hasattr(self.new_config.system, "action_sequence")

        # Test getattr with default
        value = getattr(self.new_config.system, "action_sequence", None)
        assert value is not None or value == self.old_config.get(
            "ACTION_SEQUENCE", False
        )

        # Test direct access
        try:
            _ = self.new_config.system.click_api
            _ = self.new_config.app_agent.visual_mode
            _ = self.new_config.rag.bing_api_key
        except AttributeError as e:
            pytest.fail(f"Direct attribute access failed: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
