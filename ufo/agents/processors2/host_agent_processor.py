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
import logging
from dataclasses import asdict
from typing import TYPE_CHECKING, Any, Dict, List, Optional


from ufo import utils
from ufo.agents.memory.memory import MemoryItem
from ufo.agents.processors.actions import ActionCommandInfo
from ufo.agents.processors.host_agent_processor import (
    HostAgentAdditionalMemory,
    HostAgentRequestLog,
    HostAgentResponse,
)
from ufo.agents.processors.target import TargetInfo, TargetKind, TargetRegistry
from ufo.agents.processors2.strategies.processing_strategy import BaseProcessingStrategy
from ufo.agents.processors2.core.processor_framework import (
    ProcessingContext,
    ProcessingPhase,
    ProcessingResult,
    ProcessorTemplate,
)
from ufo.agents.processors2.core.processing_context import ProcessorContextFactory
from ufo.agents.processors2.core.strategy_dependency import (
    depends_on,
    provides,
)
from ufo.agents.processors2.middleware.enhanced_middleware import (
    EnhancedLoggingMiddleware,
)
from ufo.config import Config
from ufo.contracts.contracts import Command, Result, ResultStatus
from ufo.llm import AgentType
from ufo.module.context import Context, ContextNames

# Load configuration
configs = Config.get_instance().config_data

if TYPE_CHECKING:
    from ufo.agents.agent.host_agent import HostAgent


# Note: HostAgentUnifiedMemory has been replaced with HostAgentProcessorContext
# from the unified context system in processing_context.py


if TYPE_CHECKING:
    from ufo.agents.agent.host_agent import HostAgent


class HostAgentProcessorV2(ProcessorTemplate):
    """
    Enhanced processor for Host Agent with comprehensive functionality.

    This processor manages the complete workflow of a Host Agent including:
    - Desktop environment analysis and screenshot capture
    - Application window detection and registration
    - Third-party agent integration and management
    - LLM-based decision making with context-aware prompting
    - Action execution including application selection and command dispatch
    - Memory management with detailed logging and state tracking

    This processor maintains compatibility with the original BaseProcessor
    interface while providing enhanced modularity and error handling.
    """

    # Class constants for better maintainability
    SELECT_APPLICATION_COMMAND: str = "select_application_window"

    def __init__(self, agent: "HostAgent", global_context: Context) -> None:
        """
        Initialize the Host Agent Processor with enhanced capabilities.
        :param agent: The Host Agent instance to be processed
        :param global_context: Global context shared across the session
        """
        # Core components and tools - kept in __init__
        self.host_agent: "HostAgent" = agent

        # Initialize parent class
        super().__init__(agent, global_context)

    def _setup_strategies(self) -> None:
        """
        Configure processing strategies with enhanced error handling and logging capabilities.
        """
        self.strategies[ProcessingPhase.DATA_COLLECTION] = (
            DesktopDataCollectionStrategy(
                fail_fast=True  # Desktop data collection is critical for Host Agent
            )
        )
        self.strategies[ProcessingPhase.LLM_INTERACTION] = HostLLMInteractionStrategy(
            fail_fast=True  # LLM interaction failure should trigger recovery
        )
        self.strategies[ProcessingPhase.ACTION_EXECUTION] = HostActionExecutionStrategy(
            fail_fast=False  # Action failures can be handled gracefully
        )
        self.strategies[ProcessingPhase.MEMORY_UPDATE] = HostMemoryUpdateStrategy(
            fail_fast=False  # Memory update failures shouldn't stop the process
        )

    def _setup_middleware(self) -> None:
        """
        Set up enhanced middleware chain with comprehensive monitoring and recovery.
        The middleware chain includes:
        - HostAgentLoggingMiddleware: Specialized logging for Host Agent operations
        """
        self.middleware_chain = [
            HostAgentLoggingMiddleware(),  # Specialized logging for Host Agent
        ]

    def _finalize_processing_context(
        self, processing_context: ProcessingContext
    ) -> None:
        """
        Finalize processing context by updating existing ContextNames fields.
        Instead of promoting arbitrary keys, we update the predefined ContextNames
        that the system actually uses.
        :param processing_context: The processing context to finalize.
        """

        super()._finalize_processing_context(processing_context)
        try:
            # Update SUBTASK if available
            subtask = processing_context.get_local("subtask")
            if subtask:
                self.global_context.set(ContextNames.SUBTASK, subtask)

            # Update HOST_MESSAGE if available
            host_message = processing_context.get_local("host_message")
            if host_message:
                self.global_context.set(ContextNames.HOST_MESSAGE, host_message)

            # Update APPLICATION_ROOT_NAME if selected
            selected_app_root = processing_context.get_local(
                "selected_application_root"
            )
            if selected_app_root:
                self.global_context.set(
                    ContextNames.APPLICATION_ROOT_NAME, selected_app_root
                )

            selected_target: TargetInfo = processing_context.get_local("target")

            if selected_target:
                self.global_context.set(
                    ContextNames.APPLICATION_PROCESS_NAME, selected_target.name
                )

        except Exception as e:
            self.logger.warning(f"Failed to update ContextNames from results: {e}")

    def _create_processing_context(self) -> ProcessingContext:
        """
        Create Host Agent specific processing context using the new unified typed context system.
        :return: ProcessingContext with Host Agent specific typed context
        """
        # Create typed Host Agent context using factory
        local_context = ProcessorContextFactory.create_host_context(
            host_agent=self.host_agent,
            processor=self,
            global_context=self.global_context,
        )

        # # Create ProcessingContext with the unified typed local_context
        return ProcessingContext(
            global_context=self.global_context, local_context=local_context
        )

    def print_step_info(self) -> None:
        """
        Print step information for debugging and monitoring.
        Displays the current round, step, and processing status with color coding
        for better user experience and debugging visibility.
        """
        round_num = self.global_context.get(ContextNames.CURRENT_ROUND_ID)
        round_step = self.global_context.get(ContextNames.CURRENT_ROUND_STEP)

        # Log detailed information
        self.logger.info(
            f"Host Agent processing - Round {round_num + 1}, Step {round_step + 1}: "
            f"Analyzing user intent and decomposing request"
        )

        # Display user-friendly colored message (maintaining original behavior)
        utils.print_with_color(
            f"Round {round_num + 1}, Step {round_step + 1}, HostAgent: "
            f"Analyzing user intent and decomposing request...",
            "magenta",
        )


