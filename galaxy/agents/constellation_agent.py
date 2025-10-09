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
from typing import Dict, List, Optional, Union

from galaxy.agents.processors.processor import ConstellationAgentProcessor
from galaxy.agents.prompters.base_constellation_prompter import (
    BaseConstellationPrompter,
    ConstellationPrompterFactory,
)
from galaxy.agents.schema import ConstellationAgentResponse, WeavingMode
from galaxy.client.components.types import DeviceInfo
from galaxy.constellation.orchestrator.orchestrator import TaskConstellationOrchestrator
from galaxy.core.events import ConstellationEvent, EventType, TaskEvent, get_event_bus
from ufo.contracts.contracts import Command, MCPToolInfo, ResultStatus
from ufo.module.context import Context, ContextNames

from ..constellation import TaskConstellation
from ..core.interfaces import IRequestProcessor, IResultProcessor

from galaxy.agents.constellation_agent_states import ConstellationAgentStatus

# Import BasicAgent and ConstellationAgentStatus here to avoid circular import at module level
from ufo.agents.agent.basic import BasicAgent


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
        """Get the current constellation being managed."""
        return self._current_constellation

    # IRequestProcessor implementation
    async def process_creation(
        self,
        context: Context,
    ) -> TaskConstellation:
        """
        Process a user request and generate a constellation.

        :param request: User request string
        :param context: Optional processing context
        :return: Generated constellation
        :raises ConstellationError: If constellation generation fails
        """

        weaving_mode = context.get(ContextNames.WEAVING_MODE)
        self.prompter = self.get_prompter(weaving_mode)

        if not self._context_provision_executed:
            await self.context_provision(context=context)
            self._context_provision_executed = True

        self.processor = ConstellationAgentProcessor(agent=self, global_context=context)

        await self.processor.process()

        created_constellation: TaskConstellation = context.get(
            ContextNames.CONSTELLATION
        )

        is_dag, errors = created_constellation.validate_dag()
        self.status = self.processor.processing_context.get_local("status").upper()

        if not is_dag:
            self.logger.error(f"The created constellation is not a valid DAG: {errors}")
            self.status = ConstellationAgentStatus.FAIL.value

        # Sync the status with the processor.

        self.logger.info(f"Constellation agent status updated to: {self.status}")
        self._current_constellation = created_constellation

        return self._current_constellation

    # IResultProcessor implementation
    async def process_editing(
        self, context: Context = None, task_id: str = ""
    ) -> TaskConstellation:
        """
        Process a task result and potentially update the constellation.

        :param result: Task execution result
        :param context: Optional processing context
        :param task_id: The ID of the task being processed
        :return: Updated constellation
        :raises TaskExecutionError: If result processing fails
        """

        weaving_mode = context.get(ContextNames.WEAVING_MODE)
        self.prompter = self.get_prompter(weaving_mode)

        await self.context_provision(context=context)

        before_constellation: TaskConstellation = context.get(
            ContextNames.CONSTELLATION
        )

        # Update the constellation on the MCP server side.
        await context.command_dispatcher.execute_commands(
            commands=[
                Command(
                    tool_name="build_constellation",
                    parameters={
                        "config": before_constellation.to_basemodel(),
                        "clear_existing": True,
                    },
                    tool_type="action",
                )
            ]
        )

        self.logger.info(
            f"Task ID for constellation before editing: {before_constellation.tasks.keys()}"
        )

        self.logger.info(
            f"📊 Status for task before editing {task_id}: {before_constellation.get_task(task_id).status}"
        )

        self.logger.info(
            f"Dependency ID for constellation before editing: {before_constellation.dependencies.keys()}"
        )

        self.processor = ConstellationAgentProcessor(agent=self, global_context=context)
        await self.processor.process()

        # Sync the status with the processor.
        self.status = self.processor.processing_context.get_local("status").upper()
        self.logger.info(f"Constellation agent status updated to: {self.status}")

        after_constellation: TaskConstellation = context.get(ContextNames.CONSTELLATION)

        self.logger.info(
            f"📊 Status for task after editing {task_id}: {after_constellation.get_task(task_id).status}"
        )

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

        is_dag, errors = after_constellation.validate_dag()

        if not is_dag:
            self.logger.error(f"The created constellation is not a valid DAG: {errors}")
            self.status = "FAIL"

        self._current_constellation = after_constellation

        # Update the constellation on the MCP server side.
        await context.command_dispatcher.execute_commands(
            commands=[
                Command(
                    tool_name="build_constellation",
                    parameters={
                        "config": after_constellation.to_basemodel(),
                        "clear_existing": True,
                    },
                    tool_type="action",
                )
            ]
        )

        self.logger.info(
            f"Task ID for constellation after editing: {after_constellation.tasks.keys()}"
        )

        self.logger.info(
            f"Dependency ID for constellation after editing: {after_constellation.dependencies.keys()}"
        )

        # Publish DAG Modified Event
        await self._event_bus.publish_event(
            ConstellationEvent(
                event_type=EventType.CONSTELLATION_MODIFIED,
                source_id=self.name,
                timestamp=time.time(),
                data={
                    "old_constellation": before_constellation,
                    "new_constellation": after_constellation,
                    "modification_type": f"Edited by {self.name}",
                    "on_task_id": task_id,
                },
                constellation_id=after_constellation.constellation_id,
                constellation_state=(
                    after_constellation.state.value
                    if after_constellation.state
                    else "unknown"
                ),
            )
        )

        return after_constellation

    async def context_provision(
        self, context: Context, mask_creation: bool = True
    ) -> None:
        """
        Provide the context for the agent.
        :param context: The context for the agent.
        :param mask_creation: Whether to mask the tool for creation of constellation.
        """
        await self._load_mcp_context(context, mask_creation)

    async def _load_mcp_context(
        self, context: Context, mask_creation: bool = True
    ) -> None:
        """
        Load MCP context information for the current application.
        :param context: The context for the agent.
        :param mask_creation: Whether to mask the tool for creation of constellation.
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
        :param weaving_mode: The weaving mode for the agent.
        :return: The prompter for the agent.
        """
        self.logger.info(f"Creating prompter for {weaving_mode}")
        return ConstellationPrompterFactory.create_prompter(weaving_mode=weaving_mode)

    def message_constructor(
        self,
        request: str,
        device_info: Dict[str, DeviceInfo],
        constellation: TaskConstellation,
    ) -> List[Dict[str, Union[str, List[Dict[str, str]]]]]:
        """
        Construct the message for LLM interaction.
        :param request: The user request.
        :param device_info: Information about the user's device.
        :param constellation: The current task constellation.
        :return: A list of message dictionaries for LLM interaction.
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
        Print the response using the presenter.
        :param response: The ConstellationAgentResponse object to display
        :param print_action: Flag to indicate if action details should be printed
        """
        self.presenter.present_constellation_agent_response(
            response, print_action=print_action
        )

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
        except Exception as e:
            self.logger.error(f"Failed to add task event to queue: {str(e)}")
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
        except Exception as e:
            self.logger.error(f"Failed to add constellation event to queue: {str(e)}")
            raise RuntimeError(
                f"Failed to add constellation event to queue: {str(e)}"
            ) from e
