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

from ufo.agents.agent.basic import BasicAgent
from ufo.contracts.contracts import Command, MCPToolInfo, ResultStatus
from ufo.galaxy.agents.constellation_agent_states import ConstellationAgentStatus
from ufo.galaxy.agents.processors.processor import ConstellationAgentProcessor
from ufo.galaxy.agents.prompter import ConstellationAgentPrompter
from ufo.galaxy.agents.schema import WeavingMode
from ufo.galaxy.constellation.orchestrator.orchestrator import (
    TaskConstellationOrchestrator,
)
from ufo.galaxy.core.events import (
    get_event_bus,
    ConstellationEvent,
    EventType,
    TaskEvent,
)
from ufo.module.context import Context, ContextNames


from ..core.interfaces import IRequestProcessor, IResultProcessor
from ..constellation import TaskConstellation


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
        main_prompt: str = "",
        example_prompt: str = "",
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
        self.prompter: ConstellationAgentPrompter = self.get_prompter(
            main_prompt, example_prompt
        )

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
            self.status = "FAIL"

        # Sync the status with the processor.

        self.logger.info(f"Constellation agent status updated to: {self.status}")
        self._current_constellation = created_constellation

        return self._current_constellation

    # IResultProcessor implementation
    async def process_editing(
        self,
        context: Context = None,
    ) -> TaskConstellation:
        """
        Process a task result and potentially update the constellation.

        :param result: Task execution result
        :param context: Optional processing context
        :return: Updated constellation
        :raises TaskExecutionError: If result processing fails
        """

        if not self._context_provision_executed:
            await self.context_provision(context=context)
            self._context_provision_executed = True

        before_constellation: TaskConstellation = context.get(
            ContextNames.CONSTELLATION
        )

        self.processor = ConstellationAgentProcessor(agent=self, global_context=context)
        await self.processor.process()

        # Sync the status with the processor.
        self.status = self.processor.processing_context.get_local("status").upper()
        self.logger.info(f"Constellation agent status updated to: {self.status}")

        after_constellation: TaskConstellation = context.get(ContextNames.CONSTELLATION)

        try:
            await asyncio.wait_for(
                self.constellation_completion_queue.get(), timeout=1.0
            )

            self.logger.info(
                f"The old constellation {before_constellation.constellation_id} is completed."
            )

            if self.status == ConstellationAgentStatus.CONTINUE.value:
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

        self.prompter.create_api_prompt_template(tools=tools_info)

    def get_prompter(
        self, main_prompt: str, example_prompt: str, weaving_mode: WeavingMode
    ) -> ConstellationAgentPrompter:
        """
        Get the prompter for the agent.
        :param main_prompt: The main prompt for the agent.
        :param example_prompt: The example prompt for the agent.
        :param weaving_mode: The weaving mode for the agent.
        :return: The prompter for the agent.
        """

        return ConstellationAgentPrompter(main_prompt, example_prompt, weaving_mode)

    def message_constructor(
        self,
        device_info: Dict[str, str],
        constellation: TaskConstellation,
    ) -> List[Dict[str, Union[str, List[Dict[str, str]]]]]:
        """
        Construct the message for LLM interaction.

        Returns:
            List of message dictionaries for LLM
        """
        system_message = self.prompter.system_prompt_construction()
        user_message = self.prompter.user_content_construction(
            device_info=device_info, constellation=constellation
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

        if not event.event_type not in [
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

        if not event.event_type != EventType.CONSTELLATION_COMPLETED:
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
