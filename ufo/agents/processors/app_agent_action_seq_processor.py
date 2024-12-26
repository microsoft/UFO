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

        control_selected = self._annotation_dict.get(self._control_label, None)
        # Save the screenshot of the tagged selected control.
        self.capture_control_screenshot(control_selected)

        self.app_agent.Puppeteer.receiver_manager.create_ui_control_receiver(
            control_selected, self.application_window
        )

        if self._operation:

            if configs.get("SHOW_VISUAL_OUTLINE_ON_SCREEN", True):
                control_selected.draw_outline(colour="red", thickness=3)
                time.sleep(configs.get("RECTANGLE_TIME", 0))

            if control_selected:
                control_coordinates = PhotographerDecorator.coordinate_adjusted(
                    self.application_window.rectangle(),
                    control_selected.rectangle(),
                )

                self._control_log = AppAgentControlLog(
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
            else:
                self._control_log = AppAgentControlLog()

            if self.status.upper() == self._agent_status_manager.SCREENSHOT.value:
                self.handle_screenshot_status()
            else:
                self._results = self.app_agent.Puppeteer.execute_command(
                    self._operation, self._args
                )
                self.control_reannotate = None
            if not utils.is_json_serializable(self._results):
                self._results = ""

                return

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
