# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Base strategies for Constellation Agent processing.

This module provides base classes for different types of constellation processing strategies,
containing shared logic while allowing for mode-specific customization.
"""

import asyncio
import json
import time
import traceback
from abc import abstractmethod
from dataclasses import asdict
from typing import TYPE_CHECKING, Any, Dict, List

from galaxy.agents.processors.processor_context import ConstellationProcessorContext
from galaxy.agents.schema import (
    ConstellationAgentResponse,
    ConstellationRequestLog,
    WeavingMode,
)
from galaxy.client.components.types import AgentProfile
from galaxy.constellation.task_constellation import TaskConstellation
from galaxy.core.events import AgentEvent, EventType, get_event_bus
from ufo.agents.memory.memory import MemoryItem
from ufo.agents.processors.core.processor_framework import (
    ProcessingContext,
    ProcessingPhase,
    ProcessingResult,
)
from ufo.agents.processors.core.strategy_dependency import depends_on, provides
from ufo.agents.processors.schemas.actions import (
    ActionCommandInfo,
    ListActionCommandInfo,
)
from ufo.agents.processors.strategies.processing_strategy import BaseProcessingStrategy
from aip.messages import Command, Result
from ufo.llm import AgentType
from ufo.module.context import Context
from ufo.module.dispatcher import BasicCommandDispatcher
from config.config_loader import get_ufo_config

# Load configuration
ufo_config = get_ufo_config()

if TYPE_CHECKING:
    from galaxy.agents.constellation_agent import ConstellationAgent
    from ufo.module.basic import FileWriter


@provides(
    "parsed_response",
    "response_text",
    "llm_cost",
    "prompt_message",
    "status",
)
class ConstellationLLMInteractionStrategy(BaseProcessingStrategy):
    """
    Base LLM interaction strategy for Constellation Agent with shared logic.

    This base class contains common functionality for both creation and editing modes:
    - Prompt message construction
    - LLM response handling with retry logic
    - Response parsing and validation
    - Request logging

    Subclasses need to implement mode-specific prompt building logic.
    """

    def __init__(self, fail_fast: bool = True) -> None:
        """
        Initialize base Constellation LLM interaction strategy.
        :param fail_fast: Whether to raise exceptions immediately on errors
        """
        super().__init__(
            name=f"constellation_llm_interaction",
            fail_fast=fail_fast,
        )

    async def execute(
        self, agent: "ConstellationAgent", context: ProcessingContext
    ) -> ProcessingResult:
        """
        Execute LLM interaction with comprehensive error handling and retry logic.
        :param agent: The Constellation instance.
        :param context: Processing context with desktop data and agent information
        :return: ProcessingResult containing parsed response or error information
        """
        try:
            # Extract context variables
            session_step = context.get_local("session_step", 0)
            device_info = context.get_local("device_info", {})
            constellation: TaskConstellation = context.get_global("CONSTELLATION")
            request = context.get("request", "")
            request_logger = context.get_global("request_logger")
            weaving_mode = context.get_local("weaving_mode")

            # Step 1: Build comprehensive prompt message
            self.logger.info("Building prompt message with context")
            prompt_message = await self._build_comprehensive_prompt(
                agent,
                device_info,
                constellation,
                request,
                session_step,
                weaving_mode,
                request_logger,
            )

            # Step 2: Get LLM response with retry logic
            self.logger.info("Sending request to LLM")
            response_text, llm_cost = await self._get_llm_response_with_retry(
                agent, prompt_message
            )

            # Step 3: Parse and validate response
            self.logger.info("Parsing LLM response")
            parsed_response = self._parse_and_validate_response(agent, response_text)

            self.logger.info(f"Constellation LLM interaction completed successfully")

            return ProcessingResult(
                success=True,
                data={
                    "parsed_response": parsed_response,
                    "response_text": response_text,
                    "llm_cost": llm_cost,
                    "prompt_message": prompt_message,
                    **parsed_response.model_dump(),  # Include extracted structured data
                },
                phase=ProcessingPhase.LLM_INTERACTION,
            )

        except Exception as e:
            error_msg = (
                f"constellation LLM interaction failed: {str(traceback.format_exc())}"
            )
            self.logger.error(error_msg)
            return self.handle_error(e, ProcessingPhase.LLM_INTERACTION, context)

    async def _build_comprehensive_prompt(
        self,
        agent: "ConstellationAgent",
        device_info: Dict[str, AgentProfile],
        constellation: TaskConstellation,
        request: str,
        session_step: int,
        weaving_mode: str,
        request_logger: "FileWriter",
    ) -> Dict[str, Any]:
        """
        Build comprehensive prompt message with all available context information.
        Delegates mode-specific logic to subclasses.
        """
        try:
            # Build prompt message using mode-specific logic
            prompt_message = agent.message_constructor(
                request=request, device_info=device_info, constellation=constellation
            )

            constellation_json = constellation.to_json() if constellation else ""

            # Log request data for debugging
            self._log_request_data(
                session_step=session_step,
                device_info=device_info,
                constellation_json=constellation_json,
                request=request,
                prompt_message=prompt_message,
                weaving_mode=weaving_mode,
                request_logger=request_logger,
            )

            return prompt_message

        except Exception as e:
            raise Exception(
                f"Failed to build prompt message: {str(traceback.format_exc())}"
            )

    def _log_request_data(
        self,
        session_step: int,
        device_info: Dict[str, AgentProfile],
        constellation_json: str,
        request: str,
        weaving_mode: str,
        prompt_message: Dict[str, Any],
        request_logger: "FileWriter",
    ) -> None:
        """
        Log request data for debugging and analysis.
        """
        try:
            request_data = ConstellationRequestLog(
                step=session_step,
                device_info=device_info,
                constellation=constellation_json,
                request=request,
                weaving_mode=weaving_mode,
                prompt=prompt_message,
            )

            # Log request data as JSON
            request_log_str = json.dumps(
                asdict(request_data), ensure_ascii=False, default=str
            )

            # Use request logger if available
            if request_logger:
                request_logger.write(request_log_str)

        except Exception as e:
            self.logger.warning(f"Failed to log request data: {str(e)}")

    async def _get_llm_response_with_retry(
        self, agent: "ConstellationAgent", prompt_message: Dict[str, Any]
    ) -> tuple[str, float]:
        """
        Get LLM response with retry logic for JSON parsing failures.
        """
        max_retries = ufo_config.system.JSON_PARSING_RETRY
        last_exception = None

        for retry_count in range(max_retries):
            try:
                # Get response from LLM
                loop = asyncio.get_event_loop()
                response_text, cost = await loop.run_in_executor(
                    None,  # Use default ThreadPoolExecutor
                    agent.get_response,
                    prompt_message,
                    AgentType.CONSTELLATION,
                    True,  # use_backup_engine
                )

                # Validate that response can be parsed as JSON
                agent.response_to_dict(response_text)

                if retry_count > 0:
                    self.logger.info(
                        f"LLM response successful after {retry_count} retries"
                    )

                return response_text, cost

            except Exception as e:
                last_exception = e
                if retry_count < max_retries - 1:
                    self.logger.warning(
                        f"LLM response parsing failed (attempt {retry_count + 1}/{max_retries}): {str(e)}"
                    )
                else:
                    self.logger.error(
                        f"LLM response parsing failed after all retries: {str(e)}"
                    )

        raise Exception(
            f"LLM interaction failed after {max_retries} attempts: {str(last_exception)}"
        )

    def _parse_and_validate_response(
        self, agent: "ConstellationAgent", response_text: str
    ) -> ConstellationAgentResponse:
        """
        Parse and validate LLM response into structured format.
        """
        try:
            # Parse response to dictionary
            response_dict = agent.response_to_dict(response_text)

            # Create structured response object
            parsed_response = ConstellationAgentResponse.model_validate(response_dict)

            # Validate required fields
            self._validate_response_fields(parsed_response)

            # Print response for user feedback
            agent.print_response(parsed_response)

            return parsed_response

        except Exception as e:
            raise Exception(f"Failed to parse LLM response: {str(e)}")

    def _validate_response_fields(self, response: ConstellationAgentResponse) -> None:
        """
        Validate that response contains required fields and valid values.
        """
        if not response.thought:
            raise ValueError("Response missing required 'thought' field")

        if not response.status:
            raise ValueError("Response missing required 'status' field")

        # Validate status values
        valid_statuses = ["CONTINUE", "FINISH", "FAILED"]
        if response.status.upper() not in valid_statuses:
            self.logger.warning(f"Unexpected status value: {response.status}")


@depends_on("parsed_response")
@provides(
    "execution_result",
    "action_info",
    "status",
)
class BaseConstellationActionExecutionStrategy(BaseProcessingStrategy):
    """
    Base strategy for executing Constellation actions with shared logic.

    This base class contains common functionality for both creation and editing modes:
    - Action execution coordination
    - Command dispatcher interaction
    - Result processing and validation
    - Action info creation for memory

    Subclasses implement mode-specific action creation logic.
    """

    def __init__(self, weaving_mode: WeavingMode, fail_fast: bool = False) -> None:
        """
        Initialize base Constellation action execution strategy.
        :param weaving_mode: The weaving mode (CREATION or EDITING)
        :param fail_fast: Whether to raise exceptions immediately on errors
        """
        super().__init__(
            name=f"constellation_action_execution_{weaving_mode.value}",
            fail_fast=fail_fast,
        )
        self.weaving_mode = weaving_mode

    async def execute(
        self, agent: "ConstellationAgent", context: ProcessingContext
    ) -> ProcessingResult:
        """
        Execute Constellation actions with mode-specific logic.
        """
        try:
            # Step 1: Extract context variables
            parsed_response: ConstellationAgentResponse = context.get_local(
                "parsed_response"
            )
            command_dispatcher = context.global_context.command_dispatcher

            # Step 2: Create mode-specific action info
            action_info = await self._create_mode_specific_action_info(
                agent, parsed_response
            )

            # Step 3: Execute the action
            execution_results = await self._execute_constellation_action(
                command_dispatcher, action_info
            )
            self.sync_constellation(execution_results, context)

            # Step 4: Create action info for memory
            actions = self._create_action_info(action_info, execution_results)

            # Step 5: Print action info
            action_list_info = ListActionCommandInfo(actions)
            await self.publish_actions(agent, action_list_info)

            # Step 6: Determine status
            status = parsed_response.status

            return ProcessingResult(
                success=True,
                data={
                    "execution_result": execution_results,
                    "action_info": action_list_info,
                    "status": status,
                },
                phase=ProcessingPhase.ACTION_EXECUTION,
            )

        except Exception as e:
            error_msg = f"Constellation action execution ({self.weaving_mode.value}) failed: {str(traceback.format_exc())}"
            self.logger.error(error_msg)
            return self.handle_error(e, ProcessingPhase.ACTION_EXECUTION, context)

    @abstractmethod
    async def _create_mode_specific_action_info(
        self, agent: "ConstellationAgent", parsed_response: ConstellationAgentResponse
    ) -> ActionCommandInfo | List[ActionCommandInfo]:
        """
        Create mode-specific action information. Must be implemented by subclasses.
        """
        pass

    @abstractmethod
    async def publish_actions(
        self, agent: "ConstellationAgent", actions: ListActionCommandInfo
    ) -> None:
        """
        Publish agent actions as events. Must be implemented by subclasses.

        :param agent: The constellation agent
        :param actions: List of action command information
        """
        pass

    @abstractmethod
    def sync_constellation(
        self, results: List[Result], context: ProcessingContext
    ) -> None:
        """
        Synchronize the constellation state.
        :param results: List of execution results
        :param context: Processing context to access and update constellation state
        """
        pass

    async def _execute_constellation_action(
        self,
        command_dispatcher: BasicCommandDispatcher,
        actions: ActionCommandInfo | List[ActionCommandInfo],
    ) -> List[Result]:
        """
        Execute the specific action from the response.
        """
        if not actions:
            return []

        try:
            commands = []

            if isinstance(actions, ActionCommandInfo):
                actions = [actions]

            for action in actions:
                if not action.function:
                    continue
                command = self._action_to_command(action)
                commands.append(command)

            # Use the command dispatcher to execute the action
            if not command_dispatcher:
                raise ValueError("Command dispatcher not available")

            # Execute the command
            execution_result = await command_dispatcher.execute_commands(commands)
            return execution_result

        except Exception as e:
            raise Exception(f"Failed to execute constellation action: {str(e)}")

    def _action_to_command(self, action: ActionCommandInfo) -> Command:
        """
        Convert ActionCommandInfo to Command for execution.
        """
        return Command(
            tool_name=action.function,
            parameters=action.arguments or {},
            tool_type="action",
        )

    def _create_action_info(
        self,
        actions: ActionCommandInfo | List[ActionCommandInfo],
        execution_results: List[Result],
    ) -> List[ActionCommandInfo]:
        """
        Create action information for memory tracking.
        """
        try:
            if not actions:
                actions = []
            if not execution_results:
                execution_results = []

            if isinstance(actions, ActionCommandInfo):
                actions = [actions]

            # Ensure results match actions
            if len(execution_results) != len(actions):
                self.logger.warning(
                    f"Mismatch in actions ({len(actions)}) and execution results ({len(execution_results)}) length"
                )
                # Pad with empty results if needed
                while len(execution_results) < len(actions):
                    execution_results.append(
                        Result(status="error", result={"error": "No execution result"})
                    )

            for i, action in enumerate(actions):
                if i < len(execution_results):
                    action.result = execution_results[i]

                if not action.function:
                    action.function = "no_action"

            return actions

        except Exception as e:
            self.logger.warning(f"Failed to create action info: {str(e)}")
            return actions if isinstance(actions, list) else [actions]


@depends_on("parsed_response")
@provides("additional_memory", "memory_item", "memory_keys_count")
class ConstellationMemoryUpdateStrategy(BaseProcessingStrategy):
    """
    Memory update strategy for Constellation Agent - shared across all modes.

    This strategy handles comprehensive memory management for both creation and editing modes.
    The memory update logic is the same regardless of the weaving mode.
    """

    def __init__(self, fail_fast: bool = False) -> None:
        """
        Initialize Constellation Agent memory update strategy.
        :param fail_fast: Whether to raise exceptions immediately on errors
        """
        super().__init__(name="constellation_memory_update", fail_fast=fail_fast)

    async def execute(
        self, agent: "ConstellationAgent", context: ProcessingContext
    ) -> ProcessingResult:
        """
        Execute comprehensive memory update with error handling.
        """
        try:
            # Extract all needed variables from context
            parsed_response = context.get_local("parsed_response")

            # Step 1: Create comprehensive additional memory data
            self.logger.info("Creating additional memory data")
            additional_memory = self._create_additional_memory_data(agent, context)

            # Step 2: Create and populate memory item
            memory_item = self._create_and_populate_memory_item(
                parsed_response, additional_memory
            )

            # Step 3: Add memory to agent
            agent.add_memory(memory_item)

            # Step 4: Update structural logs
            self._update_structural_logs(memory_item, context.global_context)

            self.logger.info("Memory update completed successfully")

            return ProcessingResult(
                success=True,
                data={
                    "additional_memory": additional_memory,
                    "memory_item": memory_item,
                    "memory_keys_count": len(memory_item.to_dict()),
                },
                phase=ProcessingPhase.MEMORY_UPDATE,
            )

        except Exception as e:
            error_msg = f"Constellation Agent memory update failed: {str(e)}"
            self.logger.error(error_msg)
            return self.handle_error(e, ProcessingPhase.MEMORY_UPDATE, context)

    def _create_additional_memory_data(
        self, agent: "ConstellationAgent", context: ProcessingContext
    ) -> "ConstellationProcessorContext":
        """
        Create comprehensive additional memory data from processing context.
        """
        try:
            # Access the typed context directly
            constellation_context: ConstellationProcessorContext = context.local_context

            # Update context with current processing state
            constellation_context.session_step = context.get_global("SESSION_STEP", 0)
            constellation_context.round_step = context.get_global(
                "CURRENT_ROUND_STEP", 0
            )
            constellation_context.round_num = context.get_global("CURRENT_ROUND_ID", 0)
            constellation_context.agent_step = agent.step if agent else 0

            action_info: ListActionCommandInfo = constellation_context.action_info

            # Update action information if available
            if action_info:
                constellation_context.action = [
                    info.model_dump() for info in action_info.actions
                ]
                constellation_context.function_call = [
                    info.function for info in action_info.actions
                ]
                constellation_context.arguments = [
                    info.arguments for info in action_info.actions
                ]
                constellation_context.action_representation = [
                    info.to_representation() for info in action_info.actions
                ]

                constellation_after: TaskConstellation = context.get_global(
                    "CONSTELLATION"
                )

                if constellation_after:
                    constellation_context.constellation_after = (
                        constellation_after.to_json()
                    )

                if action_info.actions:
                    constellation_context.action_type = [
                        info.result.namespace for info in action_info.actions
                    ]
                    constellation_context.results = [
                        info.result.result for info in action_info.actions
                    ]

            # Update application and agent names
            constellation_context.agent_name = agent.name

            return constellation_context

        except Exception as e:
            raise Exception(
                f"Failed to create additional memory data: {str(traceback.format_exc())}"
            )

    def _create_and_populate_memory_item(
        self,
        parsed_response: ConstellationAgentResponse,
        additional_memory: "ConstellationProcessorContext",
    ) -> MemoryItem:
        """
        Create and populate memory item with response and additional data.
        """
        try:
            # Create new memory item
            memory_item = MemoryItem()

            # Add response data if available
            if parsed_response:
                memory_item.add_values_from_dict(parsed_response.model_dump())

            memory_item.add_values_from_dict(additional_memory.to_dict(selective=True))

            return memory_item

        except Exception as e:
            import traceback

            raise Exception(
                f"Failed to create and populate memory item: {str(traceback.format_exc())}"
            )

    def _update_structural_logs(
        self, memory_item: MemoryItem, global_context: Context
    ) -> None:
        """
        Update structural logs for debugging and analysis.
        """
        try:
            # Add to structural logs if context supports it
            global_context.add_to_structural_logs(memory_item.to_dict())

        except Exception as e:
            self.logger.warning(f"Failed to update structural logs: {str(e)}")
