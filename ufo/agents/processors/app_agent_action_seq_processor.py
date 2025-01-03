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
)

from ufo.agents.processors.actions import (
    ActionExecutionLog,
    ActionSequence,
    BaseControlLog,
    OneStepAction,
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

        self.question_list = self._response_json.get("Questions", [])

        # Convert the plan from a string to a list if the plan is a string.
        self.plan = self.string2list(self._response_json.get("Plan", ""))
        self._response_json["Plan"] = self.plan

        self.app_agent.print_action_sequence_response(self._response_json)

    @BaseProcessor.exception_capture
    @BaseProcessor.method_timer
    def execute_action(self) -> None:
        """
        Execute the action.
        """

        action_sequence_dicts = self._response_json.get("ActionList", [])
        action_list = [
            OneStepAction(**action_dict) for action_dict in action_sequence_dicts
        ]
        self.actions = ActionSequence(action_list)
        self.function_calls = self.actions.get_function_calls()

        self.actions.execute_all(
            puppeteer=self.app_agent.Puppeteer,
            control_dict=self._annotation_dict,
            application_window=self.application_window,
        )

        self.status = self.actions.status

        success_control_adjusted_coords = self.actions.get_success_control_coords()
        self.capture_control_screenshot_from_adjusted_coords(
            control_adjusted_coords=success_control_adjusted_coords
        )

        self.actions.print_all_results()

    def capture_control_screenshot_from_adjusted_coords(
        self, control_adjusted_coords: List[Dict[str, Any]]
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
        self.photographer.capture_app_window_screenshot_with_rectangle_from_adjusted_coords(
            self.application_window,
            control_adjusted_coords=control_adjusted_coords,
            save_path=control_screenshot_save_path,
            background_screenshot_path=self.screenshot_save_path,
        )
