# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from logging import Logger
from typing import Any, Dict, List, Optional, Type, Union

from pywinauto.controls.uiawrapper import UIAWrapper

from ufo.utils import is_json_serializable, print_with_color


class ContextNames(Enum):
    """
    The context names.
    """

    ID = "ID"  # The ID of the session
    MODE = "MODE"  # The mode of the session
    LOG_PATH = "LOG_PATH"  # The folder path to store the logs
    REQUEST = "REQUEST"  # The current request
    SUBTASK = "SUBTASK"  # The current subtask processed by the AppAgent
    PREVIOUS_SUBTASKS = (
        "PREVIOUS_SUBTASKS"  # The previous subtasks processed by the AppAgent
    )
    HOST_MESSAGE = "HOST_MESSAGE"  # The message from the HostAgent sent to the AppAgent
    REQUEST_LOGGER = "REQUEST_LOGGER"  # The logger for the LLM request
    LOGGER = "LOGGER"  # The logger for the session
    EVALUATION_LOGGER = "EVALUATION_LOGGER"  # The logger for the evaluation
    ROUND_STEP = "ROUND_STEP"  # The step of all rounds
    SESSION_STEP = "SESSION_STEP"  # The step of the current session
    CURRENT_ROUND_ID = "CURRENT_ROUND_ID"  # The ID of the current round
    APPLICATION_WINDOW = "APPLICATION_WINDOW"  # The window of the application
    APPLICATION_PROCESS_NAME = (
        "APPLICATION_PROCESS_NAME"  # The process name of the application
    )
    APPLICATION_ROOT_NAME = "APPLICATION_ROOT_NAME"  # The root name of the application
    CONTROL_REANNOTATION = "CONTROL_REANNOTATION"  # The re-annotation of the control provided by the AppAgent
    SESSION_COST = "SESSION_COST"  # The cost of the session
    ROUND_COST = "ROUND_COST"  # The cost of all rounds
    ROUND_SUBTASK_AMOUNT = (
        "ROUND_SUBTASK_AMOUNT"  # The amount of subtasks in all rounds
    )
    CURRENT_ROUND_STEP = "CURRENT_ROUND_STEP"  # The step of the current round
    CURRENT_ROUND_COST = "CURRENT_ROUND_COST"  # The cost of the current round
    CURRENT_ROUND_SUBTASK_AMOUNT = (
        "CURRENT_ROUND_SUBTASK_AMOUNT"  # The amount of subtasks in the current round
    )
    STRUCTURAL_LOGS = "STRUCTURAL_LOGS"  # The structural logs of the session

    @property
    def default_value(self) -> Any:
        """
        Get the default value for the context name based on its type.
        :return: The default value for the context name.
        """
        if (
            self == ContextNames.LOG_PATH
            or self == ContextNames.REQUEST
            or self == ContextNames.APPLICATION_PROCESS_NAME
            or self == ContextNames.APPLICATION_ROOT_NAME
            or self == ContextNames.MODE
            or self == ContextNames.SUBTASK
        ):
            return ""
        elif (
            self == ContextNames.SESSION_STEP
            or self == ContextNames.CURRENT_ROUND_ID
            or self == ContextNames.CURRENT_ROUND_STEP
            or self == ContextNames.CURRENT_ROUND_SUBTASK_AMOUNT
            or self == ContextNames.ID
        ):
            return 0
        elif (
            self == ContextNames.SESSION_COST or self == ContextNames.CURRENT_ROUND_COST
        ):
            return 0.0
        elif (
            self == ContextNames.ROUND_STEP
            or self == ContextNames.ROUND_COST
            or self == ContextNames.ROUND_SUBTASK_AMOUNT
        ):
            return {}
        elif (
            self == ContextNames.CONTROL_REANNOTATION
            or self == ContextNames.HOST_MESSAGE
            or self == ContextNames.PREVIOUS_SUBTASKS
        ):
            return []
        elif (
            self == ContextNames.REQUEST_LOGGER
            or self == ContextNames.LOGGER
            or self == ContextNames.EVALUATION_LOGGER
        ):
            return None  # Assuming Logger should be initialized elsewhere
        elif self == ContextNames.APPLICATION_WINDOW:
            return None  # Assuming UIAWrapper should be initialized elsewhere
        elif self == ContextNames.STRUCTURAL_LOGS:
            return defaultdict(lambda: defaultdict(list))
        else:
            return None

    @property
    def type(self) -> Type:
        """
        Get the type of the context name.
        :return: The type of the context name.
        """
        if (
            self == ContextNames.LOG_PATH
            or self == ContextNames.REQUEST
            or self == ContextNames.APPLICATION_PROCESS_NAME
            or self == ContextNames.APPLICATION_ROOT_NAME
            or self == ContextNames.MODE
            or self == ContextNames.SUBTASK
        ):
            return str
        elif (
            self == ContextNames.SESSION_STEP
            or self == ContextNames.CURRENT_ROUND_ID
            or self == ContextNames.CURRENT_ROUND_STEP
            or self == ContextNames.ID
            or self == ContextNames.ROUND_SUBTASK_AMOUNT
        ):
            return int
        elif (
            self == ContextNames.SESSION_COST or self == ContextNames.CURRENT_ROUND_COST
        ):
            return float
        elif (
            self == ContextNames.ROUND_STEP
            or self == ContextNames.ROUND_COST
            or self == ContextNames.CURRENT_ROUND_SUBTASK_AMOUNT
            or self == ContextNames.STRUCTURAL_LOGS
        ):
            return dict
        elif (
            self == ContextNames.CONTROL_REANNOTATION
            or self == ContextNames.HOST_MESSAGE
            or self == ContextNames.PREVIOUS_SUBTASKS
        ):
            return list
        elif (
            self == ContextNames.REQUEST_LOGGER
            or self == ContextNames.LOGGER
            or self == ContextNames.EVALUATION_LOGGER
        ):
            return Logger
        elif self == ContextNames.APPLICATION_WINDOW:
            return UIAWrapper
        else:
            return Any


