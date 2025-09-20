# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
GalaxyWeaverAgent - DAG-based Task Orchestration Agent

This module provides the GalaxyWeaverAgent interface for managing DAG-based task orchestration
in the Galaxy framework. The GalaxyWeaverAgent is responsible for processing user requests,
generating and updating DAGs, and managing task execution status.

Optimized for type safety, maintainability, and follows SOLID principles.
"""

import asyncio
import logging
import time
from abc import abstractmethod
from typing import Any, Dict, List, Optional, Union

from ufo.agents.agent.basic import BasicAgent
from ufo.module.context import Context

from ..core.interfaces import IRequestProcessor, IResultProcessor, IConstellationUpdater
from ..core.types import (
    TaskId,
    ConstellationId,
    ExecutionResult,
    ProcessingContext,
    TaskExecutionError,
    ConstellationError,
)
from ..constellation import TaskConstellation, TaskStar, TaskStatus
from ..constellation.enums import ConstellationState, TaskPriority


class GalaxyWeaverAgent(BasicAgent, IRequestProcessor, IResultProcessor):
    """
    GalaxyWeaverAgent - A specialized agent for DAG-based task orchestration.

    The GalaxyWeaverAgent extends BasicAgent and implements multiple interfaces:
    - IRequestProcessor: Process user requests to generate initial DAGs
    - IResultProcessor: Process task execution results and update DAGs

    Key responsibilities:
    - Process user requests to generate initial DAGs
    - Update DAGs based on task execution results
    - Manage task status and constellation state
    - Coordinate with TaskOrchestration for execution

    This class follows the Interface Segregation Principle by implementing
    focused interfaces rather than one large interface.
    """

    def __init__(self, name: str = "weaver_agent"):
        """
        Initialize the GalaxyWeaverAgent.

        :param name: Agent name (default: "weaver_agent")
        """
        super().__init__(name)
        self._current_constellation: Optional[TaskConstellation] = None
        self._status: str = "ready"  # ready, processing, finished, failed
        self._update_lock: asyncio.Lock = asyncio.Lock()
        self.logger = logging.getLogger(__name__)

    @property
    def current_constellation(self) -> Optional[TaskConstellation]:
        """Get the current constellation being managed."""
        return self._current_constellation

    @property
    def agent_status(self) -> str:
        """Get the current agent status."""
        return self._status

    @agent_status.setter
    def agent_status(self, status: str) -> None:
        """Set the agent status."""
        self._status = status

    # IRequestProcessor implementation
    async def process_request(
        self,
        request: str,
        context: Optional[ProcessingContext] = None,
    ) -> TaskConstellation:
        """
        Process a user request and generate a constellation.

        :param request: User request string
        :param context: Optional processing context
        :return: Generated constellation
        :raises ConstellationError: If constellation generation fails
        """
        # This is the interface method, delegate to the existing method for compatibility
        compat_context = None
        if context and hasattr(context, "to_dict"):
            # Convert ProcessingContext to UFO Context if needed
            pass  # For now, maintain compatibility

        try:
            return await self.process_initial_request(request, compat_context)
        except Exception as e:
            raise ConstellationError(
                "request_processing", f"Failed to process request: {e}"
            ) from e

    # IResultProcessor implementation
    async def process_result(
        self,
        result: ExecutionResult,
        constellation: TaskConstellation,
        context: Optional[ProcessingContext] = None,
    ) -> TaskConstellation:
        """
        Process a task result and potentially update the constellation.

        :param result: Task execution result
        :param constellation: Current constellation
        :param context: Optional processing context
        :return: Updated constellation
        :raises TaskExecutionError: If result processing fails
        """
        try:
            # Convert ExecutionResult to the format expected by existing methods
            task_result = {
                "task_id": result.task_id,
                "status": result.status,
                "result": result.result,
                "error": result.error,
                "metadata": result.metadata,
            }

            compat_context = None
            if context and hasattr(context, "to_dict"):
                # Convert ProcessingContext to UFO Context if needed
                pass  # For now, maintain compatibility

            return await self.process_task_result(
                task_result, constellation, compat_context
            )
        except Exception as e:
            raise TaskExecutionError(
                result.task_id, f"Failed to process result: {e}", e
            ) from e

    # Original interface methods (for backwards compatibility)
    @abstractmethod
    async def process_initial_request(
        self,
        request: str,
        context: Optional[Context] = None,
    ) -> TaskConstellation:
        """
        Process the initial user request to generate a DAG.

        :param request: User request string
        :param context: Optional UFO context for processing
        :return: TaskConstellation representing the initial DAG
        :raises ConstellationError: If constellation generation fails
        """
        pass

    @abstractmethod
    async def process_task_result(
        self,
        task_result: Dict[str, Any],
        constellation: TaskConstellation,
        context: Optional[Context] = None,
    ) -> TaskConstellation:
        """
        Process task execution results and update the DAG.

        :param task_result: Result from task execution
        :param constellation: Current constellation to update
        :param context: Optional UFO context for processing
        :return: Updated TaskConstellation
        :raises TaskExecutionError: If result processing fails
        """
        pass

    @abstractmethod
    async def should_continue(
        self,
        constellation: TaskConstellation,
        context: Optional[Context] = None,
    ) -> bool:
        """
        Determine if the session should continue based on constellation state.

        Args:
            constellation: Current constellation
            context: Optional context for decision making

        Returns:
            True if session should continue, False otherwise
        """
        pass

    async def update_constellation_with_lock(
        self,
        task_result: Dict[str, Any],
        context: Optional[Context] = None,
    ) -> TaskConstellation:
        """
        Thread-safe method to update constellation based on task results.

        Args:
            task_result: Result from task execution
            context: Optional context for processing

        Returns:
            Updated TaskConstellation
        """
        async with self._update_lock:
            if self._current_constellation is None:
                raise ValueError("No current constellation to update")

            # Only update if constellation is not finished
            if self._current_constellation.state in [
                ConstellationState.COMPLETED,
                ConstellationState.FAILED,
            ]:
                self.logger.warning(
                    "Attempted to update completed/failed constellation"
                )
                return self._current_constellation

            # Process the result and update constellation
            updated_constellation = await self.process_task_result(
                task_result, self._current_constellation, context
            )

            self._current_constellation = updated_constellation

            # Log constellation update (visualization handled by observer)
            task_id = task_result.get("task_id", "unknown")
            status = task_result.get("status", "unknown")
            self.logger.info(f"Updated constellation after task {task_id} -> {status}")

            return updated_constellation

    def validate_constellation_update(
        self,
        constellation: TaskConstellation,
        updates: Dict[str, Any],
    ) -> bool:
        """
        Validate that constellation updates only affect unexecuted tasks.

        Args:
            constellation: Constellation to validate
            updates: Proposed updates

        Returns:
            True if updates are valid, False otherwise
        """
        try:
            # Get all running and completed tasks
            executed_or_running_tasks = set()

            for task in constellation.tasks.values():
                if task.status in [TaskStatus.running, TaskStatus.completed]:
                    executed_or_running_tasks.add(task.task_id)

            # Check if any updates affect executed/running tasks
            for task_id in updates.get("modified_tasks", []):
                if task_id in executed_or_running_tasks:
                    self.logger.error(f"Cannot modify executed/running task: {task_id}")
                    return False

            # Check if any removed tasks are executed/running
            for task_id in updates.get("removed_tasks", []):
                if task_id in executed_or_running_tasks:
                    self.logger.error(f"Cannot remove executed/running task: {task_id}")
                    return False

            return True
        except Exception as e:
            self.logger.error(f"Error validating constellation update: {e}")
            return False

    def get_constellation_statistics(self) -> Dict[str, Any]:
        """
        Get current constellation statistics.

        Returns:
            Dictionary containing constellation statistics
        """
        if not self._current_constellation:
            return {"error": "No current constellation"}

        return {
            "constellation_id": self._current_constellation.constellation_id,
            "name": self._current_constellation.name,
            "state": self._current_constellation.state.value,
            "total_tasks": self._current_constellation.task_count,
            "total_dependencies": self._current_constellation.dependency_count,
            "statistics": self._current_constellation.get_statistics(),
            "agent_status": self._status,
        }

    async def reset_constellation(self) -> None:
        """Reset the current constellation and agent state."""
        async with self._update_lock:
            self._current_constellation = None
            self._status = "ready"
            self.logger.info("Constellation and agent state reset")

    # Required BasicAgent abstract methods - basic implementations
    def get_prompter(self) -> str:
        """Get the prompter for the agent."""
        return "GalaxyWeaverAgent"

    @property
    def status_manager(self):
        """Get the status manager."""
        return type(
            "StatusManager", (), {"CONTINUE": type("Status", (), {"value": "continue"})}
        )()

    async def context_provision(self) -> None:
        """Provide context for the agent."""
        pass

    def process_confirmation(self) -> None:
        """Process confirmation."""
        pass


class MockGalaxyWeaverAgent(GalaxyWeaverAgent):
    """
    Mock implementation of GalaxyWeaverAgent for testing and demonstration.

    This implementation provides basic DAG generation and update logic
    for testing the Galaxy framework without requiring actual LLM integration.
    """

    def __init__(self, name: str = "mock_weaver_agent"):
        """Initialize the MockGalaxyWeaverAgent."""
        super().__init__(name)

    def message_constructor(self) -> List[Dict[str, Union[str, List[Dict[str, str]]]]]:
        """
        Construct the message for LLM interaction.

        Returns:
            List of message dictionaries for LLM
        """
        return [
            {
                "role": "system",
                "content": "You are a mock GalaxyWeaverAgent for testing purposes.",
            },
            {
                "role": "user",
                "content": "Mock user message for testing Galaxy framework integration.",
            },
        ]

    async def process_initial_request(
        self,
        request: str,
        context: Optional[Context] = None,
    ) -> TaskConstellation:
        """
        Process initial request by generating a simple DAG based on request keywords.

        Args:
            request: User request string
            context: Optional context

        Returns:
            TaskConstellation with generated tasks
        """
        self.logger.info(f"Processing initial request: {request[:100]}...")

        # Simple keyword-based DAG generation for testing
        from ..constellation import create_simple_constellation

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

        constellation = create_simple_constellation(
            task_descriptions=tasks,
            constellation_name=f"MockDAG_{request[:20]}",
            sequential=True,
        )

        self._current_constellation = constellation
        self._status = "processing"

        self.logger.info(
            f"Generated constellation with {constellation.task_count} tasks"
        )

        return constellation

    async def process_task_result(
        self,
        task_result: Dict[str, Any],
        constellation: TaskConstellation,
        context: Optional[Context] = None,
    ) -> TaskConstellation:
        """
        Enhanced process task results with intelligent task generation based on result content.

        Args:
            task_result: Task execution result
            constellation: Current constellation
            context: Optional context

        Returns:
            Updated constellation
        """
        task_id = task_result.get("task_id")
        status = task_result.get("status")
        result_data = task_result.get("result", {})

        self.logger.info(f"Processing result for task {task_id}: {status}")

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

            # Check for data analysis results that need follow-up
            if "data_analysis" in result_data:
                analysis = result_data["data_analysis"]
                if analysis.get("complexity") == "high":
                    # Add advanced processing task
                    advanced_task = TaskStar(
                        task_id=f"advanced_processing_{int(time.time() * 1000) % 10000}",
                        description="Perform advanced data processing for high complexity data",
                        priority=TaskPriority.HIGH,
                    )
                    if advanced_task.task_id not in constellation.tasks:
                        constellation.add_task(advanced_task)
                        new_tasks_added += 1
                        self.logger.info(
                            f"Added advanced processing task: {advanced_task.task_id}"
                        )

            # Check for model training results that need evaluation
            if "model_training" in result_data:
                training_result = result_data["model_training"]
                accuracy = training_result.get("validation_accuracy", 0)

                if accuracy < 0.9:  # Low accuracy, add optimization tasks
                    optimization_task = TaskStar(
                        task_id=f"model_optimization_{int(time.time() * 1000) % 10000}",
                        description=f"Optimize model performance (current accuracy: {accuracy:.2f})",
                        priority=TaskPriority.HIGH,
                    )
                    if optimization_task.task_id not in constellation.tasks:
                        constellation.add_task(optimization_task)
                        new_tasks_added += 1
                        self.logger.info(
                            f"Added optimization task: {optimization_task.task_id}"
                        )

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

            # Check if deployment is ready
            if result_data.get("deployment_ready"):
                deploy_task = TaskStar(
                    task_id=f"deployment_pipeline_{int(time.time() * 1000) % 10000}",
                    description="Set up deployment pipeline for production",
                    priority=TaskPriority.HIGH,
                )
                if deploy_task.task_id not in constellation.tasks:
                    constellation.add_task(deploy_task)
                    new_tasks_added += 1
                    self.logger.info(f"Added deployment task: {deploy_task.task_id}")

            if new_tasks_added > 0:
                self.logger.info(
                    f"Total new tasks added based on result analysis: {new_tasks_added}"
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
                self._status = "needs_attention"
            elif completed_tasks >= total_tasks * 0.9:  # 90% completed successfully
                self._status = "finishing"
        else:
            self._status = "processing"

        return constellation

    async def should_continue(
        self,
        constellation: TaskConstellation,
        context: Optional[Context] = None,
    ) -> bool:
        """
        Determine if session should continue based on completion status.

        Args:
            constellation: Current constellation
            context: Optional context

        Returns:
            True if should continue, False if finished
        """
        if self._status in ["finished", "failed"]:
            return False

        # Continue if there are pending or ready tasks
        stats = constellation.get_statistics()
        status_counts = stats.get("task_status_counts", {})

        pending_tasks = status_counts.get("pending", 0)
        running_tasks = status_counts.get("running", 0)
        waiting_tasks = status_counts.get("waiting_dependency", 0)

        has_active_tasks = pending_tasks + running_tasks + waiting_tasks > 0
        pending_tasks = (
            constellation.task_count - stats["completed_tasks"] - stats["failed_tasks"]
        )

        return pending_tasks > 0
