# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.


import json
from dataclasses import asdict, dataclass
from typing import TYPE_CHECKING, Any, Dict, List, Tuple

from ufo import utils
from ufo.agents.processors.action_contracts import (
    ActionExecutionLog,
    ActionSequence,
    BaseControlLog,
    OneStepAction,
)
from ufo.agents.processors.basic import BaseProcessor
from ufo.config import Config
from ufo.contracts.contracts import Command
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


class HostAgentProcessor(BaseProcessor):
    """
    The processor for the host agent at a single step.
    """

    def __init__(self, agent: "HostAgent", context: Context) -> None:
        """
        Initialize the host agent processor.
        :param agent: The host agent to be processed.
        :param context: The context.
        """

        super().__init__(agent=agent, context=context)

        self.host_agent = agent

        self._desktop_screen_url = None

        self.bash_command = None
        self.third_party_agent_labels: List[str] = []
        self.full_desktop_windows_info: List[Dict[str, str]] = []
        self.assigned_third_party_agent: str | None = None

        self.actions: List[OneStepAction] = []

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

        result = await self.context.message_bus.publish_commands(
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

        result = await self.context.message_bus.publish_commands(
            [
                Command(
                    tool_name="get_desktop_app_info",
                    parameters={"remove_empty": True, "refresh_app_windows": True},
                    tool_type="data_collection",
                )
            ]
        )

        self._desktop_windows_info = result[0].result

        self.logger.info(
            f"Got {len(self._desktop_windows_info)} desktop windows in total."
        )

    def _create_third_party_agent_list(
        self, start_index: int = 0
    ) -> Tuple[List[Dict], List[str]]:
        """
        Create a list of third-party agents.
        :param start_index: The starting index of the third-party agent list.
        :return: A tuple containing the list of third-party agents and their labels.
        """

        third_party_agent_names = configs.get("ENABLED_THIRD_PARTY_AGENTS", [])

        self.logger.info(f"Enabled third-party agents: {third_party_agent_names}")

        third_party_agent_list = []
        third_party_agent_labels = []

        for i, agentname in enumerate(third_party_agent_names):
            label = str(i + start_index)
            third_party_agent_list.append(
                {
                    "label": label,
                    "control_type": "ThirdPartyAgent",
                    "control_text": agentname,
                }
            )
            third_party_agent_labels.append(label)

        return third_party_agent_list, third_party_agent_labels

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

        windows_num = len(self._desktop_windows_info)
        third_party_agent_list, third_party_agent_labels = (
            self._create_third_party_agent_list(start_index=windows_num + 1)
        )

        self.full_desktop_windows_info = (
            self._desktop_windows_info + third_party_agent_list
        )

        # print(f"Full desktop windows info: {self.full_desktop_windows_info}")

        self.third_party_agent_labels = third_party_agent_labels

        # Construct the prompt message for the host agent.
        self._prompt_message = self.host_agent.message_constructor(
            image_list=[self._desktop_screen_url],
            os_info=self.full_desktop_windows_info,
            plan=self.prev_plan,
            prev_subtask=self.previous_subtasks,
            request=self.request,
            blackboard_prompt=blackboard_prompt,
        )

        # print(f"Prompt message: {self._prompt_message}")

        request_data = HostAgentRequestLog(
            step=self.session_step,
            image_list=[
                self.session_data_manager.session_data.state.desktop_screen_url
            ],
            os_info=self.full_desktop_windows_info,
            plan=self.prev_plan,
            prev_subtask=self.previous_subtasks,
            request=self.request,
            blackboard_prompt=blackboard_prompt,
            prompt=self._prompt_message,
        )

        # Log the prompt message. Only save them in debug mode.
        request_log_str = json.dumps(asdict(request_data), ensure_ascii=False)
        self.request_logger.debug(request_log_str)

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

        self._response_json = self.host_agent.response_to_dict(self._response)

        self.control_label = self._response_json.get("ControlLabel", "")
        self.control_text = self._response_json.get("ControlText", "")
        self.subtask = self._response_json.get("CurrentSubtask", "")
        self.host_message = self._response_json.get("Message", [])

        # Convert the plan from a string to a list if the plan is a string.
        self.plan = self.string2list(self._response_json.get("Plan", ""))
        self._response_json["Plan"] = self.plan

        self.status = self._response_json.get("Status", "")
        self.question_list = self._response_json.get("Questions", [])
        self.bash_command = self._response_json.get("Bash", None)

        self.host_agent.print_response(self._response_json)

    @BaseProcessor.exception_capture
    @BaseProcessor.method_timer
    async def execute_action(self) -> None:
        """
        Execute the action.
        """

        if self.control_label:
            if self.control_label in self.third_party_agent_labels:

                self.assigned_third_party_agent = next(
                    (
                        info
                        for info in self.full_desktop_windows_info
                        if info["label"] == self.control_label
                    ),
                    None,
                ).get("control_text", None)

            else:
                await self._select_application(self.control_label)

        if self.bash_command:
            await self._run_shell_command(self.bash_command)

        if not self.control_label and not self.bash_command:
            self.status = self._agent_status_manager.FINISH.value
            return

    async def _select_application(self, window_label: str) -> None:

        result = await self.context.message_bus.publish_commands(
            [
                Command(
                    tool_name="select_application_window",
                    parameters={"window_label": window_label},
                    tool_type="action",
                )
            ]
        )

        self.app_root = result[0].result.get("root_name", "")
        control_info = result[0].result.get("window_info", {})

        self.logger.info(
            f"Selected application process name: {self.control_label}, root name: {self.app_root}"
        )

        action = OneStepAction(
            control_label=self.control_label,
            control_text=self.control_text,
            after_status=self.status,
            function="set_focus",
        )

        action.control_log = BaseControlLog(
            control_class=control_info.get("class_name"),
            control_type=control_info.get("control_type"),
            control_automation_id=control_info.get("automation_id"),
        )

        self.actions = [action]

        self.context.set(ContextNames.APPLICATION_ROOT_NAME, self.app_root)
        self.context.set(ContextNames.APPLICATION_PROCESS_NAME, self.control_text)

    async def _run_shell_command(self, command: str) -> None:

        result = await self.context.message_bus.publish_commands(
            [
                Command(
                    tool_name="run_shell",
                    parameters={"bash_command": command},
                    tool_type="action",
                )
            ]
        )

        self.logger.info(f"Executed shell command: {command}")

        self.actions = [
            OneStepAction(
                function="run_shell",
                args={"command": self.bash_command},
                after_status=self.status,
                control_label=self.control_label,
                control_text=self.control_text,
            )
        ]

        self.actions[0].results = ActionExecutionLog(
            status=self.status,
            error=result[0].error,
            return_value=result[0].result,
        )

    def sync_memory(self):
        """
        Sync the memory of the HostAgent.
        """
        action_seq = ActionSequence(self.actions)

        additional_memory = HostAgentAdditionalMemory(
            Step=self.session_step,
            RoundStep=self.round_step,
            AgentStep=self.host_agent.step,
            Round=self.round_num,
            ControlLabel=self.control_label,
            SubtaskIndex=-1,
            FunctionCall=action_seq.get_function_calls(),
            Action=action_seq.to_list_of_dicts(),
            ActionType="Bash" if self.bash_command else "UIControl",
            Request=self.request,
            Agent="HostAgent",
            AgentName=self.host_agent.name,
            Application=self.app_root,
            Cost=self._cost,
            Results=action_seq.get_results(),
            error=self._exeception_traceback,
            time_cost=self._time_cost,
            ControlLog=action_seq.get_control_logs(),
        )

        self.add_to_memory(self._response_json)
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
