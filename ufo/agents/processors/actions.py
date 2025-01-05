# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.


import sys

sys.path.append("./")


import json
import time
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from pywinauto.controls.uiawrapper import UIAWrapper

from ufo import utils
from ufo.automator.puppeteer import AppPuppeteer
from ufo.automator.ui_control.screenshot import PhotographerDecorator
from ufo.config.config import Config


@dataclass
class BaseControlLog:
    """
    The control log data for the HostAgent.
    """

    control_class: str = ""
    control_type: str = ""
    control_automation_id: str = ""
    control_friendly_class_name: str = ""
    control_coordinates: Dict[str, int] = field(default_factory=dict)

    def is_empty(self) -> bool:

        return self == BaseControlLog()


@dataclass
class ActionExecutionLog:
    """
    The action execution log data.
    """

    status: str = ""
    error: str = ""
    return_value: Any = None


class OneStepAction:

    def __init__(
        self,
        function: str = "",
        args: Dict[str, Any] = {},
        control_label: str = "",
        control_text: str = "",
        status: str = "",
        results: Optional[ActionExecutionLog] = None,
        configs=Config.get_instance().config_data,
    ):
        self._function = function
        self._args = args
        self._control_label = control_label
        self._control_text = control_text
        self._status = status
        self._results = ActionExecutionLog() if results is None else results
        self._configs = configs
        self._control_log = BaseControlLog()

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
    def control_log(self) -> BaseControlLog:
        """
        Get the control log.
        :return: The control log.
        """
        return self._control_log

    @control_log.setter
    def control_log(self, control_log: BaseControlLog) -> None:
        """
        Set the control log.
        :param control_log: The control log.
        """
        self._control_log = control_log

    @property
    def results(self) -> ActionExecutionLog:
        """
        Get the results.
        :return: The results.
        """
        return self._results

    @results.setter
    def results(self, results: ActionExecutionLog) -> None:
        """
        Set the results.
        :param results: The results.
        """
        self._results = results

    @property
    def command_string(self) -> str:
        """
        Generate a function call string.
        :param command_name: The function name.
        :param params: The arguments as a dictionary.
        :return: The function call string.
        """
        # Format the arguments
        args_str = ", ".join(f"{k}={v!r}" for k, v in self.args.items())

        # Return the function call string
        return f"{self.function}({args_str})"

    def is_same_action(self, action_to_compare: Dict[str, Any]) -> bool:
        """
        Check whether the two actions are the same.
        :param action1: The first action.
        :param action2: The second action.
        :return: Whether the two actions are the same.
        """

        return (
            self.function == action_to_compare.get("Function")
            and self.args == action_to_compare.get("Args")
            and self.control_text == action_to_compare.get("ControlText")
        )

    def count_repeat_times(self, previous_actions: List[Dict[str, Any]]) -> int:
        """
        Get the times of the same action in the previous actions.
        :param previous_actions: The previous actions.
        :return: The times of the same action in the previous actions.
        """

        count = 0
        for action in previous_actions[::-1]:
            if self.is_same_action(action):
                count += 1
            else:
                break
        return count

    def to_dict(
        self, previous_actions: Optional[List[Dict[str, Any]]]
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
            "Results": asdict(self.results),
        }

        # Add the repetitive times of the same action in the previous actions if the previous actions are provided.
        if previous_actions:
            action_dict["RepeatTimes"] = self.count_repeat_times(previous_actions)

        return action_dict

    def to_string(self, previous_actions: Optional[List["OneStepAction"]]) -> str:
        """
        Convert the action to a string.
        :param previous_actions: The previous actions.
        :return: The string of the action.
        """
        return json.dumps(self.to_dict(previous_actions), ensure_ascii=False)

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

    def execute(self, puppeteer: AppPuppeteer) -> Any:
        """
        Execute the action.
        :param executor: The executor.
        """
        return puppeteer.execute_command(self.function, self.args)

    def action_flow(
        self,
        puppeteer: AppPuppeteer,
        control_dict: Dict[str, UIAWrapper],
        application_window: UIAWrapper,
    ) -> Tuple[ActionExecutionLog, BaseControlLog]:
        """
        Execute the action flow.
        :param action: The action.
        :param control_dict: The control dictionary.
        :return: The action execution log.
        """
        control_selected: UIAWrapper = control_dict.get(self.control_label, None)

        # If the control is selected, but not available, return an error.
        if control_selected is not None and not self._control_validation(
            control_selected
        ):
            self.results = ActionExecutionLog(
                status="error",
                error="Control is not available.",
            )
            self._control_log = BaseControlLog()

            return self.results

        # Create the control receiver.
        puppeteer.receiver_manager.create_ui_control_receiver(
            control_selected, application_window
        )

        if self.function:

            if self._configs.get("SHOW_VISUAL_OUTLINE_ON_SCREEN", True):
                if control_selected:
                    control_selected.draw_outline(colour="red", thickness=3)
                    time.sleep(self._configs.get("RECTANGLE_TIME", 0))

            self._control_log = self._get_control_log(
                control_selected=control_selected, application_window=application_window
            )

            try:
                return_value = self.execute(puppeteer=puppeteer)
                if not utils.is_json_serializable(return_value):
                    return_value = ""

                self.results = ActionExecutionLog(
                    status="success",
                    return_value=return_value,
                )

            except Exception as e:
                self.results = ActionExecutionLog(
                    status="error",
                    error=str(e),
                )
            return self.results

    def _get_control_log(
        self,
        control_selected: Optional[UIAWrapper],
        application_window: UIAWrapper,
    ) -> BaseControlLog:
        """
        Get the control log data for the selected control.
        :param control_selected: The selected control item.
        :param application_window: The application window where the control is located.
        :return: The control log data for the selected control.
        """

        if not control_selected or not application_window:
            return BaseControlLog()

        control_coordinates = PhotographerDecorator.coordinate_adjusted(
            application_window.rectangle(), control_selected.rectangle()
        )

        control_log = BaseControlLog(
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

    def print_result(self) -> None:
        """
        Print the action execution result.
        """

        utils.print_with_color(
            "Selected item🕹️: {control_text}, Label: {label}".format(
                control_text=self.control_text, label=self.control_label
            ),
            "yellow",
        )
        utils.print_with_color(
            "Action applied⚒️: {action}".format(action=self.command_string), "blue"
        )
        utils.print_with_color(
            "Execution result📜: {result}📜".format(result=asdict(self.results))
        )


class ActionSequence:
    """
    A sequence of one-step actions.
    """

    def __init__(self, actions: Optional[List[OneStepAction]] = []):

        if not actions:
            actions = []
            self._status = "FINISH"
        else:
            self._status = actions[0].status

        self._actions = actions
        self._length = len(actions)

    @property
    def actions(self) -> List[OneStepAction]:
        """
        Get the actions.
        :return: The actions.
        """
        return self._actions

    @property
    def length(self) -> int:
        """
        Get the length of the actions.
        :return: The length of the actions.
        """
        return len(self._actions)

    @property
    def status(self) -> str:
        """
        Get the status of the actions.
        :return: The status of the actions.
        """
        return self._status

    def add_action(self, action: OneStepAction) -> None:
        """
        Add an action.
        :param action: The action.
        """
        self._actions.append(action)

    def to_list_of_dicts(
        self,
        success_only: bool = False,
        previous_actions: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Convert the action sequence to a dictionary.
        :param success_only: Whether to convert the successful actions only.
        :param previous_actions: The previous actions.
        :return: The dictionary of the action sequence.
        """

        action_list = []
        for action in self.actions:
            if success_only and action.results.status != "success":
                continue
            action_list.append(action.to_dict(previous_actions))
        return action_list

    def to_string(self, success_only: bool = False, previous_actions=None) -> str:
        """
        Convert the action sequence to a string.
        :param success_only: Whether to convert the successful actions only.
        :param previous_actions: The previous actions.
        :return: The string of the action sequence.
        """
        return json.dumps(
            self.to_list_of_dicts(success_only, previous_actions), ensure_ascii=False
        )

    def execute_all(
        self,
        puppeteer: AppPuppeteer,
        control_dict: Dict[str, UIAWrapper],
        application_window: UIAWrapper,
    ) -> None:
        """
        Execute all the actions.
        :param puppeteer: The puppeteer.
        :param control_dict: The control dictionary.
        :param application_window: The application window.
        """

        early_stop = False

        for action in self.actions:
            if early_stop:
                action.results = ActionExecutionLog(
                    status="error", error="Early stop due to error in previous action."
                )
            self._status = action.status

            action.action_flow(puppeteer, control_dict, application_window)

            if action.results.status != "success":
                early_stop = True

    def get_results(self, success_only: bool = False) -> List[Dict[str, Any]]:
        """
        Get the results of the actions.
        :param success_only: Whether to get the successful actions only.
        :return: The results of the actions.
        """
        return [
            asdict(action.results)
            for action in self.actions
            if not success_only or action.results.status == "success"
        ]

    def get_control_logs(self, success_only: bool = False) -> List[Dict[str, Any]]:
        """
        Get the control logs of the actions.
        :param success_only: Whether to get the successful actions only.
        :return: The control logs of the actions.
        """
        return [
            asdict(action.control_log)
            for action in self.actions
            if not success_only or action.results.status == "success"
        ]

    def get_success_control_coords(self) -> List[Dict[str, Any]]:
        """
        Get the control coordinates of the successful actions.
        :return: The control coordinates of the successful actions.
        """
        return [
            action.control_log.control_coordinates
            for action in self.actions
            if action.results.status == "success" and not action.control_log.is_empty()
        ]

    def get_function_calls(self, is_success_only: bool = False) -> List[str]:
        """
        Get the function calls of the actions.
        :param is_success_only: Whether to get the successful actions only.
        :return: The function calls of the actions.
        """
        return [
            action.command_string
            for action in self.actions
            if not is_success_only or action.results.status == "success"
        ]

    def print_all_results(self, success_only: bool = False) -> None:
        """
        Print the action execution result.
        """
        index = 1
        for action in self.actions:
            if success_only and action.results.status != "success":
                continue
            utils.print_with_color(f"Action {index}: {action.command_string}", "blue")
            action.print_result()
            index += 1
        utils.print_with_color(f"Final status: {self.status}", "yellow")


if __name__ == "__main__":

    action1 = OneStepAction(
        function="click",
        args={"button": "left"},
        control_label="1",
        control_text="OK",
        status="success",
        results=ActionExecutionLog(status="success"),
    )

    action2 = OneStepAction(
        function="click",
        args={"button": "right"},
        control_label="2",
        control_text="NotOK",
        status="success",
        results=ActionExecutionLog(status="success"),
    )

    action_sequence = ActionSequence([action1, action2])

    previous_actions = [
        {"Function": "click", "Args": {"button": "left"}, "ControlText": "OK"},
        {"Function": "click", "Args": {"button": "right"}, "ControlText": "OK"},
        {"Function": "click", "Args": {"button": "left"}, "ControlText": "OK"},
        {"Function": "click", "Args": {"button": "left"}, "ControlText": "OK"},
    ]

    print(action_sequence.to_list_of_dicts(previous_actions=previous_actions))
