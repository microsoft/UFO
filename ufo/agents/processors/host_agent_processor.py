# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.


import json
from dataclasses import asdict, dataclass
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from ufo import utils
from ufo.agents.processors.actions import ActionCommandInfo
from ufo.agents.processors.basic import BaseProcessor
from ufo.agents.processors.target import TargetKind, TargetRegistry
from ufo.config import Config
from ufo.contracts.contracts import Command, Result
from ufo.llm import AgentType
from ufo.module.context import Context, ContextNames

configs = Config.get_instance().config_data


if TYPE_CHECKING:
    from ufo.agents.agent.host_agent import HostAgent


@dataclass
class HostAgentAdditionalMemory:
    """
    The additional memory for the host agent.
    """

    Step: int
    RoundStep: int
    AgentStep: int
    Round: int
    ControlLabel: str
    SubtaskIndex: int
    Action: str
    FunctionCall: str
    ActionType: str
    Request: str
    Agent: str
    AgentName: str
    Application: str
    Cost: float
    Results: str
    error: str
    time_cost: Dict[str, float]
    ControlLog: Dict[str, Any]


@dataclass
class HostAgentRequestLog:
    """
    The request log data for the AppAgent.
    """

    step: int
    image_list: List[str]
    os_info: Dict[str, str]
    plan: List[str]
    prev_subtask: List[str]
    request: str
    blackboard_prompt: List[str]
    prompt: Dict[str, Any]


@dataclass
class HostAgentResponse:
    """
    The response data for the HostAgent.
    """

    observation: str
    thought: str
    status: str
    message: Optional[List[str]] = None
    questions: Optional[List[str]] = None
    current_subtask: Optional[str] = None
    plan: Optional[List[str]] = None
    comment: Optional[str] = None
    function: Optional[str] = None
    arguments: Optional[Dict[str, Any]] = None


