#!/usr/bin/env python3
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Mock implementations for Galaxy Constellation framework testing.

This module provides mock implementations of Galaxy framework components
for testing purposes, without requiring actual LLM integration or external dependencies.
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Union

from galaxy.agents.constellation_agent import ConstellationAgent
from galaxy.constellation.orchestrator.orchestrator import (
    TaskConstellationOrchestrator,
)
from galaxy.core.events import get_event_bus, ConstellationEvent, EventType
from galaxy.constellation import TaskConstellation, TaskStar
from galaxy.constellation.enums import ConstellationState, TaskPriority
from ufo.module.context import Context, ContextNames


def create_simple_test_constellation(
    task_descriptions: List[str],
    constellation_name: str = "TestConstellation",
    sequential: bool = True,
) -> TaskConstellation:
    """
    Create a simple constellation for testing purposes.

    :param task_descriptions: List of task descriptions
    :param constellation_name: Name for the constellation
    :param sequential: Whether tasks should be sequential
    :return: Created constellation
    """
    constellation = TaskConstellation(
        constellation_id=constellation_name,
        name=constellation_name,
    )

    tasks = []
    for i, desc in enumerate(task_descriptions):
        task = TaskStar(
            task_id=f"task_{i+1}",
            description=desc,
            priority=TaskPriority.MEDIUM,
        )
        tasks.append(task)
        constellation.add_task(task)

    # Add sequential dependencies if requested
    if sequential and len(tasks) > 1:
        from galaxy.constellation.task_star_line import TaskStarLine

        for i in range(len(tasks) - 1):
            dependency = TaskStarLine(
                from_task_id=tasks[i].task_id, to_task_id=tasks[i + 1].task_id
            )
            constellation.add_dependency(dependency)

    return constellation


