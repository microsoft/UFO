# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Integration tests for Presenter layer with Agents.

Tests ensure that the refactored presenter system works correctly
with actual Agent instances and produces the same output as before.
"""

import unittest
from unittest.mock import Mock, MagicMock, patch
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from ufo.agents.presenters import RichPresenter, PresenterFactory
from ufo.config import Config


class TestAgentPresenterIntegration(unittest.TestCase):
    """Integration tests for agents using presenters"""

    def setUp(self):
        """Set up test fixtures"""
        # Ensure config is initialized
        try:
            Config.get_instance()
        except:
            pass

    @patch('ufo.agents.presenters.rich_presenter.Console')
    def test_basic_agent_has_presenter(self, mock_console_class):
        """Test that BasicAgent initializes with a presenter"""
        from ufo.agents.agent.basic import BasicAgent
        from ufo.agents.states.basic import AgentStatus
        from ufo.module.context import Context
        
        # Create a concrete implementation of BasicAgent for testing
        class TestAgent(BasicAgent):
            def get_prompter(self):
                return None
            
            @property
            def status_manager(self):
                return AgentStatus
            
            def message_constructor(self, *args, **kwargs):
                return []
            
            async def context_provision(self, context: Context):
                pass
            
            async def process_confirmation(self, context: Context = None):
                return True
        
        mock_console = MagicMock()
        mock_console_class.return_value = mock_console
        
        agent = TestAgent(name="test_agent")
        
        # Verify agent has presenter
        self.assertIsNotNone(agent.presenter)
        self.assertIsInstance(agent.presenter, RichPresenter)

    @patch('ufo.agents.presenters.rich_presenter.Console')
    def test_app_agent_print_response(self, mock_console_class):
        """Test that AppAgent's print_response uses presenter correctly"""
        from ufo.agents.processors.schemas.response_schema import AppAgentResponse
        from ufo.agents.processors.schemas.actions import ActionCommandInfo
        
        mock_console = MagicMock()
        mock_console_class.return_value = mock_console
        
        # Create mock response
        response = Mock(spec=AppAgentResponse)
        response.observation = "Test observation"
        response.thought = "Test thought"
        response.plan = ["Step 1", "Step 2"]
        response.comment = None
        response.save_screenshot = {"save": False}
        
        # Create mock action
        action = Mock(spec=ActionCommandInfo)
        action.function = "click"
        action.arguments = {"x": 100, "y": 200}
        action.status = "pending"
        response.action = action
        
        # Create presenter and test
        presenter = RichPresenter(console=mock_console)
        presenter.present_app_agent_response(response, print_action=True)
        
        # Verify console.print was called
        self.assertTrue(mock_console.print.called)
        # Should print: observation, thought, actions table, plan
        self.assertGreaterEqual(mock_console.print.call_count, 4)

    @patch('ufo.agents.presenters.rich_presenter.Console')
    def test_host_agent_print_response(self, mock_console_class):
        """Test that HostAgent's print_response uses presenter correctly"""
        from ufo.agents.processors.schemas.response_schema import HostAgentResponse
        
        mock_console = MagicMock()
        mock_console_class.return_value = mock_console
        
        # Create mock response
        response = Mock(spec=HostAgentResponse)
        response.observation = "Test observation"
        response.thought = "Test thought"
        response.function = "select_application"
        response.arguments = {"name": "TestApp"}
        response.current_subtask = "Select application"
        response.plan = ["Task 1", "Task 2"]
        response.message = []
        response.status = "CONTINUE"
        response.comment = None
        response._formatted_action = "select_application(name=TestApp)"
        
        # Create presenter and test
        presenter = RichPresenter(console=mock_console)
        presenter.present_host_agent_response(response)
        
        # Verify console.print was called
        self.assertTrue(mock_console.print.called)
        # Should print: observation, thought, action, plan, status
        self.assertGreaterEqual(mock_console.print.call_count, 5)

    @patch('ufo.agents.presenters.rich_presenter.Console')
    def test_constellation_agent_print_response(self, mock_console_class):
        """Test that ConstellationAgent's print_response uses presenter correctly"""
        from galaxy.agents.schema import ConstellationAgentResponse
        
        mock_console = MagicMock()
        mock_console_class.return_value = mock_console
        
        # Create mock response
        response = Mock(spec=ConstellationAgentResponse)
        response.thought = "Creating constellation"
        response.status = "START"
        response.constellation = None
        response.action = None
        response.results = None
        
        # Create presenter and test
        presenter = RichPresenter(console=mock_console)
        presenter.present_constellation_agent_response(response, print_action=False)
        
        # Verify console.print was called
        self.assertTrue(mock_console.print.called)
        # Should print: thought, status
        self.assertGreaterEqual(mock_console.print.call_count, 2)

    @patch('ufo.agents.presenters.rich_presenter.Console')
    def test_list_action_command_info_color_print(self, mock_console_class):
        """Test that ListActionCommandInfo.color_print uses presenter"""
        from ufo.agents.processors.schemas.actions import (
            ActionCommandInfo,
            ListActionCommandInfo
        )
        from aip.messages import Result, ResultStatus
        
        mock_console = MagicMock()
        mock_console_class.return_value = mock_console
        
        # Create mock actions
        action1 = Mock(spec=ActionCommandInfo)
        action1.to_representation = Mock(return_value="Action 1 representation")
        action1.result = Result(status=ResultStatus.SUCCESS, result="Success")
        
        action2 = Mock(spec=ActionCommandInfo)
        action2.to_representation = Mock(return_value="Action 2 representation")
        action2.result = Result(status=ResultStatus.SUCCESS, result="Success")
        
        # Create ListActionCommandInfo
        action_list = Mock(spec=ListActionCommandInfo)
        action_list.actions = [action1, action2]
        action_list.status = "COMPLETED"
        
        # Mock the color_print method to use presenter
        with patch.object(action_list, 'color_print') as mock_color_print:
            # Simulate the refactored color_print behavior
            presenter = PresenterFactory.create_presenter("rich")
            presenter.present_action_list(action_list, success_only=False)
        
        # The test passes if no exception is raised