class HostAgentProcessor(BaseProcessor):
    """
    The processor for the host agent at a single step.
    """

    _select_application_command = "select_application_window"

    def __init__(self, agent: "HostAgent", context: Context) -> None:
        """
        Initialize the host agent processor.
        :param agent: The host agent to be processed.
        :param context: The context.
        """

        super().__init__(agent=agent, context=context)

        self.host_agent = agent

        self._desktop_screen_url = None

        self.target_registry = TargetRegistry()

        self.assigned_third_party_agent: str | None = None

        self.target_info: List[Dict[str, str]] = []

    def print_step_info(self) -> None:
        """
        Print the step information.
        """
        utils.print_with_color(
            "Round {round_num}, Step {step}, HostAgent: Analyzing the user intent and decomposing the request...".format(
                round_num=self.round_num + 1, step=self.round_step + 1
            ),
            "magenta",
        )

    @BaseProcessor.exception_capture
    @BaseProcessor.method_timer
    async def capture_screenshot(self) -> None:
        """
        Capture the screenshot.
        """

        desktop_save_path = self.log_path + f"action_step{self.session_step}.png"

        self._memory_data.add_values_from_dict({"CleanScreenshot": desktop_save_path})

        result = await self.context.command_dispatcher.execute_commands(
            [
                Command(
                    tool_name="capture_desktop_screenshot",
                    parameters={"all_screens": True},
                    tool_type="data_collection",
                )
            ]
        )

        self._desktop_screen_url = result[0].result

        utils.save_image_string(self._desktop_screen_url, desktop_save_path)

        self.logger.info(f"Desktop screenshot saved at: {desktop_save_path}")

    @BaseProcessor.exception_capture
    @BaseProcessor.method_timer
    async def get_control_info(self) -> None:
        """
        Get the control information.
        """

        result = await self.context.command_dispatcher.execute_commands(
            [
                Command(
                    tool_name="get_desktop_app_info",
                    parameters={"remove_empty": True, "refresh_app_windows": True},
                    tool_type="data_collection",
                )
            ]
        )

        desktop_windows_info = result[0].result

        self.logger.info(f"Got {len(desktop_windows_info)} desktop windows in total.")

        self.target_registry.register_from_dicts(desktop_windows_info)
        self.register_third_party_agents(start_index=len(desktop_windows_info) + 1)

    def register_third_party_agents(self, start_index: int = 0) -> None:
        """
        Create a list of third-party agents.
        :param start_index: The starting index of the third-party agent list.
        """

        third_party_agent_names = configs.get("ENABLED_THIRD_PARTY_AGENTS", [])

        self.logger.info(f"Enabled third-party agents: {third_party_agent_names}")

        third_party_agent_list = []

        for i, agentname in enumerate(third_party_agent_names):
            label = str(i + start_index)
            third_party_agent_list.append(
                {
                    "kind": TargetKind.THIRD_PARTY_AGENT.value,
                    "id": label,
                    "type": "ThirdPartyAgent",
                    "name": agentname,
                }
            )
        self.target_registry.register_from_dicts(third_party_agent_list)

    @BaseProcessor.exception_capture
    @BaseProcessor.method_timer
    async def get_prompt_message(self) -> None:
        """
        Get the prompt message.
        """

        if not self.host_agent.blackboard.is_empty():
            blackboard_prompt = self.host_agent.blackboard.blackboard_to_prompt()
        else:
            blackboard_prompt = []

        self.target_info = self.target_registry.to_list(
            keep_keys=["id", "name", "kind"]
        )

        # Construct the prompt message for the host agent.
        self._prompt_message = self.host_agent.message_constructor(
            image_list=[self._desktop_screen_url],
            os_info=self.target_info,
            plan=self.prev_plan,
            prev_subtask=self.previous_subtasks,
            request=self.request,
            blackboard_prompt=blackboard_prompt,
        )

        # print(f"Prompt message: {self._prompt_message}")

        request_data = HostAgentRequestLog(
            step=self.session_step,
            image_list=[self._desktop_screen_url],
            os_info=self.target_info,
            plan=self.prev_plan,
            prev_subtask=self.previous_subtasks,
            request=self.request,
            blackboard_prompt=blackboard_prompt,
            prompt=self._prompt_message,
        )

        # Log the prompt message. Only save them in debug mode.
        request_log_str = json.dumps(asdict(request_data), ensure_ascii=False)
        self.request_logger.write(request_log_str)

    @BaseProcessor.exception_capture
    @BaseProcessor.method_timer
    async def get_response(self) -> None:
        """
        Get the response from the LLM.
        """

        retry = 0
        while retry < configs.get("JSON_PARSING_RETRY", 3):
            # Try to get the response from the LLM. If an error occurs, catch the exception and log the error.
            self._response, self.cost = self.host_agent.get_response(
                self._prompt_message, AgentType.HOST, use_backup_engine=True
            )

            try:
                self.host_agent.response_to_dict(self._response)
                break
            except Exception:
                print(f"Error in parsing response into json, retrying: {retry}")
                retry += 1

    @BaseProcessor.exception_capture
    @BaseProcessor.method_timer
    def parse_response(self) -> None:
        """
        Parse the response.
        """

        response_dict = self.host_agent.response_to_dict(self._response)

        self.response = HostAgentResponse(**response_dict)

        self.subtask = self.response.current_subtask
        self.host_message = self.response.message

        # Convert the plan from a string to a list if the plan is a string.
        self.plan = self.string2list(self.response.plan)

        self.status = self.response.status
        self.question_list = self.response.questions

        self.host_agent.print_response(self.response)

    @BaseProcessor.exception_capture
    @BaseProcessor.method_timer
    async def execute_action(self) -> None:
        """
        Execute the action.
        """

        result = [Result(status="none")]

        function, arguments = self.response.function, self.response.arguments

        target_id = arguments.get("id")

        if function == self._select_application_command:

            result = await self._select_application(target_id)

        elif function:
            result = await self.context.command_dispatcher.execute_commands(
                [
                    Command(
                        tool_name=function,
                        parameters=arguments,
                        tool_type="action",
                    )
                ]
            )

            self.logger.info(
                f"Executed command: {function}, with arguments: {arguments}"
            )

        action = ActionCommandInfo(
            function=self.response.function,
            arguments=self.response.arguments,
            target=self.target_registry.get(self.control_label),
            status=self.response.status,
            result=result[0],
        )

        self.actions.add_action(action)

    async def _select_application(self, target_id: str) -> Dict[str, Any]:
        """
        Select an application.
        :param target_id: The ID of the target application.
        :return: The selected application information.
        """

        target: TargetKind = self.target_registry.get(target_id)

        if target and target.kind == TargetKind.THIRD_PARTY_AGENT:

            self.assigned_third_party_agent = target.name
            result = [
                Result(status="success", result={"id": target.id, "name": target.name})
            ]

        else:

            result = await self.context.command_dispatcher.execute_commands(
                [
                    Command(
                        tool_name=self._select_application_command,
                        parameters={"id": str(target_id), "name": target.name},
                        tool_type="action",
                    )
                ]
            )

            self.app_root = result[0].result.get("root_name", "")
            self.logger.info(
                f"Selected application process name: {target.name}, root name: {self.app_root}"
            )

        self.control_label = target_id
        self.control_text = target.name
        self.context.set(ContextNames.APPLICATION_ROOT_NAME, self.app_root)
        self.context.set(ContextNames.APPLICATION_PROCESS_NAME, target.name)

        return result

    def sync_memory(self):
        """
        Sync the memory of the HostAgent.
        """

        additional_memory = HostAgentAdditionalMemory(
            Step=self.session_step,
            RoundStep=self.round_step,
            AgentStep=self.host_agent.step,
            Round=self.round_num,
            ControlLabel=self.control_label,
            SubtaskIndex=-1,
            FunctionCall=self.actions.get_function_calls(),
            Action=self.actions.to_list_of_dicts(),
            ActionType=self.actions.actions[0].result.namespace,
            Request=self.request,
            Agent="HostAgent",
            AgentName=self.host_agent.name,
            Application=self.app_root,
            Cost=self._cost,
            Results=self.actions.get_results(),
            error=self._exeception_traceback,
            time_cost=self._time_cost,
            ControlLog=self.actions.get_target_info(),
        )

        self.add_to_memory(asdict(self.response))
        self.add_to_memory(asdict(additional_memory))

    def update_memory(self) -> None:
        """
        Update the memory of the Agent.
        """

        # Sync the memory
        self.sync_memory()

        self.host_agent.add_memory(self._memory_data)

        # Log the memory item.
        self.context.add_to_structural_logs(self._memory_data.to_dict())
        # self.log(self._memory_data.to_dict())

        # Only memorize the keys in the HISTORY_KEYS list to feed into the prompt message in the future steps.
        memorized_action = {
            key: self._memory_data.to_dict().get(key) for key in configs["HISTORY_KEYS"]
        }

        self.host_agent.blackboard.add_trajectories(memorized_action)
