# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Constellation - DAG-based Task Orchestration Agent

This module provides the Constellation interface for managing DAG-based task orchestration
in the Galaxy framework. The Constellation is responsible for processing user requests,
generating and updating DAGs, and managing task execution status.

Optimized for type safety, maintainability, and follows SOLID principles.
"""

import asyncio
import copy
import logging
import time
from typing import Any, Dict, List, Optional, Union

from ufo.agents.agent.basic import BasicAgent
from ufo.galaxy.agents.processors.processor import ConstellationAgentProcessor
from ufo.galaxy.constellation.orchestrator.orchestrator import (
    TaskConstellationOrchestrator,
)
from ufo.module.context import Context

from ..core.interfaces import IRequestProcessor, IResultProcessor
from ..core.types import ProcessingContext
from ..constellation import TaskConstellation, TaskStar
from ..constellation.enums import ConstellationState, TaskPriority


class ConstellationAgent(BasicAgent, IRequestProcessor, IResultProcessor):
    """
    Constellation - A specialized agent for DAG-based task orchestration.

    The Constellation extends BasicAgent and implements multiple interfaces:
    - IRequestProcessor: Process user requests to generate initial DAGs
    - IResultProcessor: Process task execution results and update DAGs

    Key responsibilities:
    - Process user requests to generate initial DAGs
    - Update DAGs based on task execution results
    - Manage task status and constellation state
    - Coordinate with TaskConstellationOrchestrator for execution

    This class follows the Interface Segregation Principle by implementing
    focused interfaces rather than one large interface.
    """

    def __init__(
        self,
        orchestrator: TaskConstellationOrchestrator,
        name: str = "constellation_agent",
    ):
        """
        Initialize the Constellation.

        :param name: Agent name (default: "constellation_agent")
        :param orchestrator: Task orchestrator instance
        """

        super().__init__(name)
        self._current_constellation: Optional[TaskConstellation] = None
        self._status: str = "start"  # ready, processing, finished, failed
        self.logger = logging.getLogger(__name__)

        # Add state machine support
        self.task_completion_queue: asyncio.Queue = asyncio.Queue()
        self.current_request: str = ""
        self._orchestrator = orchestrator

        # Initialize with start state
        from .constellation_agent_states import StartConstellationAgentState

        self.set_state(StartConstellationAgentState())

    @property
    def current_constellation(self) -> Optional[TaskConstellation]:
        """Get the current constellation being managed."""
        return self._current_constellation

    # IRequestProcessor implementation
    async def process_creation(
        self,
        context: Optional[ProcessingContext] = None,
    ) -> TaskConstellation:
        """
        Process a user request and generate a constellation.

        :param request: User request string
        :param context: Optional processing context
        :return: Generated constellation
        :raises ConstellationError: If constellation generation fails
        """

        self.processor = ConstellationAgentProcessor(agent=self, global_context=context)
        # self.processor = HostAgentProcessor(agent=self, context=context)
        await self.processor.process()
        constellation_string = self.processor.processing_context.get_local(
            "constellation_string"
        )

        self._current_constellation = (
            await self._orchestrator.create_constellation_from_llm(constellation_string)
        )

        is_dag, errors = self._current_constellation.validate_dag()
        self.status = self.processor.processing_context.get_local("status").upper()

        if not is_dag:
            self.logger.error(f"The created constellation is not a valid DAG: {errors}")
            self.status = "FAIL"

        # Sync the status with the processor.

        self.logger.info(f"Host agent status updated to: {self.status}")
        return self._current_constellation

    # IResultProcessor implementation
    async def process_editing(
        self,
        context: Optional[ProcessingContext] = None,
    ) -> TaskConstellation:
        """
        Process a task result and potentially update the constellation.

        :param result: Task execution result
        :param context: Optional processing context
        :return: Updated constellation
        :raises TaskExecutionError: If result processing fails
        """

        self.processor = ConstellationAgentProcessor(agent=self, global_context=context)
        await self.processor.process()

        # Sync the status with the processor.
        self.status = self.processor.processing_context.get_local("status").upper()
        self.logger.info(f"Host agent status updated to: {self.status}")

        old_constellation = copy.deepcopy(self._current_constellation)

        update_string = self.processor.processing_context.get_local("editing")

        updated_constellation = await self._orchestrator.modify_constellation_with_llm(
            self._current_constellation, update_string
        )

        is_dag, errors = updated_constellation.validate_dag()

        if not is_dag:
            self.logger.error(f"The created constellation is not a valid DAG: {errors}")
            self.status = "FAIL"

        if old_constellation.is_complete():
            self.logger.info(
                f"The old constellation {old_constellation.constellation_id} is completed."
            )
            # IMPORTANT: Restart the constellation orchestration when there is new update.
            if self.status == "CONTINUE":
                self.logger.info(
                    f"New update to the constellation {self._current_constellation.constellation_id} needed, restart the orchestration"
                )
                self.status = "START"

        self._current_constellation = updated_constellation

        return updated_constellation

    # Required BasicAgent abstract methods - basic implementations
    def get_prompter(self) -> str:
        """Get the prompter for the agent."""
        return "Constellation"

    @property
    def status_manager(self):
        """Get the status manager."""
        from .constellation_agent_states import ConstellationAgentStateManager

        return ConstellationAgentStateManager()

    @property
    def orchestrator(self) -> TaskConstellationOrchestrator:
        """
        The orchestrator for managing constellation tasks.
        :return: The task constellation orchestrator.
        """
        return self._orchestrator


class MockConstellationAgent(ConstellationAgent):
    """
    Mock implementation of Constellation for testing and demonstration.

    This implementation provides basic DAG generation and update logic
    for testing the Galaxy framework without requiring actual LLM integration.
    """

    def __init__(self, name: str = "mock_weaver_agent"):
        """Initialize the MockConstellation."""
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
                "content": "You are a mock Constellation for testing purposes.",
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
