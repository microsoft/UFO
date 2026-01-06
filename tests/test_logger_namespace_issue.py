# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Test to verify the logger namespace issue in real Galaxy session.
"""

import asyncio
import logging
import pytest
import time
from unittest.mock import Mock, AsyncMock

from galaxy.session.observers.base_observer import ConstellationProgressObserver
from galaxy.agents.constellation_agent import ConstellationAgent
from galaxy.core.events import TaskEvent, EventType
from galaxy.constellation.orchestrator.orchestrator import (
    TaskConstellationOrchestrator,
)


class TestLoggerNamespaceIssue:
    """Test class to verify the logger namespace issue."""

    @pytest.fixture
    def task_event(self):
        """Create a test task event."""
        return TaskEvent(
            event_type=EventType.TASK_COMPLETED,
            source_id="test_source",
            timestamp=time.time(),
            data={"constellation_id": "test_constellation"},
            task_id="task-collect-logs-2",
            status="completed",
            result={"success": True},
            error=None,
        )

    @pytest.fixture
    def mock_orchestrator(self):
        """Create a mock orchestrator."""
        orchestrator = Mock(spec=TaskConstellationOrchestrator)
        orchestrator.start = AsyncMock()
        orchestrator.stop = AsyncMock()
        return orchestrator

    @pytest.mark.asyncio
    async def test_logger_namespace_issue_simulation(
        self, mock_orchestrator, task_event, caplog
    ):
        """Simulate the exact logger configuration from the real test."""

        print(f"\n=== SIMULATING REAL TEST LOGGER CONFIGURATION ===")

        # Reset caplog to capture all logs
        caplog.set_level(logging.DEBUG)
        caplog.clear()

        # Create constellation agent and observer
        constellation_agent = ConstellationAgent(orchestrator=mock_orchestrator)
        observer = ConstellationProgressObserver(agent=constellation_agent)

        print(f"Observer logger name: {observer.logger.name}")
        print(f"Agent logger name: {constellation_agent.logger.name}")

        # Simulate the EXACT logger configuration from the real test
        # Only set up logging for "ufo.galaxy.session" (NOT for agents!)
        session_logger = logging.getLogger("ufo.galaxy.session")
        session_logger.setLevel(logging.DEBUG)

        # Add console handler (this is what the real test does)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        console_handler.setFormatter(formatter)
        session_logger.addHandler(console_handler)

        print(f"\nAfter setting up session logger:")
        print(f"Session logger level: {session_logger.level}")
        print(f"Session logger effective level: {session_logger.getEffectiveLevel()}")
        print(f"Observer logger effective level: {observer.logger.getEffectiveLevel()}")
        print(
            f"Agent logger effective level: {constellation_agent.logger.getEffectiveLevel()}"
        )

        # Now test the actual flow
        await observer.on_event(task_event)

        # Check what was captured
        observer_logs = [
            record for record in caplog.records if "Task progress:" in record.message
        ]
        agent_logs = [
            record
            for record in caplog.records
            if "Added task event for task" in record.message
        ]

        print(f"\n=== CAPTURED LOGS ===")
        for i, record in enumerate(caplog.records):
            print(f"{i+1}. [{record.levelname}] {record.name} - {record.message}")

        print(f"\nObserver logs: {len(observer_logs)}")
        print(f"Agent logs: {len(agent_logs)}")

        # Here's the problem!
        if len(observer_logs) > 0 and len(agent_logs) == 0:
            print("❌ ISSUE CONFIRMED: Logger namespace mismatch!")
            print("   Observer logs appear (under 'ufo.galaxy.session.observers')")
            print(
                "   Agent logs missing (under 'ufo.galaxy.agents.constellation_agent')"
            )
            print("   The test only configures 'ufo.galaxy.session' logger!")

        # Clean up
        session_logger.removeHandler(console_handler)

    @pytest.mark.asyncio
    async def test_fix_by_configuring_agent_logger(
        self, mock_orchestrator, task_event, caplog
    ):
        """Test the fix by properly configuring the agent logger."""

        print(f"\n=== TESTING THE FIX ===")

        caplog.set_level(logging.DEBUG)
        caplog.clear()

        # Create constellation agent and observer
        constellation_agent = ConstellationAgent(orchestrator=mock_orchestrator)
        observer = ConstellationProgressObserver(agent=constellation_agent)

        # Configure session logger (like the real test does)
        session_logger = logging.getLogger("ufo.galaxy.session")
        session_logger.setLevel(logging.DEBUG)

        # THE FIX: Also configure the agent logger!
        agent_logger = logging.getLogger("ufo.galaxy.agents")
        agent_logger.setLevel(logging.DEBUG)

        # Or more specifically:
        constellation_agent_logger = logging.getLogger(
            "ufo.galaxy.agents.constellation_agent"
        )
        constellation_agent_logger.setLevel(logging.DEBUG)

        # Add console handlers
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        console_handler.setFormatter(formatter)

        session_logger.addHandler(console_handler)
        agent_logger.addHandler(console_handler)

        print(f"After fix:")
        print(f"Session logger effective level: {session_logger.getEffectiveLevel()}")
        print(f"Observer logger effective level: {observer.logger.getEffectiveLevel()}")
        print(
            f"Agent logger effective level: {constellation_agent.logger.getEffectiveLevel()}"
        )

        # Test the flow
        await observer.on_event(task_event)

        # Check results
        observer_logs = [
            record for record in caplog.records if "Task progress:" in record.message
        ]
        agent_logs = [
            record
            for record in caplog.records
            if "Added task event for task" in record.message
        ]

        print(f"\n=== CAPTURED LOGS AFTER FIX ===")
        for i, record in enumerate(caplog.records):
            print(f"{i+1}. [{record.levelname}] {record.name} - {record.message}")

        print(f"\nObserver logs: {len(observer_logs)}")
        print(f"Agent logs: {len(agent_logs)}")

        if len(observer_logs) > 0 and len(agent_logs) > 0:
            print("✅ FIX WORKS: Both observer and agent logs appear!")
        else:
            print("❌ Fix didn't work as expected")

        # Clean up
        session_logger.removeHandler(console_handler)
        agent_logger.removeHandler(console_handler)

    def test_suggest_minimal_fix(self):
        """Suggest the minimal fix for the real test."""

        print(f"\n=== SUGGESTED FIX FOR REAL TEST ===")
        print("In test_real_galaxy_session_integration.py, after line 299:")
        print("session_logger.addHandler(console_handler)")
        print("")
        print("ADD THESE LINES:")
        print("# Also configure agent loggers to capture ConstellationAgent logs")
        print("agent_logger = logging.getLogger('ufo.galaxy.agents')")
        print("agent_logger.setLevel(logging.DEBUG)")
        print("agent_logger.addHandler(console_handler)")
        print("")
        print("And in the cleanup section after line 333:")
        print("session_logger.removeHandler(console_handler)")
        print("")
        print("ADD:")
        print("agent_logger.removeHandler(console_handler)")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
