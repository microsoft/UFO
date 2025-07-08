# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import json
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from ufo.config import Config


@dataclass
class BaseControlLog:
    """
    The control log data for the HostAgent.
    """

    control_name: str = ""
    control_class: str = ""
    control_type: str = ""
    control_automation_id: str = ""
    control_friendly_class_name: str = ""
    control_matched: bool = True
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
    traceback: str = ""
    return_value: Any = None


class OneStepAction:
    """
    A single action that can be executed.
    """

    def __init__(
        self,
        function: str = "",
        args: Dict[str, Any] = {},
        control_label: str = "",
        control_text: str = "",
        after_status: str = "",
        results: Optional[ActionExecutionLog] = None,
        configs=Config.get_instance().config_data,
    ):
        self._function = function
        self._args = args
        self._control_label = control_label
        self._control_text = control_text
        self._after_status = after_status
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
    def after_status(self) -> str:
        """
        Get the status.
        :return: The status.
        """
        return self._after_status

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
        :return: The function call string.
        """
        # Format the arguments
        args_str = ", ".join(f"{k}={v!r}" for k, v in self.args.items())

        # Return the function call string
        return f"{self.function}({args_str})"

    def is_same_action(self, action_to_compare: Dict[str, Any]) -> bool:
        """
        Check whether the two actions are the same.
        :param action_to_compare: The action to compare with the current action.
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
            "Status": self.after_status,
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

    def get_operation_point_list(self) -> List[Tuple[int]]:
        """
        Get the operation points of the action.
        :return: The operation points of the action.
        """

        if "path" in self.args:
            return [(point["x"], point["y"]) for point in self.args["path"]]
        elif "x" in self.args and "y" in self.args:
            return [(self.args["x"], self.args["y"])]
        else:
            return []


class ActionSequence:
    """
    A sequence of one-step actions.
    """

    def __init__(self, actions: Optional[List[OneStepAction]] = None):

        if not actions:
            actions = []
            self._status = "FINISH"
        else:
            self._status = actions[0].after_status

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