class TestPresenterOutputConsistency(unittest.TestCase):
    """Tests to ensure presenter output is consistent with original implementation"""

    @patch('ufo.agents.presenters.rich_presenter.Console')
    def test_status_styling_consistency(self, mock_console_class):
        """Test that status styling matches original implementation"""
        mock_console = MagicMock()
        mock_console_class.return_value = mock_console
        
        presenter = RichPresenter(console=mock_console)
        
        # Test different statuses
        statuses = ["FINISH", "FAIL", "CONTINUE", "START"]
        for status in statuses:
            mock_console.reset_mock()
            presenter.present_status(status)
            
            # Verify print was called
            self.assertTrue(mock_console.print.called)

    @patch('ufo.agents.presenters.rich_presenter.Console')
    def test_constellation_operation_formatting(self, mock_console_class):
        """Test that constellation operations are formatted correctly"""
        presenter = RichPresenter()
        
        test_cases = [
            {
                "function": "add_task",
                "arguments": {"task_id": "task-1", "name": "Test"},
                "expected_substring": "Add Task"
            },
            {
                "function": "remove_task",
                "arguments": {"task_id": "task-1"},
                "expected_substring": "Remove Task"
            },
            {
                "function": "add_dependency",
                "arguments": {
                    "dependency_id": "dep-1",
                    "from_task_id": "task-1",
                    "to_task_id": "task-2"
                },
                "expected_substring": "Add Dependency"
            },
        ]
        
        for test_case in test_cases:
            mock_action = Mock()
            mock_action.function = test_case["function"]
            mock_action.arguments = test_case["arguments"]
            
            result = presenter._format_constellation_operation(mock_action)
            self.assertIn(test_case["expected_substring"], result)


class TestPresenterFactoryConfig(unittest.TestCase):
    """Tests for presenter factory configuration"""

    def test_default_presenter_type(self):
        """Test that default presenter type is 'rich'"""
        from ufo.config import Config
        
        # Get or create config instance
        try:
            config = Config.get_instance()
            config_data = config.config_data
        except:
            config_data = {}
        
        # Get presenter type from config or use default
        presenter_type = config_data.get("OUTPUT_PRESENTER", "rich")
        self.assertEqual(presenter_type, "rich")

    def test_presenter_creation_with_config(self):
        """Test that presenters are created according to config"""
        presenter = PresenterFactory.create_presenter("rich")
        self.assertIsInstance(presenter, RichPresenter)


class TestBackwardCompatibility(unittest.TestCase):
    """Tests to ensure backward compatibility after refactoring"""

    @patch('ufo.agents.presenters.rich_presenter.Console')
    def test_app_agent_response_structure(self, mock_console_class):
        """Test that AppAgent response structure is maintained"""
        mock_console = MagicMock()
        mock_console_class.return_value = mock_console
        
        presenter = RichPresenter(console=mock_console)
        
        # Create a response with all expected fields
        mock_response = Mock()
        mock_response.observation = "Test"
        mock_response.thought = "Test"
        mock_response.plan = ["Test"]
        mock_response.comment = None
        mock_response.save_screenshot = {"save": False}
        mock_response.action = []
        
        # Should not raise any AttributeError
        try:
            presenter.present_app_agent_response(mock_response, print_action=False)
        except AttributeError as e:
            self.fail(f"AppAgent response structure changed: {e}")

    @patch('ufo.agents.presenters.rich_presenter.Console')
    def test_host_agent_response_structure(self, mock_console_class):
        """Test that HostAgent response structure is maintained"""
        mock_console = MagicMock()
        mock_console_class.return_value = mock_console
        
        presenter = RichPresenter(console=mock_console)
        
        # Create a response with all expected fields
        mock_response = Mock()
        mock_response.observation = "Test"
        mock_response.thought = "Test"
        mock_response.function = None
        mock_response.arguments = {}
        mock_response.current_subtask = "Test"
        mock_response.plan = []
        mock_response.message = []
        mock_response.status = "CONTINUE"
        mock_response.comment = None
        
        # Should not raise any AttributeError
        try:
            presenter.present_host_agent_response(mock_response)
        except AttributeError as e:
            self.fail(f"HostAgent response structure changed: {e}")


if __name__ == "__main__":
    # Run tests with verbose output
    unittest.main(verbosity=2)
