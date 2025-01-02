# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.


import json
import os
import time
from dataclasses import asdict, dataclass, field
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple, Union

from pywinauto.controls.uiawrapper import UIAWrapper

from ufo import utils
from ufo.agents.processors.basic import BaseControlLog, BaseProcessor
from ufo.automator.puppeteer import AppPuppeteer
from ufo.automator.ui_control import ui_tree
from ufo.automator.ui_control.control_filter import ControlFilterFactory
from ufo.automator.ui_control.screenshot import PhotographerDecorator
from ufo.config.config import Config
from ufo.module.context import Context, ContextNames

if TYPE_CHECKING:
    from ufo.agents.agent.app_agent import AppAgent

configs = Config.get_instance().config_data
if configs is not None:
    BACKEND = configs.get("CONTROL_BACKEND", "uia")


@dataclass
class AppAgentAdditionalMemory:
    """
    The additional memory data for the AppAgent.
    """

    Step: int
    RoundStep: int
    AgentStep: int
    Round: int
    Subtask: str
    SubtaskIndex: int
    Action: str
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
    UserConfirm: Optional[str] = None


@dataclass
class AppAgentControlLog(BaseControlLog):
    """
    The control log data for the AppAgent.
    """

    control_friendly_class_name: str = ""
    control_coordinates: Dict[str, int] = field(default_factory=dict)


@dataclass
class AppAgentRequestLog:
    """
    The request log data for the AppAgent.
    """

    step: int
    dynamic_examples: List[str]
    dynamic_tips: List[str]
    dynamic_knowledge: List[str]
    image_list: List[str]
    prev_subtask: List[str]
    plan: List[str]
    request: str
    control_info: List[Dict[str, str]]
    subtask: str
    host_message: str
    blackboard_prompt: List[str]
    include_last_screenshot: bool
    prompt: Dict[str, Any]


@dataclass
class ActionExecutionLog:
    """
    The action execution log data.
    """

    status: str = ""
    error: str = ""
    results: str = ""


class OneStepAction:

    def __init__(
        self,
        function: str = "",
        args: Dict[str, Any] = {},
        control_label: str = "",
        control_text: str = "",
        status: str = "",
        results: Optional[str] = None,
    ):
        self._function = function
        self._args = args
        self._control_label = control_label
        self._control_text = control_text
        self._status = status
        self._results = results

    @property
    def function(self) -> str:
        """
        Get the function name.
        :return: The function.
        """
        return self._function

    @property
    def args(self) -> Dict[str, Any]:
        """
        Get the arguments.
        :return: The arguments.
        """
        return self._args

    @property
    def control_label(self) -> str:
        """
        Get the control label.
        :return: The control label.
        """
        return self._control_label

    @property
    def control_text(self) -> str:
        """
        Get the control text.
        :return: The control text.
        """
        return self._control_text

    @property
    def status(self) -> str:
        """
        Get the status.
        :return: The status.
        """
        return self._status

    @property
    def results(self) -> str:
        """
        Get the results.
        :return: The results.
        """
        return self._results

    @results.setter
    def results(self, results: str) -> None:
        """
        Set the results.
        :param results: The results.
        """
        self._results = results

    @classmethod
    def is_same_action(cls, action1: "OneStepAction", action2: "OneStepAction") -> bool:
        """
        Check whether the two actions are the same.
        :param action1: The first action.
        :param action2: The second action.
        :return: Whether the two actions are the same.
        """
        return (
            action1.function == action2.function
            and action1.args == action2.args
            and action1.control_text == action2.control_text
        )

    def count_repeative_times(self, previous_actions: List["OneStepAction"]) -> int:
        """
        Get the times of the same action in the previous actions.
        :param previous_actions: The previous actions.
        :return: The times of the same action in the previous actions.
        """
        return sum(
            1 for action in previous_actions if self.is_same_action(self, action)
        )

    def to_dict(
        self, previous_actions: Optional[List["OneStepAction"]]
    ) -> Dict[str, Any]:
        """
        Convert the action to a dictionary.
        :param previous_actions: The previous actions.
        :return: The dictionary of the action.
        """

        action_dict = {
            "Function": self.function,
            "Args": self.args,
            "ControlLabel": self.control_label,
            "ControlText": self.control_text,
            "Status": self.status,
            "Results": self.results,
        }

        # Add the repetitive times of the same action in the previous actions if the previous actions are provided.
        if previous_actions:
            action_dict["RepetitiveTimes"] = self.count_repeative_times(
                previous_actions
            )

        return action_dict

    def to_string(self, previous_actions: Optional[List["OneStepAction"]]) -> str:
        """
        Convert the action to a string.
        :param previous_actions: The previous actions.
        :return: The string of the action.
        """
        return json.dumps(self.to_dict(previous_actions), ensure_ascii=False)

    def execute(self, puppeteer: AppPuppeteer) -> Any:
        """
        Execute the action.
        :param executor: The executor.
        """
        return puppeteer.execute_command(self.function, self.args)


