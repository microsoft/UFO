# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import sys

sys.path.append("./")

import time
from dataclasses import asdict
from typing import Any, Dict, Optional, TYPE_CHECKING

from pywinauto.controls.uiawrapper import UIAWrapper

from ufo import utils
from ufo.automator.puppeteer import AppPuppeteer

from ufo.agents.processors.action_contracts import (
    OneStepAction,
    ActionSequence,
    BaseControlLog,
    ActionExecutionLog,
)

# if TYPE_CHECKING:
#     from ufo.agents.processors.action_contracts import (
#         OneStepAction,
#         ActionSequence,
#         BaseControlLog,
#         ActionExecutionLog,
#     )
# else:
#     # Import at runtime to avoid circular imports
#     from ..agents.processors.action_contracts import (
#         OneStepAction,
#         ActionSequence,
#         BaseControlLog,
#         ActionExecutionLog,
#     )


class OneStepActionExecutor:
    """
    Execution logic for OneStepAction.
    """

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
    def execute(action: OneStepAction, puppeteer: AppPuppeteer) -> Any:
        """
        Execute the action.
        :param action: The action to execute.
        :param puppeteer: The puppeteer that controls the application.
        """
        return puppeteer.execute_command(action.function, action.args)

    @staticmethod
    def _get_control_log(
        action: OneStepAction,
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
            control_matched=control_selected.element_info.name == action.control_text,
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

    @staticmethod
    def action_flow(
        action: OneStepAction,
        puppeteer: AppPuppeteer,
        control_dict: Dict[str, UIAWrapper],
        application_window: Optional[UIAWrapper] = None,
    ) -> ActionExecutionLog:
        """
        Execute the action flow.
        :param action: The action to execute.
        :param puppeteer: The puppeteer that controls the application.
        :param control_dict: The control dictionary.
        :param application_window: The application window where the control is located.
        :return: The action execution log.
        """
        control_selected = control_dict.get(action.control_label, None)

        # If the control is selected, but not available, return an error.
        if (
            control_selected is not None
            and not OneStepActionExecutor._control_validation(control_selected)
        ):
            action.results = ActionExecutionLog(
                status="error",
                traceback="Control is not available.",
                error="Control is not available.",
            )
            action.control_log = BaseControlLog()

            return action.results

        import logging

        logger = logging.getLogger(__name__)
        logger.info(
            f"Application window: {application_window}, Control selected: {control_selected}"
        )

        # Create the control receiver.
        if application_window:
            puppeteer.receiver_manager.create_ui_control_receiver(
                control_selected, application_window
            )
            logger.info(
                f"Create AppPuppeteer for window: {application_window.window_text()}"
            )
            logger.info(f"Available commands: {puppeteer.list_commands()}")

        if action.function:

            if action._configs.get("SHOW_VISUAL_OUTLINE_ON_SCREEN", True):
                if control_selected:
                    control_selected.draw_outline(colour="red", thickness=3)
                    time.sleep(action._configs.get("RECTANGLE_TIME", 0))

            action.control_log = OneStepActionExecutor._get_control_log(
                action=action,
                control_selected=control_selected,
                application_window=application_window,
            )

            try:
                return_value = OneStepActionExecutor.execute(
                    action=action, puppeteer=puppeteer
                )
                if not utils.is_json_serializable(return_value):
                    return_value = ""

                action.results = ActionExecutionLog(
                    status="success",
                    return_value=return_value,
                )

            except Exception as e:

                import traceback

                action.results = ActionExecutionLog(
                    status="error",
                    traceback=traceback.format_exc(),
                    error=str(e),
                )
            return action.results

    @staticmethod
    def print_result(action: OneStepAction) -> None:
        """
        Print the action execution result.
        :param action: The action to print results for.
        """

        utils.print_with_color(
            "Selected item🕹️: {control_text}, Label: {label}".format(
                control_text=action.control_text, label=action.control_label
            ),
            "yellow",
        )
        utils.print_with_color(
            "Action applied⚒️: {action}".format(action=action.command_string), "blue"
        )

        result_color = "red" if action.results.status != "success" else "green"

        utils.print_with_color(
            "Execution result📜: {result}".format(result=asdict(action.results)),
            result_color,
        )


class ActionSequenceExecutor:
    """
    Execution logic for ActionSequence.
    """

    @staticmethod
    def execute_all(
        action_sequence: ActionSequence,
        puppeteer: AppPuppeteer,
        control_dict: Dict[str, UIAWrapper],
        application_window: Optional[UIAWrapper] = None,
    ) -> None:
        """
        Execute all the actions.
        :param action_sequence: The action sequence to execute.
        :param puppeteer: The puppeteer.
        :param control_dict: The control dictionary.
        :param application_window: The application window.
        """

        early_stop = False

        for action in action_sequence.actions:
            if early_stop:
                action.results = ActionExecutionLog(
                    status="error", error="Early stop due to error in previous actions."
                )

            else:
                action_sequence._status = action.after_status

                OneStepActionExecutor.action_flow(
                    action, puppeteer, control_dict, application_window
                )

                # Sleep for a while to avoid the UI being too busy.
                time.sleep(0.5)

            if action.results.status != "success":
                early_stop = True

    @staticmethod
    def print_all_results(
        action_sequence: ActionSequence, success_only: bool = False
    ) -> None:
        """
        Print the action execution result.
        :param action_sequence: The action sequence to print results for.
        :param success_only: Whether to print successful actions only.
        """
        index = 1
        for action in action_sequence.actions:
            if success_only and action.results.status != "success":
                continue
            if action_sequence.length > 1:
                utils.print_with_color(f"Action {index}:", "cyan")
            OneStepActionExecutor.print_result(action)
            index += 1
        utils.print_with_color(f"Final status: {action_sequence.status}", "yellow")


# Monkey patch the execution methods back to the contract classes for backward compatibility
def _patch_execution_methods():
    """Add execution methods to the contract classes for backward compatibility."""

    # Add execution methods to OneStepAction
    OneStepAction._control_validation = OneStepActionExecutor._control_validation
    OneStepAction.execute = lambda self, puppeteer: OneStepActionExecutor.execute(
        self, puppeteer
    )
    OneStepAction.action_flow = lambda self, puppeteer, control_dict, application_window: OneStepActionExecutor.action_flow(
        self, puppeteer, control_dict, application_window
    )
    OneStepAction._get_control_log = lambda self, control_selected, application_window: OneStepActionExecutor._get_control_log(
        self, control_selected, application_window
    )
    OneStepAction.print_result = lambda self: OneStepActionExecutor.print_result(self)

    # Add execution methods to ActionSequence
    ActionSequence.execute_all = lambda self, puppeteer, control_dict, application_window: ActionSequenceExecutor.execute_all(
        self, puppeteer, control_dict, application_window
    )
    ActionSequence.print_all_results = (
        lambda self, success_only=False: ActionSequenceExecutor.print_all_results(
            self, success_only
        )
    )


# Apply the patches when this module is imported
_patch_execution_methods()