@depends_on("command_dispatcher", "log_path", "session_step")
@provides(
    "desktop_screenshot_url",
    "desktop_screenshot_path",
    "application_windows_info",
    "target_registry",
    "target_info_list",
)
class DesktopDataCollectionStrategy(BaseProcessingStrategy):
    """
    Enhanced strategy for collecting desktop environment data with comprehensive error handling.

    This strategy handles:
    - Desktop screenshot capture with proper path management
    - Application window detection and filtering
    - Third-party agent registration and configuration
    - Target registry management for application selection
    """

    def __init__(self, fail_fast: bool = True) -> None:
        """
        Initialize desktop data collection strategy.
        :param fail_fast: Whether to raise exceptions immediately on errors
        """
        super().__init__(name="desktop_data_collection", fail_fast=fail_fast)

    async def execute(
        self, agent: "HostAgent", context: ProcessingContext
    ) -> ProcessingResult:
        """
        Execute comprehensive desktop data collection with enhanced error handling.
        :param agent: The HostAgent instance.
        :param context: Processing context with global and local data
        :return: ProcessingResult with collected desktop data or error information
        """
        try:
            # Step 1: Capture desktop screenshot
            self.logger.info("Starting desktop screenshot capture")
            screenshot_data = await self._capture_desktop_screenshot(context)

            # Step 2: Collect application window information
            self.logger.info("Collecting desktop application information")
            app_windows_info = await self._get_desktop_application_info(context)

            # Step 3: Register applications and third-party agents
            self.logger.info(f"Registering {len(app_windows_info)} applications")
            target_registry = self._register_applications_and_agents(
                context, app_windows_info
            )

            # Step 4: Prepare target information for LLM
            target_info_list = target_registry.to_list(keep_keys=["id", "name", "kind"])

            return ProcessingResult(
                success=True,
                data={
                    "desktop_screenshot_url": screenshot_data["url"],
                    "desktop_screenshot_path": screenshot_data["path"],
                    "application_windows_info": app_windows_info,
                    "target_registry": target_registry,
                    "target_info_list": target_info_list,
                },
                phase=ProcessingPhase.DATA_COLLECTION,
            )

        except Exception as e:
            error_msg = f"Desktop data collection failed: {str(e)}"
            self.logger.error(error_msg)
            return self.handle_error(e, ProcessingPhase.DATA_COLLECTION, context)

    async def _capture_desktop_screenshot(
        self, context: ProcessingContext
    ) -> Dict[str, str]:
        """
        Capture desktop screenshot with proper error handling and path management.
        :param context: Processing context containing command dispatcher and paths
        :return: Dictionary containing screenshot URL and file path
        :raises: Exception if screenshot capture fails
        """
        try:
            command_dispatcher = context.global_context.command_dispatcher

            if not command_dispatcher:
                raise ValueError("Command dispatcher not available in context")

            log_path = context.get("log_path", "")
            session_step = context.get("session_step", 0)

            desktop_save_path = f"{log_path}action_step{session_step}.png"

            # Execute screenshot capture command
            result = await command_dispatcher.execute_commands(
                [
                    Command(
                        tool_name="capture_desktop_screenshot",
                        parameters={"all_screens": True},
                        tool_type="data_collection",
                    )
                ]
            )

            if (
                not result
                or not result[0].result
                or result[0].status != ResultStatus.SUCCESS
            ):
                raise RuntimeError("Screenshot capture returned empty result")

            desktop_screenshot_url = result[0].result

            # Save screenshot to file
            utils.save_image_string(desktop_screenshot_url, desktop_save_path)
            self.logger.info(f"Desktop screenshot saved to: {desktop_save_path}")

            return {"url": desktop_screenshot_url, "path": desktop_save_path}

        except Exception as e:
            raise Exception(f"Failed to capture desktop screenshot: {str(e)}")

    async def _get_desktop_application_info(
        self, context: ProcessingContext
    ) -> List[Dict[str, Any]]:
        """
        Get comprehensive desktop application information with filtering.
        :param context: Processing context containing command dispatcher
        :return: List of application window information dictionaries
        :raises: Exception if application info collection fails
        """
        try:
            command_dispatcher = context.global_context.command_dispatcher
            if not command_dispatcher:
                raise ValueError("Command dispatcher not available in context")

            # Execute desktop app info collection command
            result = await command_dispatcher.execute_commands(
                [
                    Command(
                        tool_name="get_desktop_app_info",
                        parameters={"remove_empty": True, "refresh_app_windows": True},
                        tool_type="data_collection",
                    )
                ]
            )

            if not result:
                raise RuntimeError("Desktop app info collection returned empty result")

            app_windows_info = result[0].result or []
            self.logger.info(f"Found {len(app_windows_info)} desktop windows")

            return app_windows_info

        except Exception as e:
            raise Exception(f"Failed to get desktop application info: {str(e)}")

    def _register_applications_and_agents(
        self, context: ProcessingContext, app_windows_info: List[Dict[str, Any]]
    ) -> TargetRegistry:
        """
        Register desktop applications and third-party agents in target registry.
        :param context: Processing context
        :param app_windows_info: List of application window information
        :return: Target registry with registered applications and agents
        """
        try:
            # Get or create target registry
            target_registry = context.get_local("target_registry")
            if not target_registry:
                target_registry = TargetRegistry()
                context.set_local("target_registry", target_registry)

            # Register desktop application windows
            target_registry.register_from_dicts(app_windows_info)
            self.logger.info(f"Registered {len(app_windows_info)} application windows")

            # Register third-party agents
            third_party_count = self._register_third_party_agents(
                target_registry, len(app_windows_info)
            )

            self.logger.info(f"Registered {third_party_count} third-party agents")
            return target_registry

        except Exception as e:
            raise Exception(f"Failed to register applications and agents: {str(e)}")

    def _register_third_party_agents(
        self, target_registry: TargetRegistry, start_index: int
    ) -> int:
        """
        Register enabled third-party agents with proper indexing.
        :param target_registry: Target registry to add agents to
        :param start_index: Starting index for agent IDs
        :return: Number of third-party agents registered
        """
        try:
            # Get enabled third-party agent names from configuration
            third_party_agent_names = configs.get("ENABLED_THIRD_PARTY_AGENTS", [])

            if not third_party_agent_names:
                self.logger.info("No third-party agents configured")
                return 0

            # Create third-party agent entries
            third_party_agent_list = []
            for i, agent_name in enumerate(third_party_agent_names):
                agent_id = str(i + start_index + 1)  # +1 for proper indexing
                third_party_agent_list.append(
                    {
                        "kind": TargetKind.THIRD_PARTY_AGENT.value,
                        "id": agent_id,
                        "type": "ThirdPartyAgent",
                        "name": agent_name,
                    }
                )

            # Register third-party agents in registry
            target_registry.register_from_dicts(third_party_agent_list)

            return len(third_party_agent_list)

        except Exception as e:
            self.logger.warning(f"Failed to register third-party agents: {str(e)}")
            return 0  # Don't fail the entire process for third-party agent registration