class AppAgentProcessor(BaseProcessor):
    """
    The processor for the app agent at a single step.
    """

    def __init__(self, agent: "AppAgent", context: Context) -> None:
        """
        Initialize the app agent processor.
        :param agent: The app agent who executes the processor.
        :param context: The context of the session.
        """

        super().__init__(agent=agent, context=context)

        self.app_agent = agent
        self.host_agent = agent.host

        self._annotation_dict = None
        self._control_info = None
        self._operation = None
        self._args = None
        self._image_url = []
        self.control_filter_factory = ControlFilterFactory()
        self.filtered_annotation_dict = None
        self.screenshot_save_path = None

    @property
    def action(self) -> str:
        """
        Get the action.
        :return: The action.
        """
        return self._action

    @action.setter
    def action(self, action: str) -> None:
        """
        Set the action.
        :param action: The action.
        """
        self._action = action

    def print_step_info(self) -> None:
        """
        Print the step information.
        """
        utils.print_with_color(
            "Round {round_num}, Step {step}, AppAgent: Completing the subtask [{subtask}] on application [{application}].".format(
                round_num=self.round_num + 1,
                step=self.round_step + 1,
                subtask=self.subtask,
                application=self.application_process_name,
            ),
            "magenta",
        )

    @BaseProcessor.exception_capture
    @BaseProcessor.method_timer
    def capture_screenshot(self) -> None:
        """
        Capture the screenshot.
        """

        # Define the paths for the screenshots saved.
        screenshot_save_path = self.log_path + f"action_step{self.session_step}.png"
        self.screenshot_save_path = screenshot_save_path

        annotated_screenshot_save_path = (
            self.log_path + f"action_step{self.session_step}_annotated.png"
        )
        concat_screenshot_save_path = (
            self.log_path + f"action_step{self.session_step}_concat.png"
        )

        self._memory_data.add_values_from_dict(
            {
                "CleanScreenshot": screenshot_save_path,
                "AnnotatedScreenshot": annotated_screenshot_save_path,
                "ConcatScreenshot": concat_screenshot_save_path,
            }
        )

        # Get the control elements in the application window if the control items are not provided for reannotation.
        if type(self.control_reannotate) == list and len(self.control_reannotate) > 0:
            control_list = self.control_reannotate
        else:
            control_list = self.control_inspector.find_control_elements_in_descendants(
                self.application_window,
                control_type_list=configs.get("CONTROL_LIST", []),
                class_name_list=configs.get("CONTROL_LIST", []),
            )

        # Get the annotation dictionary for the control items, in a format of {control_label: control_element}.
        self._annotation_dict = self.photographer.get_annotation_dict(
            self.application_window, control_list, annotation_type="number"
        )

        # Attempt to filter out irrelevant control items based on the previous plan.
        self.filtered_annotation_dict = self.get_filtered_annotation_dict(
            self._annotation_dict
        )
        self.photographer.capture_app_window_screenshot(
            self.application_window, save_path=screenshot_save_path
        )

        # Capture the screenshot of the selected control items with annotation and save it.
        self.photographer.capture_app_window_screenshot_with_annotation_dict(
            self.application_window,
            self.filtered_annotation_dict,
            annotation_type="number",
            save_path=annotated_screenshot_save_path,
        )

        if configs.get("SAVE_UI_TREE", False):
            if self.application_window is not None:
                step_ui_tree = ui_tree.UITree(self.application_window)
                step_ui_tree.save_ui_tree_to_json(
                    os.path.join(
                        self.ui_tree_path, f"ui_tree_step{self.session_step}.json"
                    )
                )

        # If the configuration is set to include the last screenshot with selected controls tagged, save the last screenshot.
        if configs.get("INCLUDE_LAST_SCREENSHOT", True):
            last_screenshot_save_path = (
                self.log_path + f"action_step{self.session_step - 1}.png"
            )
            last_control_screenshot_save_path = (
                self.log_path
                + f"action_step{self.session_step - 1}_selected_controls.png"
            )
            self._image_url += [
                self.photographer.encode_image_from_path(
                    last_control_screenshot_save_path
                    if os.path.exists(last_control_screenshot_save_path)
                    else last_screenshot_save_path
                )
            ]

        # Whether to concatenate the screenshots of clean screenshot and annotated screenshot into one image.
        if configs.get("CONCAT_SCREENSHOT", False):
            self.photographer.concat_screenshots(
                screenshot_save_path,
                annotated_screenshot_save_path,
                concat_screenshot_save_path,
            )
            self._image_url += [
                self.photographer.encode_image_from_path(concat_screenshot_save_path)
            ]
        else:
            screenshot_url = self.photographer.encode_image_from_path(
                screenshot_save_path
            )
            screenshot_annotated_url = self.photographer.encode_image_from_path(
                annotated_screenshot_save_path
            )
            self._image_url += [screenshot_url, screenshot_annotated_url]

        # Save the XML file for the current state.
        if configs.get("LOG_XML", False):
            self._save_to_xml()

    @BaseProcessor.exception_capture
    @BaseProcessor.method_timer
    def get_control_info(self) -> None:
        """
        Get the control information.
        """

        # Get the control information for the control items and the filtered control items, in a format of list of dictionaries.
        self._control_info = self.control_inspector.get_control_info_list_of_dict(
            self._annotation_dict,
            ["control_text", "control_type" if BACKEND == "uia" else "control_class"],
        )
        self.filtered_control_info = (
            self.control_inspector.get_control_info_list_of_dict(
                self.filtered_annotation_dict,
                [
                    "control_text",
                    "control_type" if BACKEND == "uia" else "control_class",
                ],
            )
        )

    @BaseProcessor.exception_capture
    @BaseProcessor.method_timer
    def get_prompt_message(self) -> None:
        """
        Get the prompt message for the AppAgent.
        """

        examples, tips = self.demonstration_prompt_helper()

        # Get the external knowledge prompt for the AppAgent using the offline and online retrievers.
        external_knowledge_prompt = self.app_agent.external_knowledge_prompt_helper(
            self.request,
            configs.get("RAG_OFFLINE_DOCS_RETRIEVED_TOPK", 0),
            configs.get("RAG_ONLINE_RETRIEVED_TOPK", 0),
        )

        if not self.app_agent.blackboard.is_empty():
            blackboard_prompt = self.app_agent.blackboard.blackboard_to_prompt()
        else:
            blackboard_prompt = []

        # Construct the prompt message for the AppAgent.
        self._prompt_message = self.app_agent.message_constructor(
            dynamic_examples=examples,
            dynamic_tips=tips,
            dynamic_knowledge=external_knowledge_prompt,
            image_list=self._image_url,
            control_info=self.filtered_control_info,
            prev_subtask=self.previous_subtasks,
            plan=self.prev_plan,
            request=self.request,
            subtask=self.subtask,
            host_message=self.host_message,
            blackboard_prompt=blackboard_prompt,
            include_last_screenshot=configs.get("INCLUDE_LAST_SCREENSHOT", True),
        )

        # Log the prompt message. Only save them in debug mode.
        request_data = AppAgentRequestLog(
            step=self.session_step,
            dynamic_examples=examples,
            dynamic_tips=tips,
            dynamic_knowledge=external_knowledge_prompt,
            image_list=self._image_url,
            prev_subtask=self.previous_subtasks,
            plan=self.prev_plan,
            request=self.request,
            control_info=self.filtered_control_info,
            subtask=self.subtask,
            host_message=self.host_message,
            blackboard_prompt=blackboard_prompt,
            include_last_screenshot=configs.get("INCLUDE_LAST_SCREENSHOT", True),
            prompt=self._prompt_message,
        )

        request_log_str = json.dumps(asdict(request_data), indent=4, ensure_ascii=False)
        self.request_logger.debug(request_log_str)

    @BaseProcessor.exception_capture
    @BaseProcessor.method_timer
    def get_response(self) -> None:
        """
        Get the response from the LLM.
        """

        self._response, self.cost = self.app_agent.get_response(
            self._prompt_message, "APPAGENT", use_backup_engine=True
        )

    @BaseProcessor.exception_capture
    @BaseProcessor.method_timer
    def parse_response(self) -> None:
        """
        Parse the response.
        """

        self._response_json = self.app_agent.response_to_dict(self._response)

        self.control_label = self._response_json.get("ControlLabel", "")
        self.control_text = self._response_json.get("ControlText", "")
        self._operation = self._response_json.get("Function", "")
        self.question_list = self._response_json.get("Questions", [])
        self._args = utils.revise_line_breaks(self._response_json.get("Args", ""))

        # Convert the plan from a string to a list if the plan is a string.
        self.plan = self.string2list(self._response_json.get("Plan", ""))
        self._response_json["Plan"] = self.plan

        # Compose the function call and the arguments string.
        self.action = self.app_agent.Puppeteer.get_command_string(
            self._operation, self._args
        )

        self.status = self._response_json.get("Status", "")
        self.app_agent.print_response(self._response_json)

    # @BaseProcessor.exception_capture
    # @BaseProcessor.method_timer
    # def execute_action(self) -> None:
    #     """
    #     Execute the action.
    #     """

    #     control_selected = self._annotation_dict.get(self._control_label, None)
    #     # Save the screenshot of the tagged selected control.
    #     self.capture_control_screenshot(control_selected)

    #     self.app_agent.Puppeteer.receiver_manager.create_ui_control_receiver(
    #         control_selected, self.application_window
    #     )

    #     if self._operation:

    #         if configs.get("SHOW_VISUAL_OUTLINE_ON_SCREEN", True):
    #             if control_selected:
    #                 control_selected.draw_outline(colour="red", thickness=3)
    #                 time.sleep(configs.get("RECTANGLE_TIME", 0))

    #         self._control_log = self._get_control_log(control_selected)

    #         if self.status.upper() == self._agent_status_manager.SCREENSHOT.value:
    #             self.handle_screenshot_status()
    #         else:
    #             self._results = self.app_agent.Puppeteer.execute_command(
    #                 self._operation, self._args
    #             )
    #             self.control_reannotate = None
    #         if not utils.is_json_serializable(self._results):
    #             self._results = ""

    #             return

    @BaseProcessor.exception_capture
    @BaseProcessor.method_timer
    def execute_action(self) -> None:
        """
        Execute the action.
        """

        action = OneStepAction(
            function=self._operation,
            args=self._args,
            control_label=self._control_label,
            control_text=self.control_text,
            status=self.status,
        )

        execution_log, control_log = self.single_action_flow(action)
        self._results = asdict(execution_log)
        self._control_log = control_log

        control_selected = self._annotation_dict.get(self._control_label, None)
        # Save the screenshot of the tagged selected control.
        self.capture_control_screenshot(control_selected)

    def single_action_flow(
        self, action: OneStepAction, early_stop: bool = False
    ) -> Tuple[ActionExecutionLog, AppAgentControlLog]:
        """
        Execute a single action.
        :param action: The action to execute.
        :param early_stop: Whether to stop the execution.
        :return: The execution result and the control log if available.
        """

        if early_stop:
            return ActionExecutionLog(
                status="error", error="Early stop due to error in previous action."
            )

        control_selected: UIAWrapper = self._annotation_dict.get(
            action.control_label, None
        )

        # If the control is selected, but not available, return an error.
        if control_selected is not None and not self._control_validation(
            control_selected
        ):

            return (
                ActionExecutionLog(
                    status="error",
                    error="Control is not available.",
                ),
                AppAgentControlLog(),
            )

        # Create the control receiver.
        self.app_agent.Puppeteer.receiver_manager.create_ui_control_receiver(
            control_selected, self.application_window
        )

        if action.function:

            if configs.get("SHOW_VISUAL_OUTLINE_ON_SCREEN", True):
                if control_selected:
                    control_selected.draw_outline(colour="red", thickness=3)
                    time.sleep(configs.get("RECTANGLE_TIME", 0))

            control_log = self._get_control_log(control_selected)

            try:
                results = self.app_agent.Puppeteer.execute_command(
                    self._operation, self._args
                )
                if not utils.is_json_serializable(results):
                    results = ""

                return (
                    ActionExecutionLog(
                        status="success",
                        results=results,
                    ),
                    control_log,
                )
            except Exception as e:
                return ActionExecutionLog(status="error", error=str(e)), control_log

    def _control_validation(self, control: UIAWrapper) -> bool:
        """
        Validate the action.
        :param action: The action to validate.
        :return: The validation result.
        """
        try:
            control.is_enabled()
            return True
        except:
            return False

    def _get_control_log(
        self, control_selected: Optional[UIAWrapper]
    ) -> AppAgentControlLog:
        """
        Get the control log data for the selected control.
        :param control_selected: The selected control item.
        :return: The control log data for the selected control.
        """

        if not control_selected:
            return AppAgentControlLog()

        control_coordinates = PhotographerDecorator.coordinate_adjusted(
            self.application_window.rectangle(), control_selected.rectangle()
        )

        control_log = AppAgentControlLog(
            control_class=control_selected.element_info.class_name,
            control_type=control_selected.element_info.control_type,
            control_automation_id=control_selected.element_info.automation_id,
            control_friendly_class_name=control_selected.friendly_class_name(),
            control_coordinates={
                "left": control_coordinates[0],
                "top": control_coordinates[1],
                "right": control_coordinates[2],
                "bottom": control_coordinates[3],
            },
        )

        return control_log

    def capture_control_screenshot(
        self, control_selected: Union[UIAWrapper, List[UIAWrapper]]
    ) -> None:
        """
        Capture the screenshot of the selected control.
        :param control_selected: The selected control item or a list of selected control items.
        """
        control_screenshot_save_path = (
            self.log_path + f"action_step{self.session_step}_selected_controls.png"
        )

        self._memory_data.add_values_from_dict(
            {"SelectedControlScreenshot": control_screenshot_save_path}
        )

        sub_control_list = (
            control_selected
            if isinstance(control_selected, list)
            else [control_selected]
        )

        self.photographer.capture_app_window_screenshot_with_rectangle(
            self.application_window,
            sub_control_list=sub_control_list,
            save_path=control_screenshot_save_path,
            background_screenshot_path=self.screenshot_save_path,
        )

    def handle_screenshot_status(self) -> None:
        """
        Handle the screenshot status when the annotation is overlapped and the agent is unable to select the control items.
        """

        utils.print_with_color(
            "Annotation is overlapped and the agent is unable to select the control items. New annotated screenshot is taken.",
            "magenta",
        )
        self.control_reannotate = self.app_agent.Puppeteer.execute_command(
            "annotation", self._args, self._annotation_dict
        )

    def sync_memory(self):
        """
        Sync the memory of the AppAgent.
        """

        app_root = self.control_inspector.get_application_root_name(
            self.application_window
        )

        action_type = self.app_agent.Puppeteer.get_command_types(self._operation)

        # Create the additional memory data for the log.
        additional_memory = AppAgentAdditionalMemory(
            Step=self.session_step,
            RoundStep=self.round_step,
            AgentStep=self.app_agent.step,
            Round=self.round_num,
            Subtask=self.subtask,
            SubtaskIndex=self.round_subtask_amount,
            Action=self.action,
            ActionType=action_type,
            Request=self.request,
            Agent="AppAgent",
            AgentName=self.app_agent.name,
            Application=app_root,
            Cost=self._cost,
            Results=self._results,
            error=self._exeception_traceback,
            time_cost=self._time_cost,
            ControlLog=asdict(self._control_log),
            UserConfirm=(
                "Yes"
                if self.status.upper()
                == self._agent_status_manager.CONFIRM.value.upper()
                else None
            ),
        )

        # Log the original response from the LLM.
        self.add_to_memory(self._response_json)

        # Log the additional memory data for the AppAgent.
        self.add_to_memory(asdict(additional_memory))

    def update_memory(self) -> None:
        """
        Update the memory of the Agent.
        """

        # Sync the memory of the AppAgent.
        self.sync_memory()

        self.app_agent.add_memory(self._memory_data)

        # Log the memory item.
        self.context.add_to_structural_logs(self._memory_data.to_dict())
        # self.log(self._memory_data.to_dict())

        # Only memorize the keys in the HISTORY_KEYS list to feed into the prompt message in the future steps.
        memorized_action = {
            key: self._memory_data.to_dict().get(key)
            for key in configs.get("HISTORY_KEYS", [])
        }

        if self.is_confirm():

            if self._is_resumed:
                self._memory_data.add_values_from_dict({"UserConfirm": "Yes"})
                memorized_action["UserConfirm"] = "Yes"
            else:
                self._memory_data.add_values_from_dict({"UserConfirm": "No"})
                memorized_action["UserConfirm"] = "No"

        # Save the screenshot to the blackboard if the SaveScreenshot flag is set to True by the AppAgent.
        self._update_image_blackboard()
        self.host_agent.blackboard.add_trajectories(memorized_action)

    def _update_image_blackboard(self) -> None:
        """
        Save the screenshot to the blackboard if the SaveScreenshot flag is set to True by the AppAgent.
        """
        screenshot_saving = self._response_json.get("SaveScreenshot", {})

        if screenshot_saving.get("save", False):

            screenshot_save_path = self.log_path + f"action_step{self.session_step}.png"
            metadata = {
                "screenshot application": self.context.get(
                    ContextNames.APPLICATION_PROCESS_NAME
                ),
                "saving reason": screenshot_saving.get("reason", ""),
            }
            self.app_agent.blackboard.add_image(screenshot_save_path, metadata)

    def _save_to_xml(self) -> None:
        """
        Save the XML file for the current state. Only work for COM objects.
        """
        log_abs_path = os.path.abspath(self.log_path)
        xml_save_path = os.path.join(
            log_abs_path, f"xml/action_step{self.session_step}.xml"
        )
        self.app_agent.Puppeteer.save_to_xml(xml_save_path)

    def demonstration_prompt_helper(self) -> Tuple[List[str], List[str]]:
        """
        Get the examples and tips for the AppAgent using the demonstration retriever.
        :return: The examples and tips for the AppAgent.
        """

        # Get the examples and tips for the AppAgent using the experience and demonstration retrievers.
        if configs["RAG_EXPERIENCE"]:
            experience_examples, experience_tips = (
                self.app_agent.rag_experience_retrieve(
                    self.request, configs["RAG_EXPERIENCE_RETRIEVED_TOPK"]
                )
            )
        else:
            experience_examples = []
            experience_tips = []

        if configs["RAG_DEMONSTRATION"]:
            demonstration_examples, demonstration_tips = (
                self.app_agent.rag_demonstration_retrieve(
                    self.request, configs["RAG_DEMONSTRATION_RETRIEVED_TOPK"]
                )
            )
        else:
            demonstration_examples = []
            demonstration_tips = []

        examples = experience_examples + demonstration_examples
        tips = experience_tips + demonstration_tips

        return examples, tips

    def get_filtered_annotation_dict(
        self, annotation_dict: Dict[str, UIAWrapper], configs=configs
    ) -> Dict[str, UIAWrapper]:
        """
        Get the filtered annotation dictionary.
        :param annotation_dict: The annotation dictionary.
        :return: The filtered annotation dictionary.
        """

        # Get the control filter type and top k plan from the configuration.
        control_filter_type = configs["CONTROL_FILTER_TYPE"]
        topk_plan = configs["CONTROL_FILTER_TOP_K_PLAN"]

        if len(control_filter_type) == 0 or self.prev_plan == []:
            return annotation_dict

        control_filter_type_lower = [
            control_filter_type_lower.lower()
            for control_filter_type_lower in control_filter_type
        ]

        filtered_annotation_dict = {}

        # Get the top k recent plans from the memory.
        plans = self.control_filter_factory.get_plans(self.prev_plan, topk_plan)

        # Filter the annotation dictionary based on the keywords of control text and plan.
        if "text" in control_filter_type_lower:
            model_text = self.control_filter_factory.create_control_filter("text")
            filtered_text_dict = model_text.control_filter(annotation_dict, plans)
            filtered_annotation_dict = (
                self.control_filter_factory.inplace_append_filtered_annotation_dict(
                    filtered_annotation_dict, filtered_text_dict
                )
            )

        # Filter the annotation dictionary based on the semantic similarity of the control text and plan with their embeddings.
        if "semantic" in control_filter_type_lower:
            model_semantic = self.control_filter_factory.create_control_filter(
                "semantic", configs["CONTROL_FILTER_MODEL_SEMANTIC_NAME"]
            )
            filtered_semantic_dict = model_semantic.control_filter(
                annotation_dict, plans, configs["CONTROL_FILTER_TOP_K_SEMANTIC"]
            )
            filtered_annotation_dict = (
                self.control_filter_factory.inplace_append_filtered_annotation_dict(
                    filtered_annotation_dict, filtered_semantic_dict
                )
            )

        # Filter the annotation dictionary based on the icon image icon and plan with their embeddings.
        if "icon" in control_filter_type_lower:
            model_icon = self.control_filter_factory.create_control_filter(
                "icon", configs["CONTROL_FILTER_MODEL_ICON_NAME"]
            )

            cropped_icons_dict = self.photographer.get_cropped_icons_dict(
                self.application_window, annotation_dict
            )
            filtered_icon_dict = model_icon.control_filter(
                annotation_dict,
                cropped_icons_dict,
                plans,
                configs["CONTROL_FILTER_TOP_K_ICON"],
            )
            filtered_annotation_dict = (
                self.control_filter_factory.inplace_append_filtered_annotation_dict(
                    filtered_annotation_dict, filtered_icon_dict
                )
            )

        return filtered_annotation_dict
