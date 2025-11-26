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
import logging
import time
from typing import Dict, List, Optional, Tuple, Union

from galaxy.agents.constellation_agent_states import ConstellationAgentStatus
from galaxy.agents.processors.processor import ConstellationAgentProcessor
from galaxy.agents.prompters.base_constellation_prompter import (
    BaseConstellationPrompter,
    ConstellationPrompterFactory,
)
from galaxy.agents.schema import ConstellationAgentResponse, WeavingMode
from galaxy.client.components.types import AgentProfile
from galaxy.constellation.orchestrator.orchestrator import TaskConstellationOrchestrator
from galaxy.core.events import (
    AgentEvent,
    ConstellationEvent,
    EventType,
    TaskEvent,
    get_event_bus,
)

# Import BasicAgent and ConstellationAgentStatus here to avoid circular import at module level
from ufo.agents.agent.basic import BasicAgent
from aip.messages import Command, MCPToolInfo, ResultStatus
from ufo.module.context import Context, ContextNames

from ..constellation import TaskConstellation
from ..core.interfaces import IRequestProcessor, IResultProcessor


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

    _constellation_creation_tool_name: str = "build_constellation"

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
        self._status: str = "START"  # start, continue, finish, fail
        self.logger = logging.getLogger(__name__)

        # Add state machine support
        self.current_request: str = ""
        self._orchestrator = orchestrator

        self._task_completion_queue = asyncio.Queue()
        self._constellation_completion_queue = asyncio.Queue()

        self._context_provision_executed = False
        self._event_bus = get_event_bus()

        self.prompter = None  # Will be initialized when weaving_mode is known

        # Initialize with start state
        from .constellation_agent_states import StartConstellationAgentState

        self.set_state(StartConstellationAgentState())

    @property
    def current_constellation(self) -> Optional[TaskConstellation]:
        """
        Get the current constellation being managed.

        :return: Current constellation instance or None
        """
        return self._current_constellation

    # ==================== Private Helper Methods ====================

    async def _initialize_prompter(self, context: Context) -> None:
        """
        Initialize prompter based on weaving mode.

        :param context: Processing context containing weaving mode
        """
        weaving_mode = context.get(ContextNames.WEAVING_MODE)
        self.prompter = self.get_prompter(weaving_mode)

    async def _ensure_context_provision(self, context: Context) -> None:
        """
        Ensure context provision is executed once for creation.

        :param context: Processing context
        """
        if not self._context_provision_executed:
            await self.context_provision(context=context)
            self._context_provision_executed = True

    async def _create_and_process(self, context: Context) -> Tuple[float, float, float]:
        """
        Create processor and execute processing.

        :param context: Processing context
        :return: Tuple of (start_time, end_time, duration)
        """
        self.processor = ConstellationAgentProcessor(agent=self, global_context=context)

        start_time = time.time()
        await self.processor.process()
        end_time = time.time()

        return start_time, end_time, end_time - start_time

    def _update_agent_status(self) -> None:
        """
        Update agent status from processor context.
        """
        self.status = self.processor.processing_context.get_local("status").upper()
        self.logger.info(f"Constellation agent status updated to: {self.status}")

    async def _validate_and_update_constellation(
        self, constellation: TaskConstellation
    ) -> TaskConstellation:
        """
        Validate constellation DAG structure and update status if invalid.

        :param constellation: The constellation to validate
        :return: The validated constellation
        """
        is_dag, errors = constellation.validate_dag()

        if not is_dag:
            self.logger.error(f"The created constellation is not a valid DAG: {errors}")
            self.status = ConstellationAgentStatus.FAIL.value

        self._current_constellation = constellation
        return constellation

    def _create_timing_info(
        self, start_time: float, end_time: float, duration: float
    ) -> Dict[str, float]:
        """
        Create timing information dictionary.

        :param start_time: Processing start time
        :param end_time: Processing end time
        :param duration: Processing duration
        :return: Dictionary containing timing information
        """
        return {
            "processing_start_time": start_time,
            "processing_end_time": end_time,
            "processing_duration": duration,
        }

    async def _sync_constellation_to_mcp(
        self, constellation: TaskConstellation, context: Context
    ) -> None:
        """
        Sync constellation to MCP server.

        :param constellation: The constellation to sync
        :param context: Processing context
        """
        await context.command_dispatcher.execute_commands(
            commands=[
                Command(
                    tool_name="build_constellation",
                    parameters={
                        "config": constellation.to_basemodel(),
                        "clear_existing": True,
                    },
                    tool_type="action",
                )
            ]
        )

    def _log_constellation_state(
        self, constellation: TaskConstellation, prefix: str = ""
    ) -> None:
        """
        Log constellation state information.

        :param constellation: The constellation to log
        :param prefix: Prefix for log messages
        """
        self.logger.info(f"{prefix}Task ID: {constellation.tasks.keys()}")
        self.logger.info(f"{prefix}Dependency ID: {constellation.dependencies.keys()}")

    def _log_task_statuses(
        self, constellation: TaskConstellation, task_ids: List[str], stage: str
    ) -> None:
        """
        Log status for specific tasks.

        :param constellation: The constellation containing the tasks
        :param task_ids: List of task IDs to log
        :param stage: Stage description (e.g., 'before editing', 'after editing')
        """
        for tid in task_ids:
            task = constellation.get_task(tid)
            if task:
                self.logger.info(f"📊 Status for task {stage} {tid}: {task.status}")

    async def _publish_constellation_modified_event(
        self,
        before_constellation: TaskConstellation,
        after_constellation: TaskConstellation,
        task_ids: List[str],
        timing_info: Dict[str, float],
    ) -> None:
        """
        Publish constellation modified event.

        :param before_constellation: The constellation before modification
        :param after_constellation: The constellation after modification
        :param task_ids: List of task IDs that were modified
        :param timing_info: Timing information for the modification
        """
        await self._event_bus.publish_event(
            ConstellationEvent(
                event_type=EventType.CONSTELLATION_MODIFIED,
                source_id=self.name,
                timestamp=time.time(),
                data={
                    "old_constellation": before_constellation,
                    "new_constellation": after_constellation,
                    "modification_type": f"Edited by {self.name}",
                    "on_task_id": task_ids,
                    **timing_info,
                },
                constellation_id=after_constellation.constellation_id,
                constellation_state=(
                    after_constellation.state.value
                    if after_constellation.state
                    else "unknown"
                ),
            )
        )

    async def _handle_constellation_completion(
        self,
        before_constellation: TaskConstellation,
        after_constellation: TaskConstellation,
    ) -> None:
        """
        Handle constellation completion logic.

        :param before_constellation: The constellation before completion
        :param after_constellation: The constellation after completion
        """
        try:
            await asyncio.wait_for(
                self.constellation_completion_queue.get(), timeout=1.0
            )

            self.logger.info(
                f"The old constellation {before_constellation.constellation_id} is completed."
            )

            if (
                self.status == ConstellationAgentStatus.CONTINUE.value
                and not after_constellation.is_complete()
            ):
                self.logger.info(
                    f"New update to the constellation {before_constellation.constellation_id} needed, restart the orchestration"
                )
                self.status = ConstellationAgentStatus.START.value

        except asyncio.TimeoutError:
            pass

    # ==================== Public Interface Methods ====================

    # IRequestProcessor implementation
    async def process_creation(
        self,
        context: Context,
    ) -> Tuple[TaskConstellation, Dict[str, float]]:
        """
        Process a user request and generate a constellation.

        :param request: User request string
        :param context: Optional processing context
        :return: Tuple of (Generated constellation, processing timing info)
        :raises ConstellationError: If constellation generation fails
        """
        # Initialize
        await self._initialize_prompter(context)
        await self._ensure_context_provision(context)

        # Process
        start_time, end_time, duration = await self._create_and_process(context)

        # Update status and get constellation
        self._update_agent_status()
        created_constellation = context.get(ContextNames.CONSTELLATION)

        # Validate
        if created_constellation:
            await self._validate_and_update_constellation(created_constellation)

        # Return result with timing
        return self._current_constellation, self._create_timing_info(
            start_time, end_time, duration
        )

    # IResultProcessor implementation
    async def process_editing(
        self,
        context: Context = None,
        task_ids: Optional[List[str]] = None,
        before_constellation: Optional[TaskConstellation] = None,
    ) -> TaskConstellation:
        """
        Process task completion events and potentially update the constellation.

        :param context: Optional processing context
        :param task_ids: List of task IDs that were just completed
        :param before_constellation: The constellation before editing
        :return: Updated constellation
        :raises TaskExecutionError: If result processing fails
        """
        # Initialize
        await self._initialize_prompter(context)
        await self.context_provision(context=context)

        # Prepare constellation
        if not before_constellation:
            before_constellation = context.get(ContextNames.CONSTELLATION)
        else:
            context.set(ContextNames.CONSTELLATION, before_constellation)

        task_ids = task_ids or []

        # Log and sync before state
        self.logger.debug(
            f"Tasks {task_ids} marked as completed, Agent's constellation updated, completed tasks ids: "
            f"{[t.task_id for t in before_constellation.get_completed_tasks()]}"
        )
        await self._sync_constellation_to_mcp(before_constellation, context)
        self._log_constellation_state(
            before_constellation, "Task ID for constellation before editing: "
        )
        self._log_task_statuses(before_constellation, task_ids, "before editing")
        self._log_constellation_state(
            before_constellation, "Dependency ID for constellation before editing: "
        )

        # Process
        start_time, end_time, duration = await self._create_and_process(context)

        # Update status and get constellation
        self._update_agent_status()
        after_constellation = context.get(ContextNames.CONSTELLATION)

        # Log after state
        self._log_task_statuses(after_constellation, task_ids, "after editing")

        # Handle completion
        await self._handle_constellation_completion(
            before_constellation, after_constellation
        )

        # Validate
        await self._validate_and_update_constellation(after_constellation)

        # Sync and publish event
        await self._sync_constellation_to_mcp(after_constellation, context)
        self._log_constellation_state(
            after_constellation, "Task ID for constellation after editing: "
        )
        self._log_constellation_state(
            after_constellation, "Dependency ID for constellation after editing: "
        )

        await self._publish_constellation_modified_event(
            before_constellation,
            after_constellation,
            task_ids,
            self._create_timing_info(start_time, end_time, duration),
        )

        return after_constellation

    async def context_provision(
        self, context: Context, mask_creation: bool = True
    ) -> None:
        """
        Provide the context for the agent.

        :param context: The context for the agent
        :param mask_creation: Whether to mask the tool for creation of constellation
        """
        await self._load_mcp_context(context, mask_creation)

    async def _load_mcp_context(
        self, context: Context, mask_creation: bool = True
    ) -> None:
        """
        Load MCP context information for the current application.

        :param context: The context for the agent
        :param mask_creation: Whether to mask the tool for creation of constellation
        """

        self.logger.info("Loading MCP tool information...")
        result = await context.command_dispatcher.execute_commands(
            [
                Command(
                    tool_name="list_tools",
                    parameters={
                        "tool_type": "action",
                    },
                    tool_type="action",
                )
            ]
        )

        if result[0].status == ResultStatus.FAILURE:
            tool_list = []
            self.logger.warning(
                f"Failed to load MCP tool information: {result[0].result}"
            )
        else:
            tool_list = result[0].result if result else []

        # Mask the creation tool for the prompt
        if mask_creation:
            tool_list = [
                tool
                for tool in tool_list
                if tool.get("tool_name") != self._constellation_creation_tool_name
            ]

        tool_name_list = (
            [tool.get("tool_name") for tool in tool_list if tool.get("tool_name")]
            if tool_list
            else []
        )

        self.logger.info(f"Loaded tool list: {tool_name_list} for {self.name}.")

        tools_info = [MCPToolInfo(**tool) for tool in tool_list]
        self.logger.debug(f"Loaded tool tools_info: {tools_info}.")

        self.prompter.create_api_prompt_template(tools=tools_info)

    def get_prompter(self, weaving_mode: WeavingMode) -> BaseConstellationPrompter:
        """
        Get the prompter for the agent using factory pattern.

        :param weaving_mode: The weaving mode for the agent
        :return: The prompter for the agent
        """
        self.logger.info(f"Creating prompter for {weaving_mode}")
        return ConstellationPrompterFactory.create_prompter(weaving_mode=weaving_mode)

    def message_constructor(
        self,
        request: str,
        device_info: Dict[str, AgentProfile],
        constellation: TaskConstellation,
    ) -> List[Dict[str, Union[str, List[Dict[str, str]]]]]:
        """
        Construct the message for LLM interaction.

        :param request: The user request
        :param device_info: Information about the user's device
        :param constellation: The current task constellation
        :return: A list of message dictionaries for LLM interaction
        """

        if not self.prompter:
            raise ValueError("Prompter is not initialized")

        system_message = self.prompter.system_prompt_construction()
        user_message = self.prompter.user_content_construction(
            request=request, device_info=device_info, constellation=constellation
        )

        prompt = self.prompter.prompt_construction(system_message, user_message)

        return prompt

    async def process_confirmation(self, context: Context = None) -> bool:
        """
        Process confirmation for constellation operations.

        :param context: Processing context
        :return: True if confirmed, False otherwise
        """
        # For now, always confirm for constellation operations
        # This can be extended with actual confirmation logic
        return True

    def print_response(
        self, response: ConstellationAgentResponse, print_action: bool = False
    ) -> None:
        """
        Publish agent response as an event instead of directly printing.
        :param response: The ConstellationAgentResponse object to display
        :param print_action: Flag to indicate if action details should be printed
        """
        # Publish agent response event
        event = AgentEvent(
            event_type=EventType.AGENT_RESPONSE,
            source_id=self.name,
            timestamp=time.time(),
            data={},
            agent_name=self.name,
            agent_type="constellation",
            output_type="response",
            output_data={
                **response.model_dump(),
                "print_action": print_action,
            },
        )

        # Publish event asynchronously (non-blocking)
        asyncio.create_task(get_event_bus().publish_event(event))

    @property
    def default_state(self):
        """
        Get the default state of the Constellation Agent.

        :return: The default StartConstellationAgentState
        """
        from .constellation_agent_states import StartConstellationAgentState

        return StartConstellationAgentState()

    @property
    def status_manager(self):
        """Get the status manager."""

        return ConstellationAgentStatus

    @property
    def orchestrator(self) -> TaskConstellationOrchestrator:
        """
        The orchestrator for managing constellation tasks.
        :return: The task constellation orchestrator.
        """
        return self._orchestrator

    @property
    def task_completion_queue(self) -> asyncio.Queue[TaskEvent]:
        """
        Get the task completion queue.
        :return: The task completion queue.
        """
        return self._task_completion_queue

    @property
    def constellation_completion_queue(self) -> asyncio.Queue[ConstellationEvent]:
        """
        Get the constellation completion queue.
        :return: The constellation completion queue.
        """
        return self._constellation_completion_queue

    async def add_task_completion_event(self, event: TaskEvent) -> None:
        """
        Add a task event to the task completion queue.

        :param event: TaskEvent instance to add to the queue
        :raises TypeError: If the event is not a TaskEvent instance
        :raises RuntimeError: If failed to add event to queue
        """
        if not isinstance(event, TaskEvent):
            raise TypeError(
                f"Expected TaskEvent instance, got {type(event).__name__}. "
                f"Only TaskEvent instances can be added to the task completion queue."
            )

        if event.event_type not in [
            EventType.TASK_COMPLETED,
            EventType.TASK_FAILED,
        ]:
            raise TypeError(
                f"Expected TaskEvent with event_type in [TASK_COMPLETED, TASK_FAILED], "
                f"got {event.event_type}."
            )

        try:
            await self._task_completion_queue.put(event)
            self.logger.info(
                f"Added task event for task '{event.task_id}' with status '{event.status}' to completion queue"
            )
        except asyncio.QueueFull as e:
            self.logger.error(f"Task completion queue is full: {str(e)}", exc_info=True)
            raise RuntimeError(f"Task completion queue is full: {str(e)}") from e
        except Exception as e:
            self.logger.error(
                f"Unexpected error adding task event to queue: {str(e)}", exc_info=True
            )
            raise RuntimeError(f"Failed to add task event to queue: {str(e)}") from e

    async def add_constellation_completion_event(
        self, event: ConstellationEvent
    ) -> None:
        """
        Add a constellation event to the constellation completion queue.

        :param event: ConstellationEvent instance to add to the queue
        :raises TypeError: If the event is not a ConstellationEvent instance
        :raises RuntimeError: If failed to add event to queue
        """
        if not isinstance(event, ConstellationEvent):
            raise TypeError(
                f"Expected ConstellationEvent instance, got {type(event).__name__}. "
                f"Only ConstellationEvent instances can be added to the constellation completion queue."
            )

        if event.event_type != EventType.CONSTELLATION_COMPLETED:
            raise TypeError(
                f"Expected ConstellationEvent with event_type of [CONSTELLATION_COMPLETED], "
                f"got {event.event_type}."
            )

        try:
            await self._constellation_completion_queue.put(event)
            self.logger.info(
                f"Added constellation event for constellation '{event.constellation_id}' "
                f"with state '{event.constellation_state}' to completion queue"
            )
        except asyncio.QueueFull as e:
            self.logger.error(
                f"Constellation completion queue is full: {str(e)}", exc_info=True
            )
            raise RuntimeError(
                f"Constellation completion queue is full: {str(e)}"
            ) from e
        except Exception as e:
            self.logger.error(
                f"Unexpected error adding constellation event to queue: {str(e)}",
                exc_info=True,
            )
            raise RuntimeError(
                f"Failed to add constellation event to queue: {str(e)}"
            ) from e