@depends_on("target_info_list", "desktop_screenshot_url", "request")
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
class HostLLMInteractionStrategy(BaseProcessingStrategy):
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
        self, agent: "HostAgent", context: ProcessingContext
    ) -> ProcessingResult:
        """
        Execute LLM interaction with comprehensive error handling and retry logic.
        :param agent: The HostAgent instance.
        :param context: Processing context with desktop data and agent information
        :return: ProcessingResult containing parsed response or error information
        """
        try:
            # Use the agent parameter directly instead of getting from context
            host_agent = agent
            if not host_agent:
                raise ValueError("Host agent not available")

            # Step 1: Build comprehensive prompt message
            self.logger.info("Building prompt message with context")
            prompt_message = await self._build_comprehensive_prompt(host_agent, context)

            # Step 2: Log request for debugging (only in debug mode)
            self._log_request_data(context, prompt_message)

            # Step 3: Get LLM response with retry logic
            self.logger.info("Sending request to LLM")
            response_text, llm_cost = await self._get_llm_response_with_retry(
                host_agent, prompt_message
            )

            # Step 4: Parse and validate response
            self.logger.info("Parsing LLM response")
            parsed_response = self._parse_and_validate_response(
                host_agent, response_text
            )

            # Update processor status from parsed response
            context.set_local("status", parsed_response.status)

            self.logger.info(
                f"Host LLM interaction status set to: {context.get_local('status')}"
            )

            # Step 5: Extract structured information from response
            structured_data = self._extract_structured_response_data(parsed_response)

            return ProcessingResult(
                success=True,
                data={
                    "parsed_response": parsed_response,
                    "response_text": response_text,
                    "llm_cost": llm_cost,
                    "prompt_message": prompt_message,
                    **structured_data,  # Include extracted structured data
                },
                phase=ProcessingPhase.LLM_INTERACTION,
            )

        except Exception as e:
            error_msg = f"Host LLM interaction failed: {str(e)}"
            self.logger.error(error_msg)
            return self.handle_error(e, ProcessingPhase.LLM_INTERACTION, context)

    async def _build_comprehensive_prompt(
        self, agent: "HostAgent", context: ProcessingContext
    ) -> Dict[str, Any]:
        """
        Build comprehensive prompt message with all available context information.
        :param agent: The HostAgent instance.
        :param context: Processing context containing desktop and agent data
        :return: Complete prompt message dictionary for LLM interaction
        """
        try:
            host_agent: "HostAgent" = agent  # Use agent parameter directly
            target_info_list = context.get_local("target_info_list", [])
            desktop_screenshot_url = context.get_local("desktop_screenshot_url", "")

            # Get blackboard context if available
            blackboard_prompt = []
            if not host_agent.blackboard.is_empty():
                blackboard_prompt = host_agent.blackboard.blackboard_to_prompt()
                self.logger.debug(
                    f"Including {len(blackboard_prompt)} blackboard items"
                )

            # Build complete prompt message
            prompt_message = host_agent.message_constructor(
                image_list=[desktop_screenshot_url] if desktop_screenshot_url else [],
                os_info=target_info_list,
                plan=context.get("prev_plan", []),
                prev_subtask=context.get("previous_subtasks", []),
                request=context.get("request", ""),
                blackboard_prompt=blackboard_prompt,
            )

            self.logger.debug(f"Built prompt with {len(target_info_list)} targets")
            return prompt_message

        except Exception as e:
            raise Exception(f"Failed to build prompt message: {str(e)}")

    def _log_request_data(
        self,
        context: ProcessingContext,
        prompt_message: Dict[str, Any],
        blackboard_prompt: List[str],
    ) -> None:
        """
        Log request data for debugging and analysis (only in debug mode).
        :param context: Processing context
        :param prompt_message: Constructed prompt message
        :param blackboard_prompt: Extracted blackboard prompt items
        """
        try:
            desktop_screenshot_url = context.get_local("desktop_screenshot_url", "")
            request_data = HostAgentRequestLog(
                step=context.get("session_step", 0),
                image_list=[desktop_screenshot_url] if desktop_screenshot_url else [],
                os_info=context.get_local("target_info_list", []),
                plan=context.get("prev_plan", []),
                prev_subtask=context.get("previous_subtasks", []),
                request=context.get("request", ""),
                blackboard_prompt=blackboard_prompt,
                prompt=prompt_message,
            )

            # Log request data as JSON
            request_log_str = json.dumps(asdict(request_data), ensure_ascii=False)

            # Use request logger if available
            request_logger = context.get_global("request_logger")
            if request_logger:
                request_logger.debug(request_log_str)

        except Exception as e:
            self.logger.warning(f"Failed to log request data: {str(e)}")

    async def _get_llm_response_with_retry(
        self, host_agent: "HostAgent", prompt_message: Dict[str, Any]
    ) -> tuple[str, float]:
        """
        Get LLM response with retry logic for JSON parsing failures.
        :param host_agent: Host agent instance
        :param prompt_message: Prompt message for LLM
        :return: Tuple of (response_text, cost)
        :raises: Exception if all retry attempts fail
        """
        max_retries = configs.get("JSON_PARSING_RETRY", 3)
        last_exception = None

        for retry_count in range(max_retries):
            try:
                # Get response from LLM
                response_text, cost = host_agent.get_response(
                    prompt_message, AgentType.HOST, use_backup_engine=True
                )

                # Validate that response can be parsed as JSON
                host_agent.response_to_dict(response_text)

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
        self, host_agent: "HostAgent", response_text: str
    ) -> HostAgentResponse:
        """
        Parse and validate LLM response into structured format.
        :param host_agent: Host agent instance
        :param response_text: Raw response text from LLM
        :return: Parsed and validated HostAgentResponse object
        :raises: Exception if response parsing or validation fails
        """
        try:
            # Parse response to dictionary
            response_dict = host_agent.response_to_dict(response_text)

            # Create structured response object
            parsed_response = HostAgentResponse(**response_dict)

            # Validate required fields
            self._validate_response_fields(parsed_response)

            # Print response for user feedback
            host_agent.print_response(parsed_response)

            return parsed_response

        except Exception as e:
            raise Exception(f"Failed to parse LLM response: {str(e)}")

    def _validate_response_fields(self, response: HostAgentResponse) -> None:
        """
        Validate that response contains required fields and valid values.
        :param response: Parsed response object
        :raises: ValueError if If response validation fails
        """
        # Check for required fields
        if not response.observation:
            raise ValueError("Response missing required 'observation' field")

        if not response.thought:
            raise ValueError("Response missing required 'thought' field")

        if not response.status:
            raise ValueError("Response missing required 'status' field")

        # Validate status values
        valid_statuses = ["CONTINUE", "FINISH", "CONFIRM", "ERROR"]
        if response.status.upper() not in valid_statuses:
            self.logger.warning(f"Unexpected status value: {response.status}")

    def _extract_structured_response_data(
        self, response: HostAgentResponse
    ) -> Dict[str, Any]:
        """
        Extract structured data from parsed response for use by subsequent strategies.
        :param response: Parsed response object
        :return: Dictionary containing extracted structured data
        """
        # Convert plan from string to list if needed
        plan = response.plan
        if isinstance(plan, str) and plan.strip():
            # Simple string to list conversion - could be enhanced
            plan = [item.strip() for item in plan.split("\n") if item.strip()]
        elif not isinstance(plan, list):
            plan = []

        return {
            "subtask": response.current_subtask,
            "plan": plan,
            "host_message": response.message,
            "status": response.status,
            "question_list": response.questions,
            "function_name": response.function,
            "function_arguments": response.arguments or {},
        }