@dataclass
class Context:
    """
    The context class that maintains the context for the session and agent.
    """

    _context: Dict[str, Any] = field(
        default_factory=lambda: {name.name: name.default_value for name in ContextNames}
    )

    def get(self, key: ContextNames) -> Any:
        """
        Get the value from the context.
        :param key: The context name.
        :return: The value from the context.
        """
        # Sync the current round step and cost
        self._sync_round_values()
        return self._context.get(key.name)

    def set(self, key: ContextNames, value: Any) -> None:
        """
        Set the value in the context.
        :param key: The context name.
        :param value: The value to set in the context.
        """
        if key.name in self._context:
            self._context[key.name] = value
            # Sync the current round step and cost
            if key == ContextNames.CURRENT_ROUND_STEP:
                self.current_round_step = value
            if key == ContextNames.CURRENT_ROUND_COST:
                self.current_round_cost = value
            if key == ContextNames.CURRENT_ROUND_SUBTASK_AMOUNT:
                self.current_round_subtask_amount = value
        else:
            raise KeyError(f"Key '{key}' is not a valid context name.")

    def _sync_round_values(self):
        """
        Sync the current round step and cost.
        """
        self.set(ContextNames.CURRENT_ROUND_STEP, self.current_round_step)
        self.set(ContextNames.CURRENT_ROUND_COST, self.current_round_cost)
        self.set(
            ContextNames.CURRENT_ROUND_SUBTASK_AMOUNT, self.current_round_subtask_amount
        )

    def update_dict(self, key: ContextNames, value: Dict[str, Any]) -> None:
        """
        Add a dictionary to a context key. The value and the context key should be dictionaries.
        :param key: The context key to update.
        :param value: The dictionary to add to the context key.
        """
        if key.name in self._context:
            context_value = self._context[key.name]
            if isinstance(value, dict) and isinstance(context_value, dict):
                self._context[key.name].update(value)
            else:
                raise TypeError(
                    f"Value for key '{key.name}' is {key.value}, requires a dictionary."
                )
        else:
            raise KeyError(f"Key '{key.name}' is not a valid context name.")

    @property
    def current_round_cost(self) -> Optional[float]:
        """
        Get the current round cost.
        """
        return self._context.get(ContextNames.ROUND_COST.name).get(
            self._context.get(ContextNames.CURRENT_ROUND_ID.name), 0
        )

    @current_round_cost.setter
    def current_round_cost(self, value: Optional[float]) -> None:
        """
        Set the current round cost.
        :param value: The value to set.
        """
        current_round_id = self._context.get(ContextNames.CURRENT_ROUND_ID.name)
        self._context[ContextNames.ROUND_COST.name][current_round_id] = value

    @property
    def current_round_step(self) -> int:
        """
        Get the current round step.
        """
        return self._context.get(ContextNames.ROUND_STEP.name).get(
            self._context.get(ContextNames.CURRENT_ROUND_ID.name), 0
        )

    @current_round_step.setter
    def current_round_step(self, value: int) -> None:
        """
        Set the current round step.
        :param value: The value to set.
        """
        current_round_id = self._context.get(ContextNames.CURRENT_ROUND_ID.name)
        self._context[ContextNames.ROUND_STEP.name][current_round_id] = value

    @property
    def current_round_subtask_amount(self) -> int:
        """
        Get the current round subtask index.
        """
        return self._context.get(ContextNames.ROUND_SUBTASK_AMOUNT.name).get(
            self._context.get(ContextNames.CURRENT_ROUND_ID.name), 0
        )

    @current_round_subtask_amount.setter
    def current_round_subtask_amount(self, value: int) -> None:
        """
        Set the current round subtask index.
        :param value: The value to set.
        """
        current_round_id = self._context.get(ContextNames.CURRENT_ROUND_ID.name)
        self._context[ContextNames.ROUND_SUBTASK_AMOUNT.name][current_round_id] = value

    def add_to_structural_logs(self, data: Dict[str, Any]) -> None:
        """
        Add data to the structural logs.
        :param data: The data to add to the structural logs.
        """

        round_key = data.get("Round", None)
        subtask_key = data.get("SubtaskIndex", None)

        if round_key is None or subtask_key is None:
            return

        remaining_items = {key: data[key] for key in data}
        self._context[ContextNames.STRUCTURAL_LOGS.name][round_key][subtask_key].append(
            remaining_items
        )

    def filter_structural_logs(
        self, round_key: int, subtask_key: int, keys: Union[str, List[str]]
    ) -> Union[List[Any], List[Dict[str, Any]]]:
        """
        Filter the structural logs.
        :param round_key: The round key.
        :param subtask_key: The subtask key.
        :param keys: The keys to filter.
        :return: The filtered structural logs.
        """

        structural_logs = self._context[ContextNames.STRUCTURAL_LOGS.name][round_key][
            subtask_key
        ]

        if isinstance(keys, str):
            return [log[keys] for log in structural_logs]
        elif isinstance(keys, list):
            return [{key: log[key] for key in keys} for log in structural_logs]
        else:
            raise TypeError(f"Keys should be a string or a list of strings.")

    def to_dict(self, ensure_serializable: bool = False) -> Dict[str, Any]:
        """
        Convert the context to a dictionary.
        :param ensure_serializable: Ensure the context is serializable.
        :return: The dictionary of the context.
        """

        import copy

        context_dict = copy.deepcopy(self._context)

        if ensure_serializable:

            for key in ContextNames:
                if key.name in context_dict:
                    print_with_color(
                        f"Warn: The value of Context.{key.name} is not serializable.",
                        "yellow",
                    )
                    if not is_json_serializable(context_dict[key.name]):

                        context_dict[key.name] = None

        return context_dict

    def from_dict(self, context_dict: Dict[str, Any]) -> None:
        """
        Load the context from a dictionary.
        :param context_dict: The dictionary of the context.
        """
        for key in ContextNames:
            if key.name in context_dict:
                self._context[key.name] = context_dict.get(key.name)

        # Sync the current round step and cost
        self._sync_round_values()
