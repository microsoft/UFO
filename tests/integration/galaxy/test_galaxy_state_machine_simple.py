# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Simplified Integration tests for Galaxy Agent State Machine

Focuses on testing the core state machine logic without complex orchestration.
"""

import asyncio
import pytest
import time
from unittest.mock import Mock, AsyncMock
from typing import Dict, Any

from galaxy.agents.galaxy_agent import MockGalaxyWeaverAgent
from galaxy.agents.galaxy_agent_states import (
    StartGalaxyAgentState,
    MonitorGalaxyAgentState,
    FinishGalaxyAgentState,
    FailGalaxyAgentState,
)
from galaxy.constellation import TaskConstellation, TaskStar, TaskStatus
from galaxy.constellation.task_star_line import TaskStarLine
from galaxy.constellation.enums import ConstellationState, TaskPriority
from galaxy.core.events import TaskEvent, EventType
from ufo.module.context import Context


class TestGalaxyAgentStateMachineSimple:
    """Simplified tests for agent state machine core functionality."""

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

    @pytest.fixture
    def mock_agent(self):
        """Create a mock agent for testing."""
        agent = MockGalaxyWeaverAgent()
        agent.orchestrator = Mock()
        agent.orchestrator.orchestrate_constellation = AsyncMock()
        return agent

    @pytest.mark.asyncio
    async def test_agent_completes_successfully(self, simple_constellation, mock_agent):
        """Test that agent completes successfully when constellation is done."""
        # Setup
        mock_agent.process_initial_request = AsyncMock(
            return_value=simple_constellation
        )
        mock_agent.update_constellation_with_lock = AsyncMock(
            return_value=simple_constellation
        )
        mock_agent.should_continue = AsyncMock(return_value=False)

        # Simulate the constellation completing
        simple_constellation._state = ConstellationState.COMPLETED

        # Run the state machine cycle manually
        # 1. Start state
        assert isinstance(mock_agent.state, StartGalaxyAgentState)
        await mock_agent.handle(None)

        # Should transition to monitor
        next_state = mock_agent.state.next_state(mock_agent)
        mock_agent.set_state(next_state)
        assert isinstance(mock_agent.state, MonitorGalaxyAgentState)

        # 2. Simulate task completion event
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
        await mock_agent.task_completion_queue.put(task_event)

        # Handle monitor state with timeout
        try:
            await asyncio.wait_for(mock_agent.handle(None), timeout=1.0)
        except asyncio.TimeoutError:
            pytest.fail("Monitor state timed out - possible deadlock")

        # Should transition to finish
        next_state = mock_agent.state.next_state(mock_agent)
        mock_agent.set_state(next_state)
        assert isinstance(mock_agent.state, FinishGalaxyAgentState)

        # 3. Finish state
        await mock_agent.handle(None)
        assert mock_agent._status == "finished"

    @pytest.mark.asyncio
    async def test_agent_continues_processing(self, simple_constellation, mock_agent):
        """Test that agent continues when it decides to add more tasks."""
        # Setup
        mock_agent.process_initial_request = AsyncMock(
            return_value=simple_constellation
        )
        mock_agent.update_constellation_with_lock = AsyncMock(
            return_value=simple_constellation
        )
        mock_agent.should_continue = AsyncMock(
            return_value=True
        )  # Agent wants to continue

        # Simulate the constellation completing
        simple_constellation._state = ConstellationState.COMPLETED

        # Run the state machine cycle
        await mock_agent.handle(None)
        next_state = mock_agent.state.next_state(mock_agent)
        mock_agent.set_state(next_state)

        # Add task completion event
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
        await mock_agent.task_completion_queue.put(task_event)

        # Handle monitor state with timeout
        try:
            await asyncio.wait_for(mock_agent.handle(None), timeout=1.0)
        except asyncio.TimeoutError:
            pytest.fail("Monitor state timed out - possible deadlock")

        # Should transition back to start (continue processing)
        next_state = mock_agent.state.next_state(mock_agent)
        assert isinstance(next_state, StartGalaxyAgentState)
        assert mock_agent._status == "continue"

    @pytest.mark.asyncio
    async def test_agent_handles_failure(self, simple_constellation, mock_agent):
        """Test that agent handles failures properly."""
        # Setup - mock process_initial_request to fail
        mock_agent.process_initial_request = AsyncMock(
            side_effect=Exception("Test error")
        )

        # Run start state which should fail
        await mock_agent.handle(None)

        # Should transition to fail state
        assert mock_agent._status == "failed"
        next_state = mock_agent.state.next_state(mock_agent)
        mock_agent.set_state(next_state)
        assert isinstance(mock_agent.state, FailGalaxyAgentState)

        # Run fail state
        await mock_agent.handle(None)
        assert mock_agent._status == "failed"