@depends_on("target_registry", "command_dispatcher")
@provides(
    "execution_result",
    "action_info",
    "selected_target_id",
    "selected_application_root",
    "assigned_third_party_agent",
)
class HostActionExecutionStrategy(BaseProcessingStrategy):
    """
    Enhanced action execution strategy for Host Agent with comprehensive error handling.

    This strategy handles:
    - Application selection and window management
    - Third-party agent assignment and coordination
    - Generic command execution with proper error handling
    - Context state management and updates
    """

    def __init__(self, fail_fast: bool = False) -> None:
        """
        Initialize Host Agent action execution strategy.
        :param fail_fast: Whether to raise exceptions immediately on errors
        """
        super().__init__(name="host_action_execution", fail_fast=fail_fast)

    async def execute(
        self, agent: "HostAgent", context: ProcessingContext
    ) -> ProcessingResult:
        """
        Execute Host Agent actions with comprehensive error handling and state management.
        :param agent: The HostAgent instance.
        :param context: Processing context containing response and execution data
        :return: ProcessingResult with execution results or error information
        """
        try:
            parsed_response = context.get_local("parsed_response")
            if not parsed_response:
                return ProcessingResult(
                    success=True,
                    data={"message": "No response available for action execution"},
                    phase=ProcessingPhase.ACTION_EXECUTION,
                )

            function_name = context.get_local("function_name")
            if not function_name:
                return ProcessingResult(
                    success=True,
                    data={"message": "No action to execute"},
                    phase=ProcessingPhase.ACTION_EXECUTION,
                )

            self.logger.info(f"Executing action: {function_name}")

            # Execute the appropriate action based on function name
            if function_name == HostAgentProcessorV2.SELECT_APPLICATION_COMMAND:
                execution_result = await self._execute_application_selection(
                    context, parsed_response
                )
            else:
                execution_result = await self._execute_generic_command(
                    context, parsed_response
                )

            # Create action info for memory and tracking
            action_info = self._create_action_info(
                context, parsed_response, execution_result
            )

            # Update context state based on execution results
            self._update_context_state(context, parsed_response, execution_result)

            return ProcessingResult(
                success=True,
                data={
                    "execution_result": execution_result,
                    "action_info": action_info,
                    "selected_target_id": context.get_local("selected_target_id"),
                    "selected_application_root": context.get_local(
                        "selected_application_root"
                    ),
                    "assigned_third_party_agent": context.get_local(
                        "assigned_third_party_agent"
                    ),
                },
                phase=ProcessingPhase.ACTION_EXECUTION,
            )

        except Exception as e:
            error_msg = f"Host action execution failed: {str(e)}"
            self.logger.error(error_msg)
            return self.handle_error(e, ProcessingPhase.ACTION_EXECUTION, context)

    async def _execute_application_selection(
        self, context: ProcessingContext, response: HostAgentResponse
    ) -> List[Result]:
        """
        Execute application selection with proper handling of different target types.
        :param context: Processing context
        :param response: Parsed response containing function arguments
        :return: List of execution results
        """
        try:
            target_id = response.arguments.get("id") if response.arguments else None
            if not target_id:
                raise ValueError("No target ID specified for application selection")

            target_registry: TargetRegistry = context.get_local("target_registry")

            if not target_registry:
                raise ValueError("Target registry not available")

            target = target_registry.get(target_id)
            if not target:
                raise ValueError(f"Target with ID '{target_id}' not found")

            self.logger.info(
                f"Selecting target: {target.name} (ID: {target_id}, Kind: {target.kind})"
            )

            context.set_local("target", target)

            # Handle third-party agent selection
            if target.kind == TargetKind.THIRD_PARTY_AGENT:
                return await self._select_third_party_agent(context, target)

            # Handle regular application selection
            else:
                return await self._select_regular_application(context, target)

        except Exception as e:
            raise Exception(f"Application selection failed: {str(e)}")

    async def _select_third_party_agent(
        self, context: ProcessingContext, target: TargetInfo
    ) -> List[Result]:
        """
        Handle third-party agent selection and assignment.
        This method processes the selection of a third-party agent and records
        the assignment in the processing context for subsequent use.
        :param context: Processing context for storing assignment information
        :param target: Third-party agent target object containing agent details
        :return: List of Result objects indicating successful third-party agent selection
        :raises: Exception if third-party agent selection encounters critical errors
        """
        try:

            context.set_local("assigned_third_party_agent", target.name)
            context.set_local("selected_target_id", target.id)

            self.logger.info(f"Assigned third-party agent: {target.name}")

            # Create success result for third-party agent selection
            return [
                Result(
                    status="success",
                    result={
                        "id": target.id,
                        "name": target.name,
                        "type": "third_party_agent",
                    },
                )
            ]

        except Exception as e:
            raise Exception(f"Third-party agent selection failed: {str(e)}")

    async def _select_regular_application(
        self, context: ProcessingContext, target: Any
    ) -> List[Result]:
        """
        Handle regular application selection and window management.
        This method executes the application selection command and manages
        the window state, including setting the application root and updating
        the global context for use by other components.
        :param context: Processing context for state management
        :param target: Application target object containing application details
        :return: List of Result objects from application selection command execution
        :raises: Exception if application selection or window management fails
        """
        try:
            command_dispatcher = context.global_context.command_dispatcher
            if not command_dispatcher:
                raise ValueError("Command dispatcher not available")

            # Execute application selection command
            execution_result = await command_dispatcher.execute_commands(
                [
                    Command(
                        tool_name=HostAgentProcessorV2.SELECT_APPLICATION_COMMAND,
                        parameters={"id": str(target.id), "name": target.name},
                        tool_type="action",
                    )
                ]
            )

            # Extract application root information
            if execution_result and execution_result[0].result:
                app_root = execution_result[0].result.get("root_name", "")

                context.set_local("selected_application_root", app_root)
                context.set_local("selected_target_id", target.id)

                # Update global context for other components
                # context.set_global(ContextNames.APPLICATION_ROOT_NAME, app_root)
                # context.set_global(ContextNames.APPLICATION_PROCESS_NAME, target.name)

                self.logger.info(
                    f"Selected application: {target.name}, root: {app_root}"
                )

            return execution_result

        except Exception as e:
            raise Exception(f"Regular application selection failed: {str(e)}")

    async def _execute_generic_command(
        self, context: ProcessingContext, response: HostAgentResponse
    ) -> List[Result]:
        """
        Execute generic command using command dispatcher.
        This method handles the execution of arbitrary commands that are not
        specifically handled by other execution methods. It provides a generic
        interface for command execution with proper error handling.
        :param context: Processing context containing command dispatcher
        :param response: Parsed response containing function name and arguments
        :return: List of Result objects from command execution
        :raises: Exception if command dispatcher is unavailable or command execution fails
        """
        try:
            command_dispatcher = context.global_context.command_dispatcher
            if not command_dispatcher:
                raise ValueError("Command dispatcher not available")

            function_name = response.function
            arguments = response.arguments or {}

            self.logger.info(
                f"Executing generic command: {function_name} with args: {arguments}"
            )

            # Execute command
            execution_result = await command_dispatcher.execute_commands(
                [
                    Command(
                        tool_name=function_name,
                        parameters=arguments,
                        tool_type="action",
                    )
                ]
            )

            return execution_result

        except Exception as e:
            raise Exception(f"Generic command execution failed: {str(e)}")

    def _create_action_info(
        self,
        context: ProcessingContext,
        response: HostAgentResponse,
        execution_result: List[Result],
    ) -> ActionCommandInfo:
        """
        Create action information object for memory and tracking.
        This method constructs a comprehensive action information object that
        captures the complete context of the executed action, including the
        target object, execution results, and status information.
        :param context: Processing context containing target registry
        :param response: Parsed response with action details
        :param execution_result: Results from action execution
        :return: ActionCommandInfo object with complete execution details
        """
        try:
            target_registry = context.get_local("target_registry")
            selected_target_id = context.get_local("selected_target_id")

            # Get target object for action info
            target_object = None
            if target_registry and selected_target_id:
                target_object = target_registry.get(selected_target_id)

            # Create action info
            action_info = ActionCommandInfo(
                function=response.function,
                arguments=response.arguments or {},
                target=target_object,
                status=response.status,
                result=(
                    execution_result[0] if execution_result else Result(status="none")
                ),
            )

            return action_info

        except Exception as e:
            self.logger.warning(f"Failed to create action info: {str(e)}")
            # Return basic action info on failure
            return ActionCommandInfo(
                function=response.function or "unknown",
                arguments=response.arguments or {},
                target=None,
                status=response.status or "unknown",
                result=Result(status="error", result={"error": str(e)}),
            )

    def _update_context_state(
        self,
        context: ProcessingContext,
        response: HostAgentResponse,
        execution_result: List[Result],
    ) -> None:
        """
        Update context state based on action execution results.
        This method updates the processing context with relevant state information
        from the action execution, ensuring that subsequent processing phases have
        access to the updated state information.
        :param context: Processing context to update with execution state
        :param response: Parsed response containing action information
        :param execution_result: Results from action execution for state updates
        """
        try:

            # Update control label and text for memory
            selected_target_id = context.get_local("selected_target_id")
            if selected_target_id:
                updates = {"control_label": selected_target_id}

                target_registry = context.get_local("target_registry")
                if target_registry:
                    target = target_registry.get(selected_target_id)
                    if target:
                        updates["control_text"] = target.name

                context.set_local("control_label", selected_target_id)
                if "control_text" in updates:
                    context.set_local("control_text", updates["control_text"])

            # Store action result for memory
            if execution_result:

                context.set_local("action_result", execution_result[0].result)

        except Exception as e:
            self.logger.warning(f"Failed to update context state: {str(e)}")


