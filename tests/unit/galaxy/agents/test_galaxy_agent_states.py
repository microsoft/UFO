# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Unit tests for Galaxy Agent State Machine

Tests cover all state transitions, edge cases, and error handling
for the Constellation state machine implementation.
"""

import asyncio
import pytest
import time
import sys
import os
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from typing import Dict, Any, Optional

# Add project root to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))

from galaxy.agents.constellation_agent_states import (
    StartConstellationAgentState,
    MonitorConstellationAgentState,
    FinishConstellationAgentState,
    FailConstellationAgentState,
    ConstellationAgentStateManager,
    ConstellationAgentStatus,
)
from tests.galaxy.mocks import MockConstellationAgent
from galaxy.constellation import TaskConstellation, TaskStar, TaskStatus
from galaxy.constellation.enums import ConstellationState, TaskPriority
from galaxy.constellation.task_star_line import TaskStarLine
from galaxy.core.events import TaskEvent, EventType
from ufo.module.context import Context


class TestAgentStateMachine:
    """Test the agent state machine implementation."""

    @pytest.fixture
    def mock_agent(self):
        """Create a mock agent for testing."""
        agent = MockConstellationAgent()
        agent.current_request = "Test request"
        agent.orchestrator = Mock()
        agent.orchestrator.orchestrate_constellation = AsyncMock()
        agent.logger = Mock()
        return agent

    @pytest.fixture
    def mock_context(self):
        """Create a mock context for testing."""
        return Mock(spec=Context)

    @pytest.fixture
    def simple_constellation(self):
        """Create a simple constellation for testing."""
        constellation = TaskConstellation("test_constellation")
        task1 = TaskStar("task1", "Test task 1", TaskPriority.MEDIUM)
        task2 = TaskStar("task2", "Test task 2", TaskPriority.MEDIUM)
        constellation.add_task(task1)
        constellation.add_task(task2)

        # Create dependency using TaskStarLine
        dependency = TaskStarLine.create_unconditional("task1", "task2")
        constellation.add_dependency(dependency)
        return constellation

    @pytest.mark.asyncio
    async def test_start_state_success(
        self, mock_agent, mock_context, simple_constellation
    ):
        """Test successful start state execution."""
        # Arrange
        state = StartConstellationAgentState()
        mock_agent.process_initial_request = AsyncMock(
            return_value=simple_constellation
        )

        # Act
        await state.handle(mock_agent, mock_context)

        # Assert
        assert mock_agent._status == "executing"
        assert mock_agent.current_constellation == simple_constellation
        assert mock_agent._orchestration_task is not None
        mock_agent.orchestrator.orchestrate_constellation.assert_called_once_with(
            simple_constellation
        )

    @pytest.mark.asyncio
    async def test_start_state_no_constellation(self, mock_agent, mock_context):
        """Test start state when constellation creation fails."""
        # Arrange
        state = StartConstellationAgentState()
        mock_agent.process_initial_request = AsyncMock(return_value=None)

        # Act
        await state.handle(mock_agent, mock_context)

        # Assert
        assert mock_agent._status == "failed"
        assert mock_agent.current_constellation is None

    @pytest.mark.asyncio
    async def test_start_state_exception(self, mock_agent, mock_context):
        """Test start state with exception."""
        # Arrange
        state = StartConstellationAgentState()
        mock_agent.process_initial_request = AsyncMock(
            side_effect=Exception("Test error")
        )

        # Act
        await state.handle(mock_agent, mock_context)

        # Assert
        assert mock_agent._status == "failed"

    def test_start_state_transitions(self, mock_agent):
        """Test start state transitions."""
        state = StartConstellationAgentState()

        # Test transition to fail
        mock_agent._status = "failed"
        next_state = state.next_state(mock_agent)
        assert isinstance(next_state, FailConstellationAgentState)

        # Test transition to finish
        mock_agent._status = "finished"
        next_state = state.next_state(mock_agent)
        assert isinstance(next_state, FinishConstellationAgentState)

        # Test transition to monitor
        mock_agent._status = "executing"
        next_state = state.next_state(mock_agent)
        assert isinstance(next_state, MonitorConstellationAgentState)

    @pytest.mark.asyncio
    async def test_monitor_state_task_completion(
        self, mock_agent, mock_context, simple_constellation
    ):
        """Test monitor state handling task completion."""
        # Arrange
        state = MonitorConstellationAgentState()
        mock_agent._current_constellation = simple_constellation
        mock_agent.task_completion_queue = asyncio.Queue()
        mock_agent.update_constellation_with_lock = AsyncMock(
            return_value=simple_constellation
        )
        mock_agent.should_continue = AsyncMock(return_value=False)

        # Create task event
        task_event = TaskEvent(
            event_type=EventType.TASK_COMPLETED,
            source_id="test_orchestrator",
            timestamp=time.time(),
            data={},
            task_id="task1",
            status="completed",
            result={"success": True},
            error=None,
        )

        # Put event in queue
        await mock_agent.task_completion_queue.put(task_event)

        # Act
        await state.handle(mock_agent, mock_context)

        # Assert
        mock_agent.update_constellation_with_lock.assert_called_once()
        mock_agent.should_continue.assert_called_once()

    @pytest.mark.asyncio
    async def test_monitor_state_continue_processing(
        self, mock_agent, mock_context, simple_constellation
    ):
        """Test monitor state when agent decides to continue."""
        # Arrange
        state = MonitorConstellationAgentState()
        mock_agent._current_constellation = simple_constellation
        mock_agent.task_completion_queue = asyncio.Queue()
        mock_agent.update_constellation_with_lock = AsyncMock(
            return_value=simple_constellation
        )
        mock_agent.should_continue = AsyncMock(return_value=True)

        # Set constellation state to completed but agent wants to continue
        simple_constellation._state = ConstellationState.COMPLETED

        # Create task event
        task_event = TaskEvent(
            event_type=EventType.TASK_COMPLETED,
            source_id="test_orchestrator",
            timestamp=time.time(),
            data={},
            task_id="task1",
            status="completed",
            result={"success": True},
            error=None,
        )

        await mock_agent.task_completion_queue.put(task_event)

        # Act
        await state.handle(mock_agent, mock_context)

        # Assert
        assert mock_agent._status == "continue"

    @pytest.mark.asyncio
    async def test_monitor_state_agent_decides_finish(
        self, mock_agent, mock_context, simple_constellation
    ):
        """Test monitor state when agent decides task is finished."""
        # Arrange
        state = MonitorConstellationAgentState()
        mock_agent._current_constellation = simple_constellation
        mock_agent.task_completion_queue = asyncio.Queue()
        mock_agent.update_constellation_with_lock = AsyncMock(
            return_value=simple_constellation
        )
        mock_agent.should_continue = AsyncMock(return_value=False)

        # Set constellation to completed
        simple_constellation._state = ConstellationState.COMPLETED

        # Create task event
        task_event = TaskEvent(
            event_type=EventType.TASK_COMPLETED,
            source_id="test_orchestrator",
            timestamp=time.time(),
            data={},
            task_id="task1",
            status="completed",
            result={"success": True},
            error=None,
        )

        await mock_agent.task_completion_queue.put(task_event)

        # Act
        await state.handle(mock_agent, mock_context)

        # Assert
        assert mock_agent._status == "finished"

    @pytest.mark.asyncio
    async def test_monitor_state_exception_handling(self, mock_agent, mock_context):
        """Test monitor state exception handling."""
        # Arrange
        state = MonitorConstellationAgentState()
        mock_agent.task_completion_queue = asyncio.Queue()
        mock_agent.update_constellation_with_lock = AsyncMock(
            side_effect=Exception("Test error")
        )

        # Create task event
        task_event = TaskEvent(
            event_type=EventType.TASK_COMPLETED,
            source_id="test_orchestrator",
            timestamp=time.time(),
            data={},
            task_id="task1",
            status="completed",
            result={"success": True},
            error=None,
        )

        await mock_agent.task_completion_queue.put(task_event)

        # Act
        await state.handle(mock_agent, mock_context)

        # Assert
        assert mock_agent._status == "failed"

    def test_monitor_state_transitions(self, mock_agent):
        """Test monitor state transitions."""
        state = MonitorConstellationAgentState()

        # Test transition to fail
        mock_agent._status = "failed"
        next_state = state.next_state(mock_agent)
        assert isinstance(next_state, FailConstellationAgentState)

        # Test transition to finish
        mock_agent._status = "finished"
        next_state = state.next_state(mock_agent)
        assert isinstance(next_state, FinishConstellationAgentState)

        # Test transition to continue (restart)
        mock_agent._status = "continue"
        next_state = state.next_state(mock_agent)
        assert isinstance(next_state, StartConstellationAgentState)

        # Test stay in monitor
        mock_agent._status = "monitoring"
        next_state = state.next_state(mock_agent)
        assert isinstance(next_state, MonitorConstellationAgentState)

    @pytest.mark.asyncio
    async def test_finish_state(self, mock_agent, mock_context):
        """Test finish state execution."""
        # Arrange
        state = FinishConstellationAgentState()
        mock_agent._orchestration_task = Mock()
        mock_agent._orchestration_task.done.return_value = False

        # Act
        await state.handle(mock_agent, mock_context)

        # Assert
        assert mock_agent._status == "finished"
        mock_agent._orchestration_task.cancel.assert_called_once()
        assert state.is_round_end()
        assert state.is_subtask_end()

    @pytest.mark.asyncio
    async def test_fail_state(self, mock_agent, mock_context):
        """Test fail state execution."""
        # Arrange
        state = FailConstellationAgentState()
        mock_agent._orchestration_task = Mock()
        mock_agent._orchestration_task.done.return_value = False

        # Act
        await state.handle(mock_agent, mock_context)

        # Assert
        assert mock_agent._status == "failed"
        mock_agent._orchestration_task.cancel.assert_called_once()
        assert state.is_round_end()
        assert state.is_subtask_end()

    def test_state_manager(self):
        """Test state manager functionality."""
        manager = ConstellationAgentStateManager()

        # Test none_state
        none_state = manager.none_state
        assert isinstance(none_state, StartConstellationAgentState)

        # Test state registration
        assert (
            StartConstellationAgentState.name() == ConstellationAgentStatus.START.value
        )
        assert (
            MonitorConstellationAgentState.name()
            == ConstellationAgentStatus.MONITOR.value
        )
        assert (
            FinishConstellationAgentState.name()
            == ConstellationAgentStatus.FINISH.value
        )
        assert FailConstellationAgentState.name() == ConstellationAgentStatus.FAIL.value

    def test_state_properties(self):
        """Test state properties."""
        start_state = StartConstellationAgentState()
        assert not start_state.is_round_end()
        assert not start_state.is_subtask_end()

        monitor_state = MonitorConstellationAgentState()
        assert not monitor_state.is_round_end()
        assert not monitor_state.is_subtask_end()

        finish_state = FinishConstellationAgentState()
        assert finish_state.is_round_end()
        assert finish_state.is_subtask_end()

        fail_state = FailConstellationAgentState()
        assert fail_state.is_round_end()
        assert fail_state.is_subtask_end()


class TestTaskTimeoutConfiguration:
    """Test task timeout configuration in start state."""

    @pytest.fixture
    def mock_config(self):
        """Mock config for timeout testing."""
        config_data = {
            "GALAXY_TASK_TIMEOUT": 1800.0,
            "GALAXY_CRITICAL_TASK_TIMEOUT": 3600.0,
        }

        with patch("ufo.config.Config.get_instance") as mock_config_instance:
            mock_config_instance.return_value.config_data = config_data
            yield config_data

    @pytest.fixture
    def simple_constellation(self):
        """Create simple constellation for testing."""
        constellation = TaskConstellation("test_constellation")
        task1 = TaskStar("task1", "Test task 1", TaskPriority.MEDIUM)
        task2 = TaskStar("task2", "Test task 2", TaskPriority.MEDIUM)
        constellation.add_task(task1)
        constellation.add_task(task2)

        # Create dependency using TaskStarLine
        dependency = TaskStarLine.create_unconditional("task1", "task2")
        constellation.add_dependency(dependency)
        return constellation

    @pytest.mark.asyncio
    async def test_timeout_configuration(self, mock_config, simple_constellation):
        """Test task timeout configuration."""
        # Arrange
        state = StartConstellationAgentState()

        # Set different priorities
        task1 = simple_constellation.tasks["task1"]
        task2 = simple_constellation.tasks["task2"]
        task1.priority = TaskPriority.HIGH  # Should get critical timeout
        task2.priority = TaskPriority.LOW  # Should get default timeout

        # Clear existing timeouts
        task1._timeout = None
        task2._timeout = None

        # Act
        state._configure_task_timeouts(simple_constellation)

        # Assert
        assert task1._timeout == 3600.0  # Critical timeout
        assert task2._timeout == 1800.0  # Default timeout

    @pytest.mark.asyncio
    async def test_timeout_configuration_preserves_existing(
        self, mock_config, simple_constellation
    ):
        """Test that existing timeouts are preserved."""
        # Arrange
        state = StartConstellationAgentState()
        task1 = simple_constellation.tasks["task1"]
        task1._timeout = 5000.0  # Existing timeout

        # Act
        state._configure_task_timeouts(simple_constellation)

        # Assert
        assert task1._timeout == 5000.0  # Should preserve existing


class TestAgentIntegration:
    """Test agent integration with state machine."""

    @pytest.fixture
    def agent_with_states(self):
        """Create agent with state machine support."""
        agent = MockConstellationAgent()
        agent.orchestrator = Mock()
        agent.orchestrator.orchestrate_constellation = AsyncMock()
        return agent

    @pytest.fixture
    def simple_constellation(self):
        """Create simple constellation for testing."""
        constellation = TaskConstellation("test_constellation")
        task1 = TaskStar("task1", "Test task 1", TaskPriority.MEDIUM)
        task2 = TaskStar("task2", "Test task 2", TaskPriority.MEDIUM)
        constellation.add_task(task1)
        constellation.add_task(task2)

        # Create dependency using TaskStarLine
        dependency = TaskStarLine.create_unconditional("task1", "task2")
        constellation.add_dependency(dependency)
        return constellation

    @pytest.mark.asyncio
    async def test_agent_initialization(self, agent_with_states):
        """Test agent initializes with correct state."""
        assert isinstance(agent_with_states.state, StartConstellationAgentState)
        assert hasattr(agent_with_states, "task_completion_queue")
        assert hasattr(agent_with_states, "current_request")
        assert hasattr(agent_with_states, "orchestrator")

    @pytest.mark.asyncio
    async def test_agent_status_manager(self, agent_with_states):
        """Test agent status manager."""
        manager = agent_with_states.status_manager
        assert isinstance(manager, ConstellationAgentStateManager)

    @pytest.mark.asyncio
    async def test_full_state_cycle_success(
        self, agent_with_states, simple_constellation
    ):
        """Test full successful state cycle."""
        # Mock methods
        agent_with_states.process_initial_request = AsyncMock(
            return_value=simple_constellation
        )
        agent_with_states.update_constellation_with_lock = AsyncMock(
            return_value=simple_constellation
        )
        agent_with_states.should_continue = AsyncMock(return_value=False)

        # Start -> Monitor (simulate task completion) -> Finish

        # 1. Start state
        assert isinstance(agent_with_states.state, StartConstellationAgentState)
        await agent_with_states.handle(None)

        # Should transition to monitor
        next_state = agent_with_states.state.next_state(agent_with_states)
        agent_with_states.set_state(next_state)
        assert isinstance(agent_with_states.state, MonitorConstellationAgentState)

        # 2. Monitor state - add task completion event
        task_event = TaskEvent(
            event_type=EventType.TASK_COMPLETED,
            source_id="test",
            timestamp=time.time(),
            data={},
            task_id="task1",
            status="completed",
            result={"success": True},
            error=None,
        )

        await agent_with_states.task_completion_queue.put(task_event)
        simple_constellation._state = ConstellationState.COMPLETED

        await agent_with_states.handle(None)

        # Should transition to finish
        next_state = agent_with_states.state.next_state(agent_with_states)
        agent_with_states.set_state(next_state)
        assert isinstance(agent_with_states.state, FinishConstellationAgentState)

        # 3. Finish state
        await agent_with_states.handle(None)
        assert agent_with_states._status == "finished"
        assert agent_with_states.state.is_round_end()

    @pytest.mark.asyncio
    async def test_full_state_cycle_with_continue(
        self, agent_with_states, simple_constellation
    ):
        """Test state cycle with continuation."""
        # Mock methods
        agent_with_states.process_initial_request = AsyncMock(
            return_value=simple_constellation
        )
        agent_with_states.update_constellation_with_lock = AsyncMock(
            return_value=simple_constellation
        )
        agent_with_states.should_continue = AsyncMock(return_value=True)

        # Start -> Monitor -> Continue -> Start (again)

        # 1. Start state
        await agent_with_states.handle(None)
        next_state = agent_with_states.state.next_state(agent_with_states)
        agent_with_states.set_state(next_state)

        # 2. Monitor state with continuation
        task_event = TaskEvent(
            event_type=EventType.TASK_COMPLETED,
            source_id="test",
            timestamp=time.time(),
            data={},
            task_id="task1",
            status="completed",
            result={"success": True},
            error=None,
        )

        await agent_with_states.task_completion_queue.put(task_event)
        simple_constellation._state = ConstellationState.COMPLETED

        await agent_with_states.handle(None)

        # Should transition back to start
        next_state = agent_with_states.state.next_state(agent_with_states)
        assert isinstance(next_state, StartConstellationAgentState)
        assert agent_with_states._status == "continue"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
