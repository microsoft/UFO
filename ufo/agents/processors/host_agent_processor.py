# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.


import json
from dataclasses import asdict, dataclass
from typing import TYPE_CHECKING, Any, Dict, List

from ufo import utils
from ufo.agents.processors.basic import BaseProcessor
from ufo.config import Config
from ufo.module.context import Context, ContextNames
from ufo.cs.contracts import CaptureDesktopScreenshotAction, CaptureDesktopScreenshotParams, GetDesktopAppInfoAction, GetDesktopAppInfoParams, LaunchApplicationAction, LaunchApplicationParams, SelectApplicationWindowAction, SelectApplicationWindowParams, WindowInfo

from ufo.llm import AgentType

configs = Config.get_instance().config_data


if TYPE_CHECKING:
    from ufo.agents.agent.host_agent import HostAgent
import os


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
    def capture_screenshot(self) -> None:
        """
        Capture the screenshot.
        """

        desktop_save_path = self.log_path + f"action_step{self.session_step}.png"

        self._memory_data.add_values_from_dict({"CleanScreenshot": desktop_save_path})

        # Capture the desktop screenshot for all screens using action
        desktop_screenshot_action = CaptureDesktopScreenshotAction(
            params=CaptureDesktopScreenshotParams(all_screens=True)
        )

        self.session_data_manager.add_action(
            desktop_screenshot_action, 
            setter=lambda value: self.desktop_screenshot_action_callback(value, desktop_save_path)
        )
        
    def desktop_screenshot_action_callback(self, value: str, path: str) -> None:
        """
        Helper method to save screenshot to specified path and set the URL.
        
        Args:
            value (str): The screenshot data or URL
            path (str): Path to save the screenshot
        """
        # Set the URL for use in the class
        self._desktop_screen_url = value
        self.session_data_manager.session_data.state.desktop_screen_url = value
        
        # If value contains a base64 encoded image string
        if value and isinstance(value, str) and value.startswith("data:image/png;base64,"):
            try:
                # Decode the base64 string to binary data
                img_data = utils.decode_base64_image(value)
                
                # Create directory if it doesn't exist
                os.makedirs(os.path.dirname(path), exist_ok=True)
                
                # Save the image to the specified path
                with open(path, 'wb') as f:
                    f.write(img_data)
                
                print(f"Screenshot saved to {path}")
            except Exception as e:
                print(f"Error saving screenshot: {e}")

    @BaseProcessor.exception_capture
    @BaseProcessor.method_timer
    def get_control_info(self) -> None:
        """
        Get the control information.
        """
        # Get all available windows on the desktop, into a dictionary with format {index: application object}.
        # self._desktop_windows_dict = self.control_inspector.get_desktop_app_dict(
        #     remove_empty=True
        # )
        
        # Get the textual information of all windows.
        # self._desktop_windows_info = self.control_inspector.get_desktop_app_info(
        #     self._desktop_windows_dict
        # )
        
        self.session_data_manager.add_action(
            action=GetDesktopAppInfoAction(
                params=GetDesktopAppInfoParams(
                    remove_empty=True,
                    refresh_app_windows=True
                )
            ),
            setter=lambda value: self.desktop_app_info_callback(value)
        )
        
    def desktop_app_info_callback(self, value: list[dict] | list[WindowInfo]) -> None:
        """
        Helper method to handle the desktop app info callback.
        
        Args:
            value (str): The desktop app info
        """
        if isinstance(value, list) and len(value) > 0 and isinstance(value[0], dict):
            # Convert the list of dictionaries to a list of WindowInfo objects
            self._desktop_windows_info = [WindowInfo(**item) for item in value]
        else:
            self._desktop_windows_info = value
        self.session_data_manager.session_data.state.desktop_windows_info = self._desktop_windows_info

    @BaseProcessor.exception_capture
    @BaseProcessor.method_timer
    def process_collected_info(self) -> None:
        """
        Process the collected information.
        """
        pass

    @BaseProcessor.exception_capture
    @BaseProcessor.method_timer
    def get_prompt_message(self) -> None:
        """
        Get the prompt message.
        """

        if not self.host_agent.blackboard.is_empty():
            blackboard_prompt = self.host_agent.blackboard.blackboard_to_prompt()
        else:
            blackboard_prompt = []

        desktop_windows_info = self.session_data_manager.get_desktop_windows_info()

        # Construct the prompt message for the host agent.
        self._prompt_message = self.host_agent.message_constructor(
            image_list=[self.session_data_manager.session_data.state.desktop_screen_url],
            os_info=desktop_windows_info,
            plan=self.prev_plan,
            prev_subtask=self.previous_subtasks,
            request=self.request,
            blackboard_prompt=blackboard_prompt,
        )

        request_data = HostAgentRequestLog(
            step=self.session_step,
            image_list=[self.session_data_manager.session_data.state.desktop_screen_url],
            os_info=desktop_windows_info,
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
    def get_response(self) -> None:
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
            except Exception as e:
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
    def execute_action(self) -> None:
        """
        Execute the action.
        """
        desktop_windows_info = self.session_data_manager.session_data.state.desktop_windows_info

        print(f"control_label: {self.control_label}")
        new_app_windows = list(filter(lambda x: x.annotation_id == self.control_label, desktop_windows_info))

        if len(new_app_windows) > 0:
            #self._select_application(new_app_window)
            self.session_data_manager.add_action(
                action=SelectApplicationWindowAction(
                    params=SelectApplicationWindowParams(
                        window_label=new_app_windows[0].annotation_id
                    )
                ),
                setter=lambda value: self.select_application_window_callback(value))
        else:
            self.session_data_manager.add_action(
                LaunchApplicationAction(
                    params=LaunchApplicationParams(
                        bash_command=self.bash_command
                    )
                ),
                setter=lambda value: self.launch_application_callback(value))
            
    
    def select_application_window_callback(self, value: dict | WindowInfo) -> None:
        """
        Helper method to handle the application window selection callback.
        
        Args:
            value (str): The application window value
        """
        # Set the application window
        self.app_root = value["process_name"]
        #self.control_text = value["control_text"]
        
        new_app_window = value["window_info"]
        #self.application_window = new_app_window
        if isinstance(new_app_window, dict):
            self.application_window_info = WindowInfo(**new_app_window)
        elif isinstance(new_app_window, WindowInfo):
            self.application_window_info = new_app_window
        
        self.context.set(ContextNames.APPLICATION_WINDOW, self.application_window)
        self.context.set(ContextNames.APPLICATION_ROOT_NAME, self.app_root)
        self.context.set(ContextNames.APPLICATION_PROCESS_NAME, self.control_text)
        
    def launch_application_callback(self, value: dict[str, any]) -> None:
        """
        Helper method to handle the application launch callback.
        
        Args:
            value (str): The application launch value
        """
        # Set the application window
        self.app_root = value["process_name"]
        #self.control_text = value["control_text"]
        
        new_app_window = value["window_info"]
        #self.application_window = new_app_window
        self.application_window_info = WindowInfo(**new_app_window)

        self.context.set(ContextNames.APPLICATION_WINDOW, self.application_window)
        self.context.set(ContextNames.APPLICATION_ROOT_NAME, self.app_root)
        self.context.set(ContextNames.APPLICATION_PROCESS_NAME, self.control_text)
    
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
            ActionType="Bash" if self.bash_command else "UIControl",
            Request=self.request,
            Agent="HostAgent",
            AgentName=self.host_agent.name,
            Application=self.app_root,
            Cost=self._cost,
            Results=self.actions.get_results(),
            error=self._exeception_traceback,
            time_cost=self._time_cost,
            ControlLog=self.actions.get_control_logs(),
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