@depends_on("session_step", "round_step", "round_num")
@provides("additional_memory", "memory_item", "memory_keys_count")
class HostMemoryUpdateStrategy(BaseProcessingStrategy):
    """
    Enhanced memory update strategy for Host Agent with comprehensive data management.

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
        self, agent: "HostAgent", context: ProcessingContext
    ) -> ProcessingResult:
        """
        Execute comprehensive memory update with error handling.
        :param agent: The HostAgent instance.
        :param context: Processing context containing all execution data
        :return: ProcessingResult with memory update results or error information
        """
        try:
            # Use the agent parameter directly
            host_agent = agent

            # Step 1: Create comprehensive additional memory data
            self.logger.info("Creating additional memory data")
            additional_memory = self._create_additional_memory_data(context)

            # Step 2: Create and populate memory item
            memory_item = self._create_and_populate_memory_item(
                context, additional_memory
            )

            # Step 3: Add memory to agent
            host_agent.add_memory(memory_item)

            # Step 4: Update structural logs
            self._update_structural_logs(context, memory_item)

            # Step 5: Update blackboard trajectories
            self._update_blackboard_trajectories(context, host_agent, memory_item)

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
        self, context: ProcessingContext
    ) -> HostAgentAdditionalMemory:
        """
        Create comprehensive additional memory data from processing context using HostAgentProcessorContext.
        This method extracts data from the unified typed context and converts to legacy format
        for backward compatibility.
        :param context: Processing context with execution data
        :return: HostAgentAdditionalMemory object with structured data compatible with original format
        """
        try:
            # Access the typed context directly
            host_context = context.local_context

            # Update context with current processing state
            host_context.step = context.get_global(ContextNames.SESSION_STEP.name, 0)
            host_context.round_step = context.get_global(
                ContextNames.CURRENT_ROUND_STEP.name, 0
            )
            host_context.round_num = context.get_global(
                ContextNames.CURRENT_ROUND_ID.name, 0
            )
            host_context.agent_step = (
                host_context.host_agent.step if host_context.host_agent else 0
            )

            action_info: ActionCommandInfo = host_context.action_info

            # Update action information if available
            if action_info:
                # ActionCommandInfo is a Pydantic BaseModel, use model_dump() instead of asdict()
                host_context.action = [action_info.model_dump()]
                host_context.function_call = action_info.function or ""
                if action_info.result:
                    host_context.action_type = action_info.result.namespace

                # Get results
                if action_info.result and action_info.result.result:
                    host_context.results = str(action_info.result.result)

            # Update application and agent names
            host_context.application = host_context.selected_application_root or ""
            host_context.agent_name = (
                host_context.host_agent.name if host_context.host_agent else ""
            )

            # Update time costs and control log
            host_context.execution_times = self._calculate_time_costs(context)
            host_context.control_log = self._create_control_log(
                context, host_context.action_info
            )

            # Convert to legacy format using the new method
            return host_context.to_legacy_memory()

        except Exception as e:
            raise Exception(f"Failed to create additional memory data: {str(e)}")

    def _calculate_time_costs(self, context: ProcessingContext) -> Dict[str, float]:
        """
        Calculate time costs for different processing phases.
        :param context: Processing context
        :return: Dictionary mapping phase names to execution times
        """
        try:
            # Get execution times from processing context if available
            time_costs = {}

            # This would be populated by middleware or strategies if they track timing
            # For now, return empty dict as the framework handles timing differently
            return time_costs

        except Exception as e:
            self.logger.warning(f"Failed to calculate time costs: {str(e)}")
            return {}

    def _create_control_log(
        self, context: ProcessingContext, action_info: Optional[ActionCommandInfo]
    ) -> Dict[str, Any]:
        """
        Create control log information for debugging and analysis.
        :param context: Processing context
        :param action_info: Action information if available
        :return: Dictionary containing control log data
        """
        try:
            control_log = {}

            if action_info and action_info.target:
                control_log = {
                    "target_id": getattr(action_info.target, "id", ""),
                    "target_name": getattr(action_info.target, "name", ""),
                    "target_kind": getattr(action_info.target, "kind", ""),
                    "control_text": context.get_local("control_text", ""),
                }

            return control_log

        except Exception as e:
            self.logger.warning(f"Failed to create control log: {str(e)}")
            return {}

    def _create_and_populate_memory_item(
        self, context: ProcessingContext, additional_memory: HostAgentAdditionalMemory
    ) -> MemoryItem:
        """
        Create and populate memory item with response and additional data.
        :param context: Processing context
        :param additional_memory: Additional memory data
        :return: Populated MemoryItem object
        """
        try:
            # Create new memory item
            memory_item = MemoryItem()

            # Add response data if available
            parsed_response = context.get_local("parsed_response")
            if parsed_response:
                # HostAgentResponse is a regular class, use vars() to convert to dict
                memory_item.add_values_from_dict(asdict(parsed_response))

            # Add additional memory data
            memory_item.add_values_from_dict(asdict(additional_memory))

            return memory_item

        except Exception as e:
            raise Exception(f"Failed to create and populate memory item: {str(e)}")

    def _update_structural_logs(
        self, context: ProcessingContext, memory_item: MemoryItem
    ) -> None:
        """
        Update structural logs for debugging and analysis.
        :param context: Processing context
        :param memory_item: Memory item to log
        """
        try:
            # Add to structural logs if context supports it
            context.global_context.add_to_structural_logs(memory_item.to_dict())

        except Exception as e:
            self.logger.warning(f"Failed to update structural logs: {str(e)}")

    def _update_blackboard_trajectories(
        self,
        host_agent: "HostAgent",
        memory_item: MemoryItem,
    ) -> None:
        """
        Update blackboard trajectories with memorized actions.
        :param host_agent: Host agent instance
        :param memory_item: Memory item with trajectory data
        """
        try:
            # Get history keys from configuration
            history_keys = configs.get("HISTORY_KEYS", [])
            if not history_keys:
                self.logger.debug("No history keys configured for blackboard")
                return

            # Extract memorized action data
            memory_dict = memory_item.to_dict()
            memorized_action = {
                key: memory_dict.get(key) for key in history_keys if key in memory_dict
            }

            # Add trajectories to blackboard if available
            if memorized_action:
                host_agent.blackboard.add_trajectories(memorized_action)
                self.logger.debug(f"Added {len(memorized_action)} items to blackboard")

        except Exception as e:
            self.logger.warning(f"Failed to update blackboard trajectories: {str(e)}")


class HostAgentLoggingMiddleware(EnhancedLoggingMiddleware):
    """
    Specialized logging middleware for Host Agent with enhanced contextual information.

    This middleware provides:
    - Host Agent specific progress messages with color coding
    - Detailed step information and context logging
    - Performance metrics and execution summaries
    - Enhanced error reporting with Host Agent context
    """

    def __init__(self) -> None:
        """Initialize Host Agent logging middleware with appropriate log level."""
        super().__init__(log_level=logging.INFO)

    async def before_process(
        self, processor: ProcessorTemplate, context: ProcessingContext
    ) -> None:
        """
        Log Host Agent processing start with detailed context information.
        :param processor: Host Agent processor instance
        :param context: Processing context with round and step information
        """
        # Call parent implementation for standard logging
        await super().before_process(processor, context)

        # Add Host Agent specific logging
        round_num = context.get("round_num", 0)
        round_step = context.get("round_step", 0)
        request = context.get("request", "")

        # Log detailed context information
        self.logger.info(
            f"Host Agent Processing Context - "
            f"Round: {round_num + 1}, Step: {round_step + 1}, "
            f"Request: '{request[:100]}{'...' if len(request) > 100 else ''}'"
        )

        # Display colored progress message for user feedback (maintaining original UX)
        utils.print_with_color(
            f"Round {round_num + 1}, Step {round_step + 1}, HostAgent: "
            f"Analyzing user intent and decomposing request...",
            "magenta",
        )

        # Log available context data for debugging
        if self.logger.isEnabledFor(logging.DEBUG):
            context_keys = list(
                context.local_data.keys()
            )  # This uses the backward-compatible property
            self.logger.debug(f"Available context keys: {context_keys}")

    async def after_process(
        self, processor: ProcessorTemplate, result: ProcessingResult
    ) -> None:
        """
        Log Host Agent processing completion with execution summary.
        :param processor: Host Agent processor instance
        :param result: Processing result with execution data
        """
        # Call parent implementation for standard logging
        await super().after_process(processor, result)

        if result.success:
            # Log Host Agent specific success information
            selected_app = result.data.get("selected_application_root", "")
            assigned_agent = result.data.get("assigned_third_party_agent", "")
            subtask = result.data.get("subtask", "")

            success_msg = "Host Agent processing completed successfully"
            if selected_app:
                success_msg += f" - Selected application: {selected_app}"
            elif assigned_agent:
                success_msg += f" - Assigned third-party agent: {assigned_agent}"
            if subtask:
                success_msg += f" - Current subtask: {subtask}"

            self.logger.info(success_msg)

            # Display user-friendly completion message (maintaining original UX)
            if selected_app or assigned_agent:
                target_name = selected_app or assigned_agent
                utils.print_with_color(
                    f"HostAgent: Successfully selected target '{target_name}'", "green"
                )
        else:
            # Enhanced error logging for Host Agent
            error_phase = getattr(result, "phase", "unknown")
            self.logger.error(
                f"Host Agent processing failed at phase: {error_phase} - {result.error}"
            )

            # Display user-friendly error message (maintaining original UX)
            utils.print_with_color(
                f"HostAgent: Processing failed - {result.error}", "red"
            )

    async def on_error(self, processor: ProcessorTemplate, error: Exception) -> None:
        """
        Enhanced error handling for Host Agent with contextual information.
        :param processor: Host Agent processor instance
        :param error: Exception that occurred
        """
        # Call parent implementation for standard error handling
        await super().on_error(processor, error)

        utils.print_with_color(
            f"HostAgent: Encountered error - {str(error)[:100]}", "red"
        )
