import traceback
from typing import List, TYPE_CHECKING


from ufo.agents.processors.app_agent_processor import AppAgentLoggingMiddleware
from ufo.agents.processors.context.processing_context import (
    ProcessingContext,
    ProcessingResult,
    ProcessingPhase,
)
from ufo.agents.processors.core.strategy_dependency import depends_on, provides
from ufo.agents.processors.schemas.actions import (
    ListActionCommandInfo,
    ActionCommandInfo,
)
from ufo.agents.processors.strategies.app_agent_processing_strategy import (
    AppActionExecutionStrategy,
    AppLLMInteractionStrategy,
)
from aip.messages import Result
from ufo.llm.response_schema import AppAgentResponse

if TYPE_CHECKING:
    from ufo.agents.agent.customized_agent import LinuxAgent


@depends_on("request")
@provides(
    "parsed_response",
    "response_text",
    "llm_cost",
    "prompt_message",
    "action",
    "thought",
    "comment",
)
class LinuxLLMInteractionStrategy(AppLLMInteractionStrategy):
    """
    Strategy for LLM interaction with Linux Agent specific prompting.

    This strategy handles:
    - Context-aware prompt construction with app-specific data
    - Control information integration in prompts
    - LLM interaction with retry logic
    - Response parsing and validation
    """

    def __init__(self, fail_fast: bool = True) -> None:
        """
        Initialize App Agent LLM interaction strategy.
        :param fail_fast: Whether to raise exceptions immediately on errors
        """
        super().__init__(fail_fast=fail_fast)

    async def execute(
        self, agent: "LinuxAgent", context: ProcessingContext
    ) -> ProcessingResult:
        """
        Execute LLM interaction for Linux Agent.
        :param agent: The LinuxAgent instance
        :param context: Processing context with control and screenshot data
        :return: ProcessingResult with parsed response and cost
        """
        try:
            request = context.get("request")
            plan = self._get_prev_plan(agent)

            # Build comprehensive prompt
            self.logger.info("Building Linux Agent prompt")
            # Get blackboard context
            blackboard_prompt = []
            if not agent.blackboard.is_empty():
                blackboard_prompt = agent.blackboard.blackboard_to_prompt()

            prompt_message = agent.message_constructor(
                dynamic_examples=[],
                dynamic_knowledge="",
                plan=plan,
                request=request,
                blackboard_prompt=blackboard_prompt,
                last_success_actions=self._get_last_success_actions(agent=agent),
            )

            # Get LLM response
            self.logger.info("Getting LLM response for Linux Agent")
            response_text, llm_cost = await self._get_llm_response(
                agent, prompt_message
            )

            # Parse and validate response
            self.logger.info("Parsing Linux Agent response")
            parsed_response = self._parse_app_response(agent, response_text)

            # Extract structured data
            structured_data = parsed_response.model_dump()

            return ProcessingResult(
                success=True,
                data={
                    "parsed_response": parsed_response,
                    "response_text": response_text,
                    "llm_cost": llm_cost,
                    "prompt_message": prompt_message,
                    **structured_data,
                },
                phase=ProcessingPhase.LLM_INTERACTION,
            )

        except Exception as e:
            error_msg = f"App LLM interaction failed: {str(e)}"
            self.logger.error(error_msg)
            return self.handle_error(e, ProcessingPhase.LLM_INTERACTION, context)


class LinuxActionExecutionStrategy(AppActionExecutionStrategy):
    """
    Strategy for executing actions in Linux Agent.

    This strategy handles:
    - Action execution based on parsed LLM response
    - Result capturing and error handling
    """

    def __init__(self, fail_fast: bool = True) -> None:
        """
        Initialize Linux action execution strategy.
        :param fail_fast: Whether to raise exceptions immediately on errors
        """
        super().__init__(fail_fast=fail_fast)

    async def execute(
        self, agent: "LinuxAgent", context: ProcessingContext
    ) -> ProcessingResult:
        """
        Execute Linux Agent actions.
        :param agent: The AppAgent instance
        :param context: Processing context with response and control data
        :return: ProcessingResult with execution results
        """
        try:
            # Step 1: Extract context variables
            parsed_response: AppAgentResponse = context.get_local("parsed_response")
            command_dispatcher = context.global_context.command_dispatcher

            if not parsed_response:
                return ProcessingResult(
                    success=True,
                    data={"message": "No response available for action execution"},
                    phase=ProcessingPhase.ACTION_EXECUTION,
                )

            # Execute the action
            execution_results = await self._execute_app_action(
                command_dispatcher, parsed_response.action
            )

            # Create action info for memory
            actions = self._create_action_info(
                parsed_response.action,
                execution_results,
            )

            # Print action info
            action_info = ListActionCommandInfo(actions)
            action_info.color_print()

            # Create control log
            control_log = action_info.get_target_info()

            status = (
                parsed_response.action.status
                if isinstance(parsed_response.action, ActionCommandInfo)
                else action_info.status
            )

            return ProcessingResult(
                success=True,
                data={
                    "execution_result": execution_results,
                    "action_info": action_info,
                    "control_log": control_log,
                    "status": status,
                },
                phase=ProcessingPhase.ACTION_EXECUTION,
            )

        except Exception as e:

            error_msg = f"App action execution failed: {str(traceback.format_exc())}"
            self.logger.error(error_msg)
            return self.handle_error(e, ProcessingPhase.ACTION_EXECUTION, context)

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

            if isinstance(actions, ActionCommandInfo):
                actions = [actions]

            assert len(execution_results) == len(
                actions
            ), "Mismatch in actions and execution results length"

            for i, action in enumerate(actions):
                action.result = execution_results[i]

                if not action.function:
                    action.function = "no_action"

            return actions

        except Exception as e:
            self.logger.warning(f"Failed to create action info: {str(e)}")


class LinuxLoggingMiddleware(AppAgentLoggingMiddleware):
    """
    Specialized logging middleware for Linux Agent with enhanced contextual information.
    """

    def starting_message(self, context: ProcessingContext) -> str:
        """
        Return the starting message of the agent.
        :param context: Processing context with round and step information
        :return: Starting message string
        """

        # Try both global and local context for request
        request = (
            context.get("request") or context.get_local("request") or "Unknown Request"
        )

        return (
            f"Completing the user request: [bold cyan]{request}[/bold cyan] on Linux."
        )