class MockConstellationAgent(ConstellationAgent):
    """
    Mock implementation of Constellation for testing and demonstration.

    This implementation provides basic DAG generation and update logic
    for testing the Galaxy framework without requiring actual LLM integration.
    """

    def __init__(
        self,
        orchestrator: TaskConstellationOrchestrator,
        name: str = "mock_constellation_agent",
    ):
        """
        Initialize the MockConstellationAgent.

        :param orchestrator: Task orchestrator instance
        :param name: Agent name (default: "mock_constellation_agent")
        """
        super().__init__(orchestrator, name)

    def message_constructor(self) -> List[Dict[str, Union[str, List[Dict[str, str]]]]]:
        """
        Construct the message for LLM interaction.

        Returns:
            List of message dictionaries for LLM
        """
        return [
            {
                "role": "system",
                "content": "You are a mock Constellation for testing purposes.",
            },
            {
                "role": "user",
                "content": "Mock user message for testing Galaxy framework integration.",
            },
        ]

    async def process_confirmation(self, context: Context) -> bool:
        """
        Mock process confirmation.

        :param context: Processing context
        :return: Always returns True for mock
        """
        return True

    async def process_creation(
        self,
        context: Context,
    ) -> TaskConstellation:
        """
        Process a user request and generate a constellation (Mock implementation).

        :param context: Processing context
        :return: Generated constellation
        :raises ConstellationError: If constellation generation fails
        """
        # Get request from context or use a default
        request = "mock request"
        if context and hasattr(context, "get"):
            try:
                request = context.get(ContextNames.REQUEST) or "mock request"
            except (TypeError, AttributeError):
                request = "mock request"

        self.logger.info(f"Mock processing creation request: {request[:100]}...")

        # Generate tasks based on request content
        if "complex" in request.lower():
            tasks = [
                "Analyze user request and identify requirements",
                "Break down complex requirements into subtasks",
                "Design system architecture",
                "Implement core functionality",
                "Test and validate implementation",
                "Deploy and monitor system",
            ]
        elif "parallel" in request.lower():
            tasks = [
                "Initialize parallel processing framework",
                "Process data stream A",
                "Process data stream B",
                "Process data stream C",
                "Aggregate and finalize results",
            ]
        else:
            tasks = [
                "Understand user request",
                "Plan execution strategy",
                "Execute primary task",
                "Validate results",
            ]

        constellation = create_simple_test_constellation(
            task_descriptions=tasks,
            constellation_name=f"MockDAG_{request[:20]}",
            sequential=True,
        )

        self._current_constellation = constellation
        self.status = "CONTINUE"

        self.logger.info(
            f"Generated mock constellation with {constellation.task_count} tasks"
        )

        return constellation

    async def process_editing(
        self,
        context: Context = None,
    ) -> TaskConstellation:
        """
        Process a task result and potentially update the constellation (Mock implementation).

        :param context: Processing context
        :return: Updated constellation
        :raises TaskExecutionError: If result processing fails
        """
        self.logger.info("Mock processing editing request...")

        if not self._current_constellation:
            self.logger.warning("No current constellation to edit in mock agent")
            return await self.process_creation(context)

        # Store before constellation for event publishing
        before_constellation = self._current_constellation

        # Mock task result processing
        task_result = {
            "task_id": "mock_task",
            "status": "completed",
            "result": {"recommendations": ["optimize_performance", "add_monitoring"]},
        }

        constellation = self._current_constellation
        task_id = task_result.get("task_id")
        status = task_result.get("status")
        result_data = task_result.get("result", {})

        self.logger.info(f"Mock processing result for task {task_id}: {status}")

        # Enhanced logic for dynamic task generation based on result content
        if status == "completed" and isinstance(result_data, dict):
            new_tasks_added = 0

            # Check for specific triggers in the result
            if "trigger_tasks" in result_data:
                # Explicit task triggers from result
                for task_name in result_data["trigger_tasks"]:
                    new_task_id = f"{task_name}_{int(time.time() * 1000) % 10000}"
                    new_task = TaskStar(
                        task_id=new_task_id,
                        description=f"Execute {task_name.replace('_', ' ')} as triggered by {task_id}",
                        priority=TaskPriority.MEDIUM,
                    )

                    if new_task_id not in constellation.tasks:
                        constellation.add_task(new_task)
                        new_tasks_added += 1
                        self.logger.info(f"Added triggered task: {new_task_id}")

            # Check for recommendations in results
            if "recommendations" in result_data:
                for i, recommendation in enumerate(
                    result_data["recommendations"][:2]
                ):  # Limit to 2
                    rec_task = TaskStar(
                        task_id=f"implement_{recommendation}_{int(time.time() * 1000) % 10000}",
                        description=f"Implement recommendation: {recommendation.replace('_', ' ')}",
                        priority=TaskPriority.MEDIUM,
                    )
                    if rec_task.task_id not in constellation.tasks:
                        constellation.add_task(rec_task)
                        new_tasks_added += 1
                        self.logger.info(
                            f"Added recommendation task: {rec_task.task_id}"
                        )

            if new_tasks_added > 0:
                self.logger.info(
                    f"Total new tasks added based on mock result analysis: {new_tasks_added}"
                )

        # Handle error cases
        elif status == "failed" or "error" in str(result_data).lower():
            # Add error recovery task
            recovery_task = TaskStar(
                task_id=f"recovery_{task_id}_{int(time.time() * 1000) % 10000}",
                description=f"Handle error recovery for {task_id}",
                priority=TaskPriority.HIGH,
            )

            # Only add if not already exists and constellation is not finished
            if (
                recovery_task.task_id not in constellation.tasks
                and constellation.state
                not in [ConstellationState.COMPLETED, ConstellationState.FAILED]
            ):
                constellation.add_task(recovery_task)
                self.logger.info(f"Added recovery task: {recovery_task.task_id}")

        # Update agent status based on constellation state
        stats = constellation.get_statistics()
        status_counts = stats.get("task_status_counts", {})

        completed_tasks = status_counts.get("completed", 0)
        failed_tasks = status_counts.get("failed", 0)
        total_tasks = constellation.task_count

        if (
            completed_tasks + failed_tasks >= total_tasks * 0.8
        ):  # 80% completion threshold
            if failed_tasks > completed_tasks * 0.3:  # More than 30% failed
                self.status = "FAIL"
            elif completed_tasks >= total_tasks * 0.9:  # 90% completed successfully
                self.status = "FINISH"
            else:
                self.status = "CONTINUE"
        else:
            self.status = "CONTINUE"

        # Publish DAG Modified Event for mock agent
        await self._event_bus.publish_event(
            ConstellationEvent(
                event_type=EventType.CONSTELLATION_MODIFIED,
                source_id=self.name,
                timestamp=time.time(),
                data={
                    "old_constellation": before_constellation,
                    "new_constellation": constellation,
                    "modification_type": "mock_agent_processing",
                },
                constellation_id=constellation.constellation_id,
                constellation_state=(
                    constellation.state.value if constellation.state else "unknown"
                ),
            )
        )

        return constellation


class MockTaskConstellationOrchestrator:
    """Mock orchestrator for testing."""

    def __init__(self, device_manager=None, enable_logging=True):
        self.device_manager = device_manager
        self.enable_logging = enable_logging
        self.constellation = None

    async def execute_constellation(self, constellation):
        """Mock execution of constellation."""
        if self.enable_logging:
            print(
                f"🎭 Mock orchestrator executing constellation: {constellation.constellation_id}"
            )

        # Mock execution by just returning success
        return {"status": "completed", "tasks_executed": constellation.task_count}
