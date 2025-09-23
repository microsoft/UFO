# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Host Agent Processor V2 - Refactored processor for Host Agent using the new framework.

This processor handles the Host Agent's workflow including:
- Desktop screenshot capture
- Application window detection and registration
- Third-party agent integration
- LLM interaction with proper context building
- Action execution and application selection
- Memory management and logging

The processor maintains backward compatibility with BaseProcessor interface
while providing enhanced modularity, error handling, and extensibility.
"""

import json
import traceback
from dataclasses import asdict
from typing import TYPE_CHECKING, Any, Dict, List

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
from ufo.config import Config
from ufo.contracts.contracts import Command, Result
from ufo.galaxy.agents.processors.context import ConstellationProcessorContext
from ufo.galaxy.agents.schema import (
    ConstellationAgentResponse,
    ConstellationRequestLog,
    WeavingMode,
)
from ufo.galaxy.constellation.task_constellation import TaskConstellation
from ufo.llm import AgentType
from ufo.module.context import Context, ContextNames
from ufo.module.dispatcher import BasicCommandDispatcher

# Load configuration
configs = Config.get_instance().config_data

if TYPE_CHECKING:
    from ufo.galaxy.agents.constellation_agent import ConstellationAgent
    from ufo.module.basic import FileWriter


@depends_on("device_info", "constellation", "request")
@provides(
    "parsed_response",
    "response_text",
    "llm_cost",
    "prompt_message",
    "subtask",
    "plan",
    "host_message",
    "status",
    "question_list",
    "function_name",
    "function_arguments",
)
class ConstellationLLMInteractionStrategy(BaseProcessingStrategy):
    """
    Enhanced LLM interaction strategy for Host Agent with comprehensive context building.

    This strategy handles:
    - Context-aware prompt construction with blackboard integration
    - Robust LLM interaction with retry logic
    - Response parsing and validation
    - Request logging for debugging and analysis
    """

    def __init__(self, fail_fast: bool = True) -> None:
        """
        Initialize Host Agent LLM interaction strategy.
        :param fail_fast: Whether to raise exceptions immediately on errors
        """
        super().__init__(name="host_llm_interaction", fail_fast=fail_fast)

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
            device_info = context.get_local("device_info", [])
            constellation: TaskConstellation = context.get_global(
                ContextNames.CONSTELLATION
            )
            weaving_mode = context.get_local("weaving_mode", "")
            request = context.get("request", "")
            request_logger = context.get_global("request_logger")

            # Step 1: Build comprehensive prompt message
            self.logger.info("Building prompt message with context")

            prompt_message = await self._build_comprehensive_prompt(
                agent,
                device_info,
                constellation,
                weaving_mode,
                request,
                session_step,
                request_logger,
            )

            # Step 3: Get LLM response with retry logic
            self.logger.info("Sending request to LLM")
            response_text, llm_cost = await self._get_llm_response_with_retry(
                agent, prompt_message
            )

            # Step 4: Parse and validate response
            self.logger.info("Parsing LLM response")
            parsed_response = self._parse_and_validate_response(agent, response_text)

            weaving_mode = context.get_local("weaving_mode")

            self.logger.info(
                f"Host LLM interaction status set to: {context.get_local('status')}"
            )

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
            error_msg = f"Host LLM interaction failed: {str(e)}"
            self.logger.error(error_msg)
            return self.handle_error(e, ProcessingPhase.LLM_INTERACTION, context)

    async def _build_comprehensive_prompt(
        self,
        agent: "ConstellationAgent",
        device_info: List[str],
        constellation: TaskConstellation,
        weaving_mode: str,
        request: str,
        session_step: int,
        request_logger: "FileWriter",
    ) -> Dict[str, Any]:
        """
        Build comprehensive prompt message with all available context information.
        :param agent: The Constellation Agent instance.
        :param target_info_list: List of target information
        :param desktop_screenshot_url: URL of desktop screenshot
        :param prev_plan: Previous plan
        :param previous_subtasks: Previous subtasks
        :param request: User request
        :param session_step: Current session step
        :param request_logger: Request logger
        :return: Complete prompt message dictionary for LLM interaction
        """
        try:

            # Build complete prompt message
            prompt_message = agent.message_constructor(
                device_info=device_info,
                constellation=constellation,
                weaving_mode=weaving_mode,
                request=request,
            )

            constellation_json = constellation.to_json()

            # Log request data for debugging
            self._log_request_data(
                session_step=session_step,
                device_info=device_info,
                constellation_json=constellation_json,
                weaving_mode=weaving_mode,
                request=request,
                prompt_message=prompt_message,
                request_logger=request_logger,
            )

            return prompt_message

        except Exception as e:
            raise Exception(f"Failed to build prompt message: {str(e)}")

    def _log_request_data(
        self,
        session_step: int,
        device_info: str,
        constellation_json: str,
        weaving_mode: WeavingMode,
        request: str,
        prompt_message: Dict[str, Any],
        request_logger: "FileWriter",
    ) -> None:
        """
        Log request data for debugging and analysis (only in debug mode).
        :param session_step: Current session step
        :param desktop_screenshot_url: Desktop screenshot URL
        :param target_info_list: List of target information
        :param prev_plan: Previous plan
        :param previous_subtasks: Previous subtasks
        :param request: User request
        :param blackboard_prompt: Extracted blackboard prompt items
        :param prompt_message: Constructed prompt message
        :param request_logger: Request logger
        """
        try:
            request_data = ConstellationRequestLog(
                step=session_step,
                device_info=device_info,
                constellation=constellation_json,
                weaving_mode=weaving_mode,
                request=request,
                prompt=prompt_message,
            )

            # Log request data as JSON
            request_log_str = json.dumps(asdict(request_data), ensure_ascii=False)

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
        :param agent: Host agent instance
        :param prompt_message: Prompt message for LLM
        :return: Tuple of (response_text, cost)
        :raises: Exception if all retry attempts fail
        """
        max_retries = configs.get("JSON_PARSING_RETRY", 3)
        last_exception = None

        for retry_count in range(max_retries):
            try:
                # Get response from LLM
                response_text, cost = agent.get_response(
                    prompt_message, AgentType.HOST, use_backup_engine=True
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
        :param agent: Host agent instance
        :param response_text: Raw response text from LLM
        :return: Parsed and validated ConstellationAgentResponse object
        :raises: Exception if response parsing or validation fails
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

        except Exception as e:
            self.logger.warning(f"Failed to create action info: {str(e)}")
            # Return basic action info on failure
            return ActionCommandInfo(
                function=function,
                arguments=parsed_response.constellation,
                status=parsed_response.status,
                result=Result(status="error", result={"error": str(e)}),
            )

    def _validate_response_fields(self, response: ConstellationAgentResponse) -> None:
        """
        Validate that response contains required fields and valid values.
        :param response: Parsed response object
        :raises: ValueError if If response validation fails
        """
        # Check for required fields

        if not response.thought:
            raise ValueError("Response missing required 'thought' field")

        if not response.status:
            raise ValueError("Response missing required 'status' field")

        # Validate status values
        valid_statuses = ["MONITOR", "FINISH", "FAILED"]
        if response.status.upper() not in valid_statuses:
            self.logger.warning(f"Unexpected status value: {response.status}")


@depends_on(
    "parsed_response",
    "log_path",
    "session_step",
    "annotation_dict",
    "application_window_info",
    "clean_screenshot_path",
)
@provides(
    "execution_result",
    "action_info",
    "control_log",
    "status",
    "selected_control_screenshot_path",
)
class ConstellationActionExecutionStrategy(BaseProcessingStrategy):
    """
    Strategy for executing Constellation actions.

    This strategy handles:
    - Action execution with UI controls
    - Control interaction and automation
    - Action result validation
    - Error handling and recovery
    """

    def __init__(self, fail_fast: bool = False) -> None:
        """
        Initialize App Agent action execution strategy.
        :param fail_fast: Whether to raise exceptions immediately on errors
        """
        super().__init__(name="app_action_execution", fail_fast=fail_fast)

    async def execute(
        self, agent: "ConstellationAgent", context: ProcessingContext
    ) -> ProcessingResult:
        """
        Execute Constellation actions.
        :param agent: The ConstellationAgent instance
        :param context: Processing context with response and control data
        :return: ProcessingResult with execution results
        """
        try:
            # Step 1: Extract context variables
            parsed_response: ConstellationAgentResponse = context.get_local(
                "parsed_response"
            )
            weaving_mode = context.get_local("weaving_mode")

            command_dispatcher = context.global_context.command_dispatcher

            if weaving_mode == WeavingMode.CREATION:
                action_info = [
                    ActionCommandInfo(
                        function=agent._constellation_creation_tool_name,
                        arguments={"config": parsed_response.constellation},
                    )
                ]
            elif weaving_mode == WeavingMode.EDITING:
                action_info = parsed_response.action

            # Execute the action
            execution_results = await self._execute_constellation_action(
                command_dispatcher, action_info
            )

            # Create action info for memory
            actions = self._create_action_info(
                action_info,
                execution_results,
            )

            # Print action info
            action_info = ListActionCommandInfo(actions)
            action_info.color_print()

            status = parsed_response.action.status

            return ProcessingResult(
                success=True,
                data={
                    "execution_result": execution_results,
                    "action_info": action_info,
                    "status": status,
                },
                phase=ProcessingPhase.ACTION_EXECUTION,
            )

        except Exception as e:

            error_msg = f"App action execution failed: {str(traceback.format_exc())}"
            self.logger.error(error_msg)
            return self.handle_error(e, ProcessingPhase.ACTION_EXECUTION, context)

    async def _execute_constellation_action(
        self,
        command_dispatcher: BasicCommandDispatcher,
        actions: ActionCommandInfo | List[ActionCommandInfo],
    ) -> List[Result]:
        """
        Execute the specific action from the response.
        :param command_dispatcher: Command dispatcher for executing commands
        :param response: Parsed response with action details
        :return: List of execution results
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
            raise Exception(f"Failed to execute app action: {str(e)}")

    def _action_to_command(self, action: ActionCommandInfo) -> Command:
        """
        Convert ActionCommandInfo to Command for execution.
        :param action: ActionCommandInfo object
        :return: Command object
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
        :param control_info: List of filtered controls
        :param response: Parsed response
        :param execution_result: Execution results
        :return: ActionCommandInfo object
        """
        try:
            # Get control information if action involved a control
            if not actions:
                actions = []
            if not execution_results:
                execution_results = []

            assert len(execution_results) == len(
                actions
            ), "Mismatch in actions and execution results length"

            if isinstance(actions, ActionCommandInfo):
                actions = [actions]

            for i, action in enumerate(actions):

                if action.arguments and "id" in action.arguments:
                    action.result = execution_results[i]

                if not action.function:
                    action.function = "no_action"

            return actions

        except Exception as e:
            self.logger.warning(f"Failed to create action info: {str(e)}")


@depends_on("session_step", "round_step", "round_num")
@provides("additional_memory", "memory_item", "memory_keys_count")
class ConstellationMemoryUpdateStrategy(BaseProcessingStrategy):
    """
    Enhanced memory update strategy for Constellation Agent with comprehensive data management.

    This strategy handles:
    - Memory item creation with structured data
    - Agent memory synchronization
    - Blackboard trajectory management
    - Structural logging for debugging and analysis
    """

    def __init__(self, fail_fast: bool = False) -> None:
        """
        Initialize Host Agent memory update strategy.
        :param fail_fast: Whether to raise exceptions immediately on errors
        """
        super().__init__(name="host_memory_update", fail_fast=fail_fast)

    async def execute(
        self, agent: "ConstellationAgent", context: ProcessingContext
    ) -> ProcessingResult:
        """
        Execute comprehensive memory update with error handling.
        :param agent: The Constellation instance.
        :param context: Processing context containing all execution data
        :return: ProcessingResult with memory update results or error information
        """
        try:
            # Extract all needed variables from context
            parsed_response = context.get_local("parsed_response")

            # Use the agent parameter directly

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
            error_msg = f"Host memory update failed: {str(e)}"
            self.logger.error(error_msg)
            return self.handle_error(e, ProcessingPhase.MEMORY_UPDATE, context)

    def _create_additional_memory_data(
        self, agent: "ConstellationAgent", context: ProcessingContext
    ) -> "ConstellationProcessorContext":
        """
        Create comprehensive additional memory data from processing context using ConstellationProcessorContext.
        This method extracts data from the unified typed context and converts to legacy format
        for backward compatibility.
        :param context: Processing context with execution data
        :return: ConstellationProcessorContext object with structured data compatible with original format
        """
        try:
            # Access the typed context directly
            constellation_context: ConstellationProcessorContext = context.local_context

            # Update context with current processing state
            constellation_context.session_step = context.get_global(
                ContextNames.SESSION_STEP.name, 0
            )
            constellation_context.round_step = context.get_global(
                ContextNames.CURRENT_ROUND_STEP.name, 0
            )
            constellation_context.round_num = context.get_global(
                ContextNames.CURRENT_ROUND_ID.name, 0
            )
            constellation_context.agent_step = agent.step if agent else 0

            action_info: ActionCommandInfo = constellation_context.action_info

            # Update action information if available
            if action_info:
                # ActionCommandInfo is a Pydantic BaseModel, use model_dump() instead of asdict()
                constellation_context.action = [action_info.model_dump()]
                constellation_context.function_call = action_info.function or ""
                constellation_context.arguments = action_info.arguments
                constellation_context.action_representation = (
                    action_info.to_representation()
                )

                constellation_after: TaskConstellation = context.get_global(
                    ContextNames.CONSTELLATION.name
                )

                if constellation_after:
                    constellation_context.constellation_after = (
                        constellation_after.to_json()
                    )

                if action_info.result:
                    constellation_context.action_type = action_info.result.namespace

                # Get results
                if action_info.result and action_info.result.result:
                    constellation_context.results = str(action_info.result.result)

            # Update application and agent names
            constellation_context.agent_name = agent.name

            # Convert to legacy format using the new method
            return constellation_context

        except Exception as e:
            raise Exception(f"Failed to create additional memory data: {str(e)}")

    def _create_and_populate_memory_item(
        self,
        parsed_response: ConstellationAgentResponse,
        additional_memory: "ConstellationProcessorContext",
    ) -> MemoryItem:
        """
        Create and populate memory item with response and additional data.
        :param parsed_response: Parsed response containing response data
        :param additional_memory: Additional memory data
        :return: Populated MemoryItem object
        """
        try:
            # Create new memory item
            memory_item = MemoryItem()

            # Add response data if available
            if parsed_response:
                # ConstellationAgentResponse is a regular class, use vars() to convert to dict
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
        :param memory_item: Memory item to log
        :param global_context: Global context for structural logs
        """
        try:
            # Add to structural logs if context supports it
            global_context.add_to_structural_logs(memory_item.to_dict())

        except Exception as e:
            self.logger.warning(f"Failed to update structural logs: {str(e)}")
