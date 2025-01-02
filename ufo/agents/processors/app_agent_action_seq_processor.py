# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.


import json
import os
import time
from dataclasses import asdict, dataclass, field
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

from pywinauto.controls.uiawrapper import UIAWrapper

from ufo import utils
from ufo.agents.processors.basic import BaseProcessor
from ufo.agents.processors.app_agent_processor import (
    AppAgentProcessor,
    OneStepAction,
    AppAgentAdditionalMemory,
    AppAgentControlLog,
)
from ufo.automator.ui_control import ui_tree
from ufo.automator.ui_control.control_filter import ControlFilterFactory
from ufo.automator.ui_control.screenshot import PhotographerDecorator
from ufo.config.config import Config
from ufo.module.context import Context, ContextNames


if TYPE_CHECKING:
    from ufo.agents.agent.app_agent import AppAgent

configs = Config.get_instance().config_data
if configs is not None:
    BACKEND = configs["CONTROL_BACKEND"]


class AppAgentActionSequenceProcessor(AppAgentProcessor):
    """
    The processor for the app agent at a single step.
    """

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

    @BaseProcessor.exception_capture
    @BaseProcessor.method_timer
    def execute_action(self) -> None:
        """
        Execute the action.
        """

        outcome_list: List[Dict[str, Any]] = []

        action_sequence = self._response_json.get("ActionList", [])
        for action_dict in action_sequence:
            action = OneStepAction(**action_dict)
            outcome = self.single_action_flow(action)
            outcome_list.append(outcome)
            if outcome["status"] == "error":
                self._results = outcome["error"]
                break

    def single_action_flow(self, action: OneStepAction) -> Dict[str, Any]:
        """
        Execute a single action.
        :param action: The action to execute.
        :return: The execution result.
        """
        control_selected: UIAWrapper = self._annotation_dict.get(
            action.control_label, None
        )

        if control_selected is not None:
            try:
                control_selected.is_enabled()
            except:
                return {
                    "status": "error",
                    "error": "Control is not available.",
                    "results": "",
                    "control_log": AppAgentControlLog(),
                }

        self.app_agent.Puppeteer.receiver_manager.create_ui_control_receiver(
            control_selected, self.application_window
        )

        self.capture_control_screenshot(control_selected)

        if action.function:

            if configs.get("SHOW_VISUAL_OUTLINE_ON_SCREEN", True):
                if control_selected:
                    control_selected.draw_outline(colour="red", thickness=3)
                    time.sleep(configs.get("RECTANGLE_TIME", 0))

            control_log = self._get_control_log(control_selected)

            results = self.app_agent.Puppeteer.execute_command(
                self._operation, self._args
            )

            if not utils.is_json_serializable(self._results):
                results = ""

            return {
                "status": "success",
                "error": "",
                "results": results,
                "control_log": control_log,
            }

    def capture_control_screenshot(self, control_selected: UIAWrapper) -> None:
        """
        Capture the screenshot of the selected control.
        :param control_selected: The selected control item.
        """
        control_screenshot_save_path = (
            self.log_path + f"action_step{self.session_step}_selected_controls.png"
        )

        self._memory_data.add_values_from_dict(
            {"SelectedControlScreenshot": control_screenshot_save_path}
        )

        self.photographer.capture_app_window_screenshot_with_rectangle(
            self.application_window,
            sub_control_list=[control_selected],
            save_path=control_screenshot_save_path,
        )

    def action_validation(self, action: Dict[str, Any]) -> bool:
        """
        Validate the action.
        :param action: The action to validate.
        :return: The validation result.
        """
        pass
