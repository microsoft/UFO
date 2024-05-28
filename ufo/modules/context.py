# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from dataclasses import dataclass, field
from enum import Enum
from logging import Logger
from typing import Any, Dict, List, Optional, Type

from pywinauto.controls.uiawrapper import UIAWrapper

from ufo.agents.states.basic import AgentState


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
    STATE = AgentState
    CURRENT_ROUND_ID = int
    APPLICATION_WINDOW = UIAWrapper
    APPLICATION_PROCESS_NAME = str
    APPLICATION_ROOT_NAME = str
    CONTROL_REANNOTATION = List[str]
    SESSION_COST = Optional[float]
    ROUND_COST = Dict[int, Optional[int]]

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
        default_factory=lambda: {name.name: None for name in ContextNames}
    )

    def get(self, key: ContextNames) -> Any:
        """
        Get the value from the context.
        :param key: The key.
        :return: The value.
        """
        return self._context.get(key.name)

    def set(self, key: ContextNames, value: Any) -> None:
        """
        Set the value in the context.
        :param key: The key as an Enum member.
        :param value: The value.
        """
        if key.value in self._context:
            self._context[key.name] = value
        else:
            raise KeyError(f"Key '{key}' is not a valid context name.")

    def add_value(self, key: ContextNames, value: Any) -> None:
        """Add a the value to an existing key in the context.
        :param key: The key.
        :param value: The value to add.
        """
        if key.name in self._context:
            if isinstance(value, key.type):
                try:
                    self._context[key.name] += value
                except TypeError:
                    raise TypeError(
                        f"Value for key '{key.name}' is {type(self._context[key.name])}, not {type(value)}."
                    )
            else:
                raise TypeError(
                    f"Value for key '{key.name}' must be of type {key.type}."
                )
        else:
            raise KeyError(f"Key '{key.name}' is not a valid context name.")

    def update_dict(self, key: ContextNames, value: Dict[str, Any]) -> None:
        """
        Add a dictionary to the context.
        :param key: The key.
        :param value: The dictionary to add.
        """
        if key.name in self._context:
            if isinstance(value, dict) and key.type == dict:
                self._context[key.name].update(value)
            else:
                raise TypeError(f"Value for key '{key.name}' is not a dictionary.")
        else:
            raise KeyError(f"Key '{key.name}' is not a valid context name.")

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the context to a dictionary.
        :return: The dictionary.
        """
        return self._context
