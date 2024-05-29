# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from dataclasses import dataclass, field
from enum import Enum
from logging import Logger
from typing import Any, Dict, List, Optional, Type

from pywinauto.controls.uiawrapper import UIAWrapper


class ContextNames(Enum):
    """The context names."""

    LOG_PATH = "LOG_PATH"
    REQUEST = "REQUEST"
    REQUEST_LOGGER = "REQUEST_LOGGER"
    LOGGER = "LOGGER"
    EVALUATION_LOGGER = "EVALUATION_LOGGER"
    ROUND_STEP = "ROUND_STEP"
    SESSION_STEP = "SESSION_STEP"
    CURRENT_ROUND_ID = "CURRENT_ROUND_ID"
    APPLICATION_WINDOW = "APPLICATION_WINDOW"
    APPLICATION_PROCESS_NAME = "APPLICATION_PROCESS_NAME"
    APPLICATION_ROOT_NAME = "APPLICATION_ROOT_NAME"
    CONTROL_REANNOTATION = "CONTROL_REANNOTATION"
    SESSION_COST = "SESSION_COST"
    ROUND_COST = "ROUND_COST"
    CURRENT_ROUND_STEP = "CURRENT_ROUND_STEP"
    CURRENT_ROUND_COST = "CURRENT_ROUND_COST"

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
        ):
            return ""
        elif (
            self == ContextNames.SESSION_STEP
            or self == ContextNames.CURRENT_ROUND_ID
            or self == ContextNames.CURRENT_ROUND_STEP
        ):
            return 0
        elif (
            self == ContextNames.SESSION_COST or self == ContextNames.CURRENT_ROUND_COST
        ):
            return 0.0
        elif self == ContextNames.ROUND_STEP or self == ContextNames.ROUND_COST:
            return {}
        elif self == ContextNames.CONTROL_REANNOTATION:
            return []
        elif (
            self == ContextNames.REQUEST_LOGGER
            or self == ContextNames.LOGGER
            or self == ContextNames.EVALUATION_LOGGER
        ):
            return None  # Assuming Logger should be initialized elsewhere
        elif self == ContextNames.APPLICATION_WINDOW:
            return None  # Assuming UIAWrapper should be initialized elsewhere
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
        ):
            return str
        elif (
            self == ContextNames.SESSION_STEP
            or self == ContextNames.CURRENT_ROUND_ID
            or self == ContextNames.CURRENT_ROUND_STEP
        ):
            return int
        elif (
            self == ContextNames.SESSION_COST or self == ContextNames.CURRENT_ROUND_COST
        ):
            return float
        elif self == ContextNames.ROUND_STEP or self == ContextNames.ROUND_COST:
            return dict
        elif self == ContextNames.CONTROL_REANNOTATION:
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
    """The context."""

    _context: Dict[str, Any] = field(
        default_factory=lambda: {name.name: name.default_value for name in ContextNames}
    )

    def get(self, key: ContextNames) -> Any:
        """Get the value from the context."""
        # Sync the current round step and cost
        self._sync_round_values()
        return self._context.get(key.name)

    def set(self, key: ContextNames, value: Any) -> None:
        """Set the value in the context."""
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
        """Sync the current round step and cost."""
        self.set(ContextNames.CURRENT_ROUND_STEP, self.current_round_step)
        self.set(ContextNames.CURRENT_ROUND_COST, self.current_round_cost)

    def update_dict(self, key: ContextNames, value: Dict[str, Any]) -> None:
        """Add a dictionary to the context."""
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
        """Get the current round cost."""
        return self._context.get(ContextNames.ROUND_COST.name).get(
            self._context.get(ContextNames.CURRENT_ROUND_ID.name), 0
        )

    @current_round_cost.setter
    def current_round_cost(self, value: Optional[float]) -> None:
        """Set the current round cost."""
        current_round_id = self._context.get(ContextNames.CURRENT_ROUND_ID.name)
        self._context[ContextNames.ROUND_COST.name][current_round_id] = value

    @property
    def current_round_step(self) -> int:
        """Get the current round step."""
        return self._context.get(ContextNames.ROUND_STEP.name).get(
            self._context.get(ContextNames.CURRENT_ROUND_ID.name), 0
        )

    @current_round_step.setter
    def current_round_step(self, value: int) -> None:
        """Set the current round step."""
        current_round_id = self._context.get(ContextNames.CURRENT_ROUND_ID.name)
        self._context[ContextNames.ROUND_STEP.name][current_round_id] = value

    def to_dict(self) -> Dict[str, Any]:
        """Convert the context to a dictionary."""
        return self._context
