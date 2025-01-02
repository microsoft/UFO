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
    ActionExecutionLog,
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
        success_list: List[Dict[str, Any]] = []
        control_log_list: List[Dict[str, Any]] = []

        action_sequence = self._response_json.get("ActionList", [])

        early_stop = False

        for action_dict in enumerate(action_sequence):
            action = OneStepAction(**action_dict)
            execution_log, control_log = self.single_action_flow(action, early_stop)
            outcome_list.append(asdict(execution_log))
            control_log_list.append(asdict(control_log))

            if execution_log.status == "error":
                early_stop = True
            if not early_stop:
                success_list.append(asdict(execution_log))

        self._results = outcome_list
        self._control_logs = control_log_list
