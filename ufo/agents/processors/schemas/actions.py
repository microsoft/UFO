# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from ufo.agents.processors.schemas.target import TargetInfo
from aip.messages import Result, ResultStatus
from rich.console import Console
from rich.panel import Panel

console = Console()


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


class ActionCommandInfo(BaseModel):
    """
    The action information data.
    """

    function: str = ""
    status: str = ""
    arguments: Dict[str, Any] = Field(default_factory=dict)
    target: Optional[TargetInfo] = None
    result: Result = Field(default_factory=lambda: Result(status="none"))
    action_string: str = ""
    action_representation: str = ""

    def model_post_init(self, __context: Any) -> None:
        """
        Initialize the action string.
        """
        self.action_string = ActionCommandInfo.to_string(self.function, self.arguments)

    @staticmethod
    def to_string(command_name: str, params: Dict[str, Any]) -> str:
        """
        Generate a function call string.
        """
        args_str = ", ".join(f"{k}={v!r}" for k, v in params.items())
        return f"{command_name}({args_str})"

    def to_representation(self) -> str:
        """
        Generate a function call representation string.
        """
        components = []
        components.append(f"[Action] {self.action_string}")
        if self.target:
            target_info = ", ".join(
                f"{k}={v}"
                for k, v in self.target.model_dump(exclude_none=True).items()
                if k not in {"rect"}  # rect is not needed in representation
            )
            components.append(f"[Target] {target_info}")

        if self.result:
            components.append(f"[Status] {self.result.status}")
            if self.result.error:
                components.append(f"[Error] {self.result.error}")
            components.append(f"[Result] {self.result.result}")

        return "\n".join(components)


class ListActionCommandInfo:
    """
    A sequence of one-step actions.
    """

    def __init__(self, actions: Optional[List[ActionCommandInfo]] = None):

        if actions is None:
            actions = []

        self._actions = actions
        self._length = len(actions)

    @property
    def actions(self) -> List[ActionCommandInfo]:
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
        if not self.actions:
            status = "FINISH"
        else:
            status = "CONTINUE"
            for action in self.actions:
                if action.result.status == ResultStatus.SUCCESS:
                    status = action.status

        return status

    def add_action(self, action: ActionCommandInfo) -> None:
        """
        Add an action.
        :param action: The action.
        """
        self._actions.append(action)

    def to_list_of_dicts(
        self,
        success_only: bool = False,
        keep_keys: Optional[List[str]] = None,
        previous_actions: Optional[List[ActionCommandInfo | Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Convert the action sequence to a dictionary.
        :param success_only: Whether to convert the successful actions only.
        :param previous_actions: The previous actions for repeat count calculation.
        :return: The dictionary of the action sequence.
        """

        action_list = []
        for action in self.actions:
            if success_only and action.result.status != ResultStatus.SUCCESS:
                continue
            action_dict = action.model_dump()
            if keep_keys:
                action_dict = {k: v for k, v in action_dict.items() if k in keep_keys}
            if previous_actions:
                repeat_time = self.count_repeat_times(action, previous_actions)
                action_dict["repeat_time"] = repeat_time
            action_list.append(action_dict)
        return action_list

    def to_string(
        self,
        success_only: bool = False,
        previous_actions: Optional[List[ActionCommandInfo]] = None,
    ) -> str:
        """
        Convert the action sequence to a string.
        :param success_only: Whether to convert the successful actions only.
        :param previous_actions: The previous actions.
        :return: The string of the action sequence.
        """
        return json.dumps(
            self.to_list_of_dicts(success_only, previous_actions), ensure_ascii=False
        )

    def to_representation(
        self,
        success_only: bool = False,
    ) -> List[str]:
        """
        Convert the action sequence to a representation string.
        :param success_only: Whether to convert the successful actions only.
        :return: The representation string of the action sequence.
        """
        representations = []
        for action in self.actions:
            if success_only and action.result.status != ResultStatus.SUCCESS:
                continue
            representations.append(action.to_representation())
        return representations

    def color_print(self, success_only: bool = False) -> None:
        """
        Pretty-print the action sequence using presenter.
        :param success_only: Whether to print only successful actions.
        """
        from ufo.agents.presenters import PresenterFactory
        
        presenter = PresenterFactory.create_presenter("rich")
        presenter.present_action_list(self, success_only=success_only)

    @staticmethod
    def is_same_action(
        action1: ActionCommandInfo | Dict[str, Any],
        action2: ActionCommandInfo | Dict[str, Any],
    ) -> bool:
        """
        Check whether the two actions are the same.
        :param action1: The first action to compare.
        :param action2: The second action to compare.
        :return: Whether the two actions are the same.
        """

        if isinstance(action1, ActionCommandInfo):
            action_dict_1 = action1.model_dump()
        else:
            action_dict_1 = action1

        if isinstance(action2, ActionCommandInfo):
            action_dict_2 = action2.model_dump()
        else:
            action_dict_2 = action2

        return action_dict_1.get("function") == action_dict_2.get(
            "function"
        ) and action_dict_1.get("arguments") == action_dict_2.get("arguments")

    def count_repeat_times(
        self,
        target_action: ActionCommandInfo,
        previous_actions: List[ActionCommandInfo | Dict[str, Any]],
    ) -> int:
        """
        Get the times of the same action in the previous actions.
        :param target_action: The target action to count.
        :param previous_actions: The previous actions.
        :return: The times of the same action in the previous actions.
        """

        count = 0
        for action in previous_actions[::-1]:
            if self.is_same_action(action, target_action):
                count += 1
            else:
                break
        return count

    def get_results(self, success_only: bool = False) -> List[Dict[str, Any]]:
        """
        Get the results of the actions.
        :param success_only: Whether to get the successful actions only.
        :return: The results of the actions.
        """
        return [
            action.result.model_dump()
            for action in self.actions
            if not success_only or action.result.status == ResultStatus.SUCCESS
        ]

    def get_target_info(self, success_only: bool = False) -> List[Dict[str, Any]]:
        """
        Get the control logs of the actions.
        :param success_only: Whether to get the successful actions only.
        :return: The control logs of the actions.
        """

        target_info = []

        for action in self.actions:
            if not success_only or action.result.status == ResultStatus.SUCCESS:
                if action.target:
                    target_info.append(action.target.model_dump())
                else:
                    target_info.append({})

        return target_info

    def get_target_objects(self, success_only: bool = False) -> List[TargetInfo]:
        """
        Get the control logs of the actions.
        :param success_only: Whether to get the successful actions only.
        :return: The control logs of the actions.
        """
        target_objects = []

        for action in self.actions:
            if not success_only or action.result.status == ResultStatus.SUCCESS:
                if action.target:
                    target_objects.append(action.target)

        return target_objects

    def get_function_calls(self, is_success_only: bool = False) -> List[str]:
        """
        Get the function calls of the actions.
        :param is_success_only: Whether to get the successful actions only.
        :return: The function calls of the actions.
        """
        return [
            action.action_string
            for action in self.actions
            if not is_success_only or action.result.status == ResultStatus.SUCCESS
        ]
