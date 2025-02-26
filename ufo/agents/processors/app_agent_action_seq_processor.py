# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.


from typing import Any, Dict, List

from ufo import utils
from ufo.agents.processors.actions import ActionSequence, OneStepAction
from ufo.agents.processors.app_agent_processor import AppAgentProcessor
from ufo.agents.processors.basic import BaseProcessor
from ufo.config.config import Config

configs = Config.get_instance().config_data


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

        self.app_agent.print_response(self._response_json, print_action=False)

    @BaseProcessor.exception_capture
    @BaseProcessor.method_timer
    def execute_action(self) -> None:
        """
        Execute the action.
        """

        action_sequence_dicts = self._response_json.get("ActionList", [])
        action_list = [
            OneStepAction(
                function=action_dict.get("Function", ""),
                args=action_dict.get("Args", {}),
                control_label=action_dict.get("ControlLabel", ""),
                control_text=action_dict.get("ControlText", ""),
                after_status=action_dict.get("Status", "CONTINUE"),
            )
            for action_dict in action_sequence_dicts
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

        if self.is_application_closed():
            utils.print_with_color("Warning: The application is closed.", "yellow")
            self.status = "FINISH"

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
