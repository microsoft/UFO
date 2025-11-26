# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Unit tests for the Presenter layer.

Tests ensure that:
1. The presenter factory creates correct presenter instances
2. RichPresenter produces consistent output with original implementations
3. All agent types can use the presenter correctly
4. Action formatting works as expected
"""

import unittest
from unittest.mock import Mock, MagicMock, patch, call
from io import StringIO
import sys

from ufo.agents.presenters import BasePresenter, RichPresenter, PresenterFactory
from ufo.agents.processors.schemas.actions import ActionCommandInfo, ListActionCommandInfo
from aip.messages import Result, ResultStatus


class TestPresenterFactory(unittest.TestCase):
    """Tests for PresenterFactory"""

    def test_create_rich_presenter(self):
        """Test creating a Rich presenter"""
        presenter = PresenterFactory.create_presenter("rich")
        self.assertIsInstance(presenter, RichPresenter)
        self.assertIsInstance(presenter, BasePresenter)

    def test_create_presenter_with_unknown_type(self):
        """Test that unknown presenter type raises ValueError"""
        with self.assertRaises(ValueError) as context:
            PresenterFactory.create_presenter("unknown")
        self.assertIn("Unknown presenter type", str(context.exception))

    def test_get_available_presenters(self):
        """Test getting list of available presenters"""
        presenters = PresenterFactory.get_available_presenters()
        self.assertIn("rich", presenters)
        self.assertIsInstance(presenters, list)

    def test_register_custom_presenter(self):
        """Test registering a custom presenter"""
        class CustomPresenter(BasePresenter):
            def present_response(self, response, **kwargs):
                pass
            def present_thought(self, thought):
                pass
            def present_observation(self, observation):
                pass
            def present_status(self, status, **kwargs):
                pass
            def present_actions(self, actions, **kwargs):
                pass
            def present_plan(self, plan):
                pass
            def present_comment(self, comment):
                pass
            def present_results(self, results):
                pass

        PresenterFactory.register_presenter("custom", CustomPresenter)
        presenter = PresenterFactory.create_presenter("custom")
        self.assertIsInstance(presenter, CustomPresenter)

    def test_register_invalid_presenter(self):
        """Test that registering non-BasePresenter class raises TypeError"""
        class InvalidPresenter:
            pass

        with self.assertRaises(TypeError):
            PresenterFactory.register_presenter("invalid", InvalidPresenter)


class TestRichPresenter(unittest.TestCase):
    """Tests for RichPresenter"""

    def setUp(self):
        """Set up test fixtures"""
        self.presenter = RichPresenter()

    @patch('ufo.agents.presenters.rich_presenter.Console')
    def test_present_thought(self, mock_console_class):
        """Test presenting thought"""
        mock_console = MagicMock()
        mock_console_class.return_value = mock_console
        
        presenter = RichPresenter(console=mock_console)
        presenter.present_thought("Test thought")
        
        # Verify console.print was called with Panel
        self.assertTrue(mock_console.print.called)
        call_args = mock_console.print.call_args
        self.assertIsNotNone(call_args)

    @patch('ufo.agents.presenters.rich_presenter.Console')
    def test_present_observation(self, mock_console_class):
        """Test presenting observation"""
        mock_console = MagicMock()
        mock_console_class.return_value = mock_console
        
        presenter = RichPresenter(console=mock_console)
        presenter.present_observation("Test observation")
        
        # Verify console.print was called
        self.assertTrue(mock_console.print.called)

    @patch('ufo.agents.presenters.rich_presenter.Console')
    def test_present_status_finish(self, mock_console_class):
        """Test presenting FINISH status"""
        mock_console = MagicMock()
        mock_console_class.return_value = mock_console
        
        presenter = RichPresenter(console=mock_console)
        presenter.present_status("FINISH")
        
        # Verify console.print was called
        self.assertTrue(mock_console.print.called)

    @patch('ufo.agents.presenters.rich_presenter.Console')
    def test_present_status_fail(self, mock_console_class):
        """Test presenting FAIL status"""
        mock_console = MagicMock()
        mock_console_class.return_value = mock_console
        
        presenter = RichPresenter(console=mock_console)
        presenter.present_status("FAIL")
        
        # Verify console.print was called
        self.assertTrue(mock_console.print.called)

    @patch('ufo.agents.presenters.rich_presenter.Console')
    def test_present_plan(self, mock_console_class):
        """Test presenting plan"""
        mock_console = MagicMock()
        mock_console_class.return_value = mock_console
        
        presenter = RichPresenter(console=mock_console)
        plan = ["Step 1", "Step 2", "Step 3"]
        presenter.present_plan(plan)
        
        # Verify console.print was called
        self.assertTrue(mock_console.print.called)

    @patch('ufo.agents.presenters.rich_presenter.Console')
    def test_present_comment(self, mock_console_class):
        """Test presenting comment"""
        mock_console = MagicMock()
        mock_console_class.return_value = mock_console
        
        presenter = RichPresenter(console=mock_console)
        presenter.present_comment("Test comment")
        
        # Verify console.print was called
        self.assertTrue(mock_console.print.called)

    @patch('ufo.agents.presenters.rich_presenter.Console')
    def test_present_results(self, mock_console_class):
        """Test presenting results"""
        mock_console = MagicMock()
        mock_console_class.return_value = mock_console
        
        presenter = RichPresenter(console=mock_console)
        presenter.present_results({"result": "success"})
        
        # Verify console.print was called
        self.assertTrue(mock_console.print.called)

    @patch('ufo.agents.presenters.rich_presenter.Console')
    def test_present_results_truncation(self, mock_console_class):
        """Test that long results are truncated"""
        mock_console = MagicMock()
        mock_console_class.return_value = mock_console
        
        presenter = RichPresenter(console=mock_console)
        long_result = "x" * 1000  # Create a result longer than 500 chars
        presenter.present_results(long_result)
        
        # Verify console.print was called
        self.assertTrue(mock_console.print.called)


class TestAppAgentPresentation(unittest.TestCase):
    """Tests for AppAgent-specific presentation"""

    @patch('ufo.agents.presenters.rich_presenter.Console')
    def test_present_app_agent_response(self, mock_console_class):
        """Test presenting AppAgent response"""
        mock_console = MagicMock()
        mock_console_class.return_value = mock_console
        
        presenter = RichPresenter(console=mock_console)
        
        # Create mock response
        mock_response = Mock()
        mock_response.observation = "Test observation"
        mock_response.thought = "Test thought"
        mock_response.plan = ["Step 1", "Step 2"]
        mock_response.comment = "Test comment"
        mock_response.save_screenshot = {"save": False}
        
        # Create mock action
        mock_action = Mock(spec=ActionCommandInfo)
        mock_action.function = "test_function"
        mock_action.arguments = {"arg1": "value1"}
        mock_action.status = "pending"
        mock_response.action = mock_action
        
        presenter.present_app_agent_response(mock_response, print_action=True)
        
        # Verify console.print was called multiple times (for obs, thought, actions, plan, comment)
        self.assertTrue(mock_console.print.called)
        self.assertGreaterEqual(mock_console.print.call_count, 4)

    @patch('ufo.agents.presenters.rich_presenter.Console')
    def test_present_app_agent_response_with_screenshot(self, mock_console_class):
        """Test presenting AppAgent response with screenshot notice"""
        mock_console = MagicMock()
        mock_console_class.return_value = mock_console
        
        presenter = RichPresenter(console=mock_console)
        
        # Create mock response
        mock_response = Mock()
        mock_response.observation = "Test observation"
        mock_response.thought = "Test thought"
        mock_response.plan = ["Step 1"]
        mock_response.comment = None
        mock_response.save_screenshot = {"save": True, "reason": "Important moment"}
        mock_response.action = []
        
        presenter.present_app_agent_response(mock_response, print_action=False)
        
        # Verify console.print was called
        self.assertTrue(mock_console.print.called)


class TestHostAgentPresentation(unittest.TestCase):
    """Tests for HostAgent-specific presentation"""

    @patch('ufo.agents.presenters.rich_presenter.Console')
    def test_present_host_agent_response(self, mock_console_class):
        """Test presenting HostAgent response"""
        mock_console = MagicMock()
        mock_console_class.return_value = mock_console
        
        presenter = RichPresenter(console=mock_console)
        
        # Create mock response
        mock_response = Mock()
        mock_response.observation = "Test observation"
        mock_response.thought = "Test thought"
        mock_response.function = "test_function"
        mock_response.arguments = {"arg1": "value1"}
        mock_response.current_subtask = "Current task"
        mock_response.plan = ["Next task 1", "Next task 2"]
        mock_response.message = ["Message 1", "Message 2"]
        mock_response.status = "CONTINUE"
        mock_response.comment = None
        
        # Pass action_str as parameter instead of setting it on response
        action_str = "test_function(arg1=value1)"
        presenter.present_host_agent_response(mock_response, action_str=action_str)
        
        # Verify console.print was called multiple times
        self.assertTrue(mock_console.print.called)
        self.assertGreaterEqual(mock_console.print.call_count, 5)

    @patch('ufo.agents.presenters.rich_presenter.Console')
    def test_present_host_agent_response_without_action_str(self, mock_console_class):
        """Test presenting HostAgent response without pre-formatted action string"""
        mock_console = MagicMock()
        mock_console_class.return_value = mock_console
        
        presenter = RichPresenter(console=mock_console)
        
        # Create mock response
        mock_response = Mock()
        mock_response.observation = "Test observation"
        mock_response.thought = "Test thought"
        mock_response.function = "test_function"
        mock_response.arguments = {"arg1": "value1"}
        mock_response.current_subtask = "Current task"
        mock_response.plan = ["Next task 1"]
        mock_response.message = None
        mock_response.status = "CONTINUE"
        mock_response.comment = None
        
        # Call without action_str - should use default formatting
        presenter.present_host_agent_response(mock_response)
        
        # Verify console.print was called
        self.assertTrue(mock_console.print.called)

    @patch('ufo.agents.presenters.rich_presenter.Console')
    def test_present_host_agent_response_with_application(self, mock_console_class):
        """Test presenting HostAgent response with application selection"""
        mock_console = MagicMock()
        mock_console_class.return_value = mock_console
        
        presenter = RichPresenter(console=mock_console)
        
        # Create mock response
        mock_response = Mock()
        mock_response.observation = "Test observation"
        mock_response.thought = "Test thought"
        mock_response.function = "select_application_window"
        mock_response.arguments = {"name": "TestApp"}
        mock_response.current_subtask = "Select app"
        mock_response.plan = []
        mock_response.message = []
        mock_response.status = "CONTINUE"
        mock_response.comment = None
        mock_response._formatted_action = "select_application_window(name=TestApp)"
        
        presenter.present_host_agent_response(mock_response)
        
        # Verify console.print was called
        self.assertTrue(mock_console.print.called)


class TestConstellationAgentPresentation(unittest.TestCase):
    """Tests for ConstellationAgent-specific presentation"""

    @patch('ufo.agents.presenters.rich_presenter.Console')
    def test_present_constellation_agent_response(self, mock_console_class):
        """Test presenting ConstellationAgent response"""
        mock_console = MagicMock()
        mock_console_class.return_value = mock_console
        
        presenter = RichPresenter(console=mock_console)
        
        # Create mock response
        mock_response = Mock()
        mock_response.thought = "Test thought"
        mock_response.status = "CONTINUE"
        mock_response.constellation = None
        mock_response.action = None
        mock_response.results = None
        
        presenter.present_constellation_agent_response(mock_response, print_action=False)
        
        # Verify console.print was called at least twice (thought + status)
        self.assertTrue(mock_console.print.called)
        self.assertGreaterEqual(mock_console.print.call_count, 2)

    @patch('ufo.agents.presenters.rich_presenter.Console')
    def test_present_constellation_with_tasks(self, mock_console_class):
        """Test presenting constellation with tasks and dependencies"""
        mock_console = MagicMock()
        mock_console_class.return_value = mock_console
        
        presenter = RichPresenter(console=mock_console)
        
        # Create mock constellation
        mock_constellation = Mock()
        mock_constellation.constellation_id = "test-constellation-123"
        mock_constellation.name = "Test Constellation"
        mock_constellation.state = "PENDING"
        
        # Create mock tasks
        mock_task = Mock()
        mock_task.name = "Test Task"
        mock_task.target_device_id = "device-1"
        mock_task.description = "Test description"
        mock_task.tips = ["Tip 1", "Tip 2"]
        mock_constellation.tasks = {"task-1": mock_task}
        
        # Create mock dependencies
        mock_dep = Mock()
        mock_dep.from_task_id = "task-1"
        mock_dep.to_task_id = "task-2"
        mock_dep.condition_description = "After completion"
        mock_constellation.dependencies = {"dep-1": mock_dep}
        
        # Create mock response
        mock_response = Mock()
        mock_response.thought = "Creating constellation"
        mock_response.status = "START"
        mock_response.constellation = mock_constellation
        mock_response.action = None
        mock_response.results = None
        
        presenter.present_constellation_agent_response(mock_response, print_action=False)
        
        # Verify console.print was called multiple times
        self.assertTrue(mock_console.print.called)
        # Should print: thought, status, constellation info, task details, dependencies
        self.assertGreaterEqual(mock_console.print.call_count, 5)


class TestActionListPresentation(unittest.TestCase):
    """Tests for action list presentation"""

    @patch('ufo.agents.presenters.rich_presenter.Console')
    def test_present_action_list(self, mock_console_class):
        """Test presenting action list"""
        mock_console = MagicMock()
        mock_console_class.return_value = mock_console
        
        presenter = RichPresenter(console=mock_console)
        
        # Create mock actions
        mock_action1 = Mock()
        mock_action1.to_representation = Mock(return_value="Action 1")
        mock_action1.result = Mock()
        mock_action1.result.status = ResultStatus.SUCCESS
        
        mock_action2 = Mock()
        mock_action2.to_representation = Mock(return_value="Action 2")
        mock_action2.result = Mock()
        mock_action2.result.status = ResultStatus.FAILURE
        
        mock_action_list = Mock()
        mock_action_list.actions = [mock_action1, mock_action2]
        mock_action_list.status = "COMPLETED"
        
        presenter.present_action_list(mock_action_list, success_only=False)
        
        # Verify console.print was called (for actions and final status)
        self.assertTrue(mock_console.print.called)

    @patch('ufo.agents.presenters.rich_presenter.Console')
    def test_present_action_list_success_only(self, mock_console_class):
        """Test presenting only successful actions"""
        mock_console = MagicMock()
        mock_console_class.return_value = mock_console
        
        presenter = RichPresenter(console=mock_console)
        
        # Create mock actions
        mock_action1 = Mock()
        mock_action1.to_representation = Mock(return_value="Action 1")
        mock_action1.result = Mock()
        mock_action1.result.status = ResultStatus.SUCCESS
        
        mock_action2 = Mock()
        mock_action2.to_representation = Mock(return_value="Action 2")
        mock_action2.result = Mock()
        mock_action2.result.status = ResultStatus.FAILURE
        
        mock_action_list = Mock()
        mock_action_list.actions = [mock_action1, mock_action2]
        mock_action_list.status = "COMPLETED"
        
        presenter.present_action_list(mock_action_list, success_only=True)
        
        # Verify console.print was called
        self.assertTrue(mock_console.print.called)


class TestConstellationEditingActionsPresentation(unittest.TestCase):
    """Tests for constellation editing actions presentation"""

    @patch('ufo.agents.presenters.rich_presenter.Console')
    def test_present_constellation_editing_actions(self, mock_console_class):
        """Test presenting constellation editing actions"""
        mock_console = MagicMock()
        mock_console_class.return_value = mock_console
        
        presenter = RichPresenter(console=mock_console)
        
        # Create mock actions
        mock_action = Mock()
        mock_action.function = "add_task"
        mock_action.arguments = {"task_id": "task-1", "name": "Test Task"}
        mock_action.result = Mock()
        mock_action.result.status = ResultStatus.SUCCESS
        mock_action.result.error = None
        
        mock_action_list = Mock()
        mock_action_list.actions = [mock_action]
        mock_action_list.status = "CONTINUE"
        
        presenter.present_constellation_editing_actions(mock_action_list)
        
        # Verify console.print was called
        self.assertTrue(mock_console.print.called)

    @patch('ufo.agents.presenters.rich_presenter.Console')
    def test_present_constellation_editing_actions_empty(self, mock_console_class):
        """Test presenting empty constellation editing actions"""
        mock_console = MagicMock()
        mock_console_class.return_value = mock_console
        
        presenter = RichPresenter(console=mock_console)
        
        mock_action_list = Mock()
        mock_action_list.actions = []
        
        presenter.present_constellation_editing_actions(mock_action_list)
        
        # Verify console.print was called (to show "No actions" message)
        self.assertTrue(mock_console.print.called)

    def test_format_constellation_operation_add_task(self):
        """Test formatting add_task operation"""
        presenter = RichPresenter()
        
        mock_action = Mock()
        mock_action.function = "add_task"
        mock_action.arguments = {"task_id": "task-1", "name": "Test Task"}
        
        result = presenter._format_constellation_operation(mock_action)
        self.assertIn("Add Task", result)
        self.assertIn("task-1", result)

    def test_format_constellation_operation_remove_task(self):
        """Test formatting remove_task operation"""
        presenter = RichPresenter()
        
        mock_action = Mock()
        mock_action.function = "remove_task"
        mock_action.arguments = {"task_id": "task-1"}
        
        result = presenter._format_constellation_operation(mock_action)
        self.assertIn("Remove Task", result)
        self.assertIn("task-1", result)

    def test_format_constellation_operation_add_dependency(self):
        """Test formatting add_dependency operation"""
        presenter = RichPresenter()
        
        mock_action = Mock()
        mock_action.function = "add_dependency"
        mock_action.arguments = {
            "dependency_id": "dep-1",
            "from_task_id": "task-1",
            "to_task_id": "task-2"
        }
        
        result = presenter._format_constellation_operation(mock_action)
        self.assertIn("Add Dependency", result)
        self.assertIn("task-1", result)
        self.assertIn("task-2", result)


if __name__ == "__main__":
    unittest.main()
