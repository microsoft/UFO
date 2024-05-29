# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from dataclasses import dataclass, field
from enum import Enum
from logging import Logger
from typing import Any, Dict, List, Optional, Type

from pywinauto.controls.uiawrapper import UIAWrapper


class ContextNames(Enum):
    """
    The context names.
    """

    # The context name for the session.
    LOG_PATH = str
    REQUEST = str
    REQUEST_LOGGER = Logger
    LOGGER = Logger
    ROUND_STEP = Dict[int, int]
    SESSION_STEP = int
    CURRENT_ROUND_ID = int
    APPLICATION_WINDOW = UIAWrapper
    APPLICATION_PROCESS_NAME = str
    APPLICATION_ROOT_NAME = str
    CONTROL_REANNOTATION = List[str]
    SESSION_COST = Optional[float]
    ROUND_COST = Dict[int, Optional[float]]
    CURRENT_ROUND_STEP = int
    CURRENT_ROUND_COST = Optional[float]

    @property
    def default_value(self) -> Any:
        """
        Get the default value for the context name based on its type.
        :return: The default value.
        """
        if self.value == str:
            return ""
        elif self.value == int:
            return 0
        elif self.value == float or self.value == Optional[float]:
            return 0.0
        elif (
            self.value == dict
            or self.value == Dict[int, int]
            or self.value == Dict[int, Optional[float]]
        ):
            return {}
        elif self.value == list or self.value == List[str]:
            return []
        elif self.value == Logger:
            return None  # Assuming Logger should be initialized elsewhere
        elif self.value == UIAWrapper:
            return None  # Assuming UIAWrapper should be initialized elsewhere
        else:
            return None

    @property
    def type(self) -> Type:
        """
        Get the type of the context name.
        :return: The type.
        """
        return self.value


@dataclass
class Context:
    """
    The context.
    """

    _context: Dict[str, Any] = field(
        default_factory=lambda: {name.name: name.default_value for name in ContextNames}
    )

    def get(self, key: ContextNames) -> Any:
        """
        Get the value from the context.
        :param key: The key.
        :return: The value.
        """

        # Sync the current round step and cost
        self._sync_round_values()

        return self._context.get(key.name)

    def set(self, key: ContextNames, value: Any) -> None:
        """
        Set the value in the context.
        :param key: The key as an Enum member.
        :param value: The value.
        """
        if key.name in self._context:
            self._context[key.name] = value

            # Sync the current round step and cost
            if key == ContextNames.CURRENT_ROUND_STEP:
                self.current_round_step = value
            if key == ContextNames.CURRENT_ROUND_COST:
                self.current_round_cost = value
        else:
            raise KeyError(f"Key '{key}' is not a valid context name.")

    def _sync_round_values(self):
        """
        Sync the current round step and cost.
        """
        self.set(ContextNames.CURRENT_ROUND_STEP, self.current_round_step)
        self.set(ContextNames.CURRENT_ROUND_COST, self.current_round_cost)

    def update_dict(self, key: ContextNames, value: Dict[str, Any]) -> None:
        """
        Add a dictionary to the context.
        :param key: The key.
        :param value: The dictionary to add.
        """

        if key.name in self._context:

            context_value = self._context[key.name]

            if isinstance(value, dict) and isinstance(key, context_value):
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
        :return: The current round cost.
        """
        return self._context.get(ContextNames.ROUND_COST.name).get(
            ContextNames.CURRENT_ROUND_ID.name, 0
        )

    @current_round_cost.setter
    def current_round_cost(self, value: Optional[float]) -> None:
        """
        Set the current round cost.
        :param value: The current round cost.
        """
        current_round_id = self._context.get(ContextNames.CURRENT_ROUND_ID.name)
        self._context[ContextNames.ROUND_COST.name][current_round_id] = value

    @property
    def current_round_step(self) -> int:
        """
        Get the current round step.
        :return: The current round step.
        """
        return self._context.get(ContextNames.ROUND_STEP.name).get(
            ContextNames.CURRENT_ROUND_ID.name, 0
        )

    @current_round_step.setter
    def current_round_step(self, value: int) -> None:
        """
        Set the current round step.
        :param value: The current round step.
        """

        current_round_id = self._context.get(ContextNames.CURRENT_ROUND_ID.name)

        self._context[ContextNames.ROUND_STEP.name][current_round_id] = value

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the context to a dictionary.
        :return: The dictionary.
        """
        return self._context
