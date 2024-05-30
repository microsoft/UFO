# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.


import json
import os
import time
from typing import TYPE_CHECKING, Dict, List, Tuple

from pywinauto.controls.uiawrapper import UIAWrapper

from ufo import utils
from ufo.agents.memory.memory import MemoryItem
from ufo.agents.processors.basic import BaseProcessor
from ufo.automator.ui_control.control_filter import ControlFilterFactory
from ufo.config.config import Config
from ufo.module import interactor
from ufo.module.context import Context

if TYPE_CHECKING:
    from ufo.agents.agent.app_agent import AppAgent

configs = Config.get_instance().config_data
BACKEND = configs["CONTROL_BACKEND"]


class AppAgentProcessor(BaseProcessor):
    """
    The processor for the app agent at a single step.
    """

    def __init__(self, agent: "AppAgent", context: Context) -> None:
        """
        Initialize the app agent processor.
        :param agent: The app agent who executes the processor.
        :param context: The context of the session.
        :param control_reannotate: The control items to reannotate.
        """

        super().__init__(agent=agent, context=context)

        self.app_agent = agent
        self.host_agent = agent.host

        # self._init_processor_from_context()

        self._annotation_dict = None
        self._control_info = None
        self._operation = None
        self._args = None
        self._image_url = []
        self.prev_plan = []
        self.control_filter_factory = ControlFilterFactory()
        self.filtered_annotation_dict = None

    def print_step_info(self) -> None:
        """
        Print the step information.
        """
        utils.print_with_color(
            "Round {round_num}, Step {step}: Taking an action on application {application}.".format(
                round_num=self.round_num + 1,
                step=self.round_step + 1,
                application=self.application_process_name,
            ),
            "magenta",
        )

    def capture_screenshot(self) -> None:
        """
        Capture the screenshot.
        """

        # Define the paths for the screenshots saved.
        screenshot_save_path = self.log_path + f"action_step{self.session_step}.png"
        annotated_screenshot_save_path = (
            self.log_path + f"action_step{self.session_step}_annotated.png"
        )
        concat_screenshot_save_path = (
            self.log_path + f"action_step{self.session_step}_concat.png"
        )

        # Get the control elements in the application window if the control items are not provided for reannotation.
        if type(self.control_reannotate) == list and len(self.control_reannotate) > 0:
            control_list = self.control_reannotate
        else:
            control_list = self.control_inspector.find_control_elements_in_descendants(
                self.application_window,
                control_type_list=configs["CONTROL_LIST"],
                class_name_list=configs["CONTROL_LIST"],
            )

        # Get the annotation dictionary for the control items, in a format of {control_label: control_element}.
        self._annotation_dict = self.photographer.get_annotation_dict(
            self.application_window, control_list, annotation_type="number"
        )

        self.prev_plan = self.get_prev_plan()

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

        # If the configuration is set to include the last screenshot with selected controls tagged, save the last screenshot.
        if configs["INCLUDE_LAST_SCREENSHOT"]:
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
        if configs["CONCAT_SCREENSHOT"]:
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
        if configs["LOG_XML"]:

            self._save_to_xml()

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

    def get_prompt_message(self) -> None:
        """
        Get the prompt message for the AppAgent.
        """

        examples, tips = self.demonstration_prompt_helper()

        # Get the external knowledge prompt for the AppAgent using the offline and online retrievers.
        external_knowledge_prompt = self.app_agent.external_knowledge_prompt_helper(
            self.request,
            configs["RAG_OFFLINE_DOCS_RETRIEVED_TOPK"],
            configs["RAG_ONLINE_RETRIEVED_TOPK"],
        )

        # Get the action history and request history of the host agent and feed them into the prompt message.

        action_history = self.host_agent.get_global_action_memory().to_json()
        request_history = self.host_agent.get_request_history_memory().to_json()

        # Construct the prompt message for the AppAgent.
        self._prompt_message = self.app_agent.message_constructor(
            examples,
            tips,
            external_knowledge_prompt,
            self._image_url,
            request_history,
            action_history,
            self.filtered_control_info,
            self.prev_plan,
            self.request,
            configs["INCLUDE_LAST_SCREENSHOT"],
        )

        # Log the prompt message. Only save them in debug mode.
        log = json.dumps(
            {
                "step": self.session_step,
                "prompt": self._prompt_message,
                "control_items": self._control_info,
                "filted_control_items": self.filtered_control_info,
                "status": "",
            }
        )
        self.request_logger.debug(log)

    def get_response(self) -> None:
        """
        Get the response from the LLM.
        """

        # Try to get the response from the LLM. If an error occurs, catch the exception and log the error.
        try:
            self._response, self.cost = self.app_agent.get_response(
                self._prompt_message, "APPAGENT", use_backup_engine=True
            )

        except Exception:
            self.llm_error_handler()
            return

    def parse_response(self) -> None:
        """
        Parse the response.
        """

        # Try to parse the response. If an error occurs, catch the exception and log the error.
        try:
            self._response_json = self.app_agent.response_to_dict(self._response)

        except Exception:
            self.general_error_handler()

        self._control_label = self._response_json.get("ControlLabel", "")
        self.control_text = self._response_json.get("ControlText", "")
        self._operation = self._response_json.get("Function", "")
        self._args = utils.revise_line_breaks(self._response_json.get("Args", ""))

        # Convert the plan from a string to a list if the plan is a string.
        self._plan = self.string2list(self._response_json.get("Plan", ""))
        self._response_json["Plan"] = self._plan

        self.status = self._response_json.get("Status", "")

        self.app_agent.print_response(self._response_json)

    def execute_action(self) -> None:
        """
        Execute the action.
        """

        try:
            # Get the selected control item from the annotation dictionary and LLM response.
            # The LLm response is a number index corresponding to the key in the annotation dictionary.
            control_selected = self._annotation_dict.get(self._control_label, "")

            if control_selected:
                control_selected.draw_outline(colour="red", thickness=3)
                time.sleep(configs.get("RECTANGLE_TIME", 0))

            self.app_agent.Puppeteer.receiver_manager.create_ui_control_receiver(
                control_selected, self.application_window
            )

            # Save the screenshot of the tagged selected control.
            self.capture_control_screenshot(control_selected)

            # Compose the function call and the arguments string.
            self._action = self.app_agent.Puppeteer.get_command_string(
                self._operation, self._args
            )

            # Whether to proceed with the action.
            should_proceed = True

            # Safe guard for the action.
            if (
                self.status.upper() == self._agent_status_manager.PENDING.value
                and configs["SAFE_GUARD"]
            ):
                should_proceed = self._safe_guard_judgement(
                    self._action, self.control_text
                )

            # Execute the action if the user decides to proceed or safe guard is not enabled.
            if should_proceed:
                self._results = self.app_agent.Puppeteer.execute_command(
                    self._operation, self._args
                )
                if not utils.is_json_serializable(self._results):
                    self._results = ""
            else:
                self._results = "The user decide to stop the task."

                return

            # Handle the case when the annotation is overlapped and the agent is unable to select the control items.
            self.handle_screenshot_status()

        except Exception:
            self.general_error_handler()

    def capture_control_screenshot(self, control_selected: UIAWrapper) -> None:
        """
        Capture the screenshot of the selected control.
        :param control_selected: The selected control item.
        """
        control_screenshot_save_path = (
            self.log_path + f"action_step{self.session_step}_selected_controls.png"
        )
        self.photographer.capture_app_window_screenshot_with_rectangle(
            self.application_window,
            sub_control_list=[control_selected],
            save_path=control_screenshot_save_path,
        )

    def handle_screenshot_status(self) -> None:
        """
        Handle the screenshot status when the annotation is overlapped and the agent is unable to select the control items.
        """

        if self.status.upper() == self._agent_status_manager.SCREENSHOT.value:
            utils.print_with_color(
                "Annotation is overlapped and the agent is unable to select the control items. New annotated screenshot is taken.",
                "magenta",
            )
            self.control_reannotate = self.app_agent.Puppeteer.execute_command(
                "annotation", self._args, self._annotation_dict
            )
            if self.control_reannotate is None or len(self.control_reannotate) == 0:
                self.status = self._agent_status_manager.CONTINUE.value
        else:
            self.control_reannotate = None

    def update_memory(self) -> None:
        """
        Update the memory of the Agent.
        """
        # Create a memory item for the app agent
        app_agent_step_memory = MemoryItem()

        app_root = self.control_inspector.get_application_root_name(
            self.application_window
        )

        # Log additional information for the app agent.
        additional_memory = {
            "Step": self.session_step,
            "RoundStep": self.round_step,
            "AgentStep": self.app_agent.step,
            "Round": self.round_num,
            "Action": self._action,
            "ActionType": self.app_agent.Puppeteer.get_command_types(self._operation),
            "Request": self.request,
            "Agent": "ActAgent",
            "AgentName": self.app_agent.name,
            "Application": app_root,
            "Cost": self._cost,
            "Results": self._results,
        }
        app_agent_step_memory.set_values_from_dict(self._response_json)
        app_agent_step_memory.set_values_from_dict(additional_memory)

        self.app_agent.add_memory(app_agent_step_memory)

        # Log the memory item.
        self.log(app_agent_step_memory.to_dict())

        # Only memorize the keys in the HISTORY_KEYS list to feed into the prompt message in the future steps.
        memorized_action = {
            key: app_agent_step_memory.to_dict().get(key)
            for key in configs["HISTORY_KEYS"]
        }
        self.host_agent.add_global_action_memory(memorized_action)

        # Save the screenshot to the blackboard if the SaveScreenshot flag is set to True by the AppAgent.
        self._update_image_blackboard()

    def update_status(self) -> None:
        """
        Update the status of the session.
        """

        self.app_agent.step += 1
        self.app_agent.status = self.status

        if self.status != self._agent_status_manager.FINISH.value:
            time.sleep(configs["SLEEP_TIME"])

    def _update_image_blackboard(self) -> None:
        """
        Save the screenshot to the blackboard if the SaveScreenshot flag is set to True by the AppAgent.
        """
        screenshot_saving = self._response_json.get("SaveScreenshot", {})

        if screenshot_saving.get("save", False):

            screenshot_save_path = self.log_path + f"action_step{self.session_step}.png"
            metadata = {
                "screenshot application": self.process_name,
                "saving reason": screenshot_saving.get("reason", ""),
            }
            self.app_agent.blackboard.add_image(screenshot_save_path, metadata)

    def _safe_guard_judgement(self, action: str, control_text: str) -> bool:
        """
        Safe guard for the session.
        action: The action to be taken.
        control_text: The text of the control item.
        return: The boolean value indicating whether to proceed or not.
        """

        # Ask the user whether to proceed with the action when the status is PENDING.
        decision = interactor.sensitive_step_asker(action, control_text)
        if not decision:
            utils.print_with_color("The user decide to stop the task.", "magenta")
            self.status = self._agent_status_manager.FINISH.value
            return False

        # Handle the PENDING_AND_FINISH case
        elif (
            len(self._plan) > 0
            and self._agent_status_manager.FINISH.value in self._plan[0]
        ):
            self.status = self._agent_status_manager.FINISH.value
        return True

    def _save_to_xml(self) -> None:
        """
        Save the XML file for the current state. Only work for COM objects.
        """
        log_abs_path = os.path.abspath(self.log_path)
        xml_save_path = os.path.join(
            log_abs_path, f"xml/action_step{self.session_step}.xml"
        )
        self.app_agent.Puppeteer.save_to_xml(xml_save_path)

    def get_control_reannotate(self) -> List[UIAWrapper]:
        """
        Get the control to reannotate.
        :return: The control to reannotate.
        """

        return self.control_reannotate

    def get_prev_plan(self) -> str:
        """
        Retrieves the previous plan from the agent's memory.
        :return: The previous plan, or an empty string if the agent's memory is empty.
        """
        agent_memory = self.app_agent.memory

        if agent_memory.length > 0:
            prev_plan = agent_memory.get_latest_item().to_dict()["Plan"]
        else:
            prev_plan = []

        return prev_plan

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
        self, annotation_dict: Dict[str, UIAWrapper]
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
