# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import logging
import platform
from typing import Any, Dict, Optional, TYPE_CHECKING

# Conditional import for Windows-specific packages
if TYPE_CHECKING or platform.system() == "Windows":
    from pywinauto.controls.uiawrapper import UIAWrapper
else:
    UIAWrapper = Any

from ufo import utils
from ufo.agents.processors.schemas.actions import ActionCommandInfo, BaseControlLog
from ufo.automator.puppeteer import AppPuppeteer


class ActionExecutor:
    """
    Execution logic for ActionCommandInfo.
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    @staticmethod
    def _control_validation(control: UIAWrapper) -> bool:
        """
        Validate the action.
        :param control: The control to validate.
        :return: The validation result.
        """
        try:
            control.is_enabled()
            if control.is_enabled() and control.is_visible():
                return True
            else:
                return False
        except:
            return False

    @staticmethod
    def _get_control_log(
        action: ActionCommandInfo,
        control_selected: Optional[UIAWrapper] = None,
        application_window: Optional[UIAWrapper] = None,
    ) -> BaseControlLog:
        """
        Get the control log data for the selected control.
        :param action: The action being executed.
        :param control_selected: The selected control item.
        :param application_window: The application window where the control is located.
        :return: The control log data for the selected control.
        """

        if not control_selected or not application_window:
            return BaseControlLog()

        control_coordinates = utils.coordinate_adjusted(
            application_window.rectangle(), control_selected.rectangle()
        )

        control_log = BaseControlLog(
            control_name=control_selected.element_info.name,
            control_class=control_selected.element_info.class_name,
            control_type=control_selected.element_info.control_type,
            control_matched=(
                control_selected.element_info.name == action.target.name
                if action.target
                else False
            ),
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

    def execute(
        self,
        action: ActionCommandInfo,
        puppeteer: AppPuppeteer,
        control_dict: Dict[str, UIAWrapper],
        application_window: Optional[UIAWrapper] = None,
    ) -> Any:
        """
        Execute the action flow.
        :param action: The action to execute.
        :param puppeteer: The puppeteer that controls the application.
        :param control_dict: The control dictionary.
        :param application_window: The application window where the control is located.
        :return: The action result.
        """
        control_id = action.target.id if action.target else None

        control_selected = control_dict.get(control_id, None)

        # If the control is selected, but not available, return an error.
        if control_selected is not None and not ActionExecutor._control_validation(
            control_selected
        ):
            raise ValueError(
                f"Control {control_id}: {action.target.name} is not available or not interactable for the action {action.action_representation()}, please refresh the application state to get the latest interactable control information."
            )

        # Create the control receiver.
        if application_window:
            puppeteer.receiver_manager.create_ui_control_receiver(
                control_selected, application_window
            )
            self.logger.info(
                f"Create AppPuppeteer for window: {application_window.window_text()}"
            )

        self.logger.info(f"Available commands: {puppeteer.list_commands()}")

        if not action.function:
            return None

        try:
            result = puppeteer.execute_command(action.function, action.arguments)
            if not utils.is_json_serializable(result):
                result = ""

            return result
        except Exception as e:
            raise RuntimeError(f"Failed to execute action {action.function}: {e}")
