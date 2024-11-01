# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List


class RobinActionSequenceGenerator:
    """
    Generate a sequence of actions from a list of Robin actions.
    """

    def __init__(self, source: str = "Recorder"):
        """
        Initialize the generator.
        :param source: The source of the actions.
        """

        self.source = "'{}'".format(source)
        self.prefix = f"@@source: {self.source}"

    def generate(self, actions: List[RobinAction]) -> str:
        """
        Generate a sequence of actions from a list of Robin actions.
        :param actions: The list of Robin actions.
        :return: The sequence of actions.
        """

        robin_script = ""

        for action in actions:
            robin_script += f"{self.prefix}\n{action.to_string()}\n"

        return robin_script

    def generate_and_save(self, actions: List[RobinAction], file_path: str):
        """
        Generate a sequence of actions from a list of Robin actions and save it to a file.
        :param actions: The list of Robin actions.
        :param file_path: The file path to save the sequence of actions.
        """

        robin_script = self.generate(actions)

        with open(file_path, "w") as file:
            file.write(robin_script)


class RobinAction(ABC):
    """
    Robin action class. Represents an action used by Microsoft Power Automate Desktop.
    """

    def __init__(self, action_type: str, parameters: Dict[str, Any]):
        """
        Initialize the Robin action.
        :param action_type: The type of the action.
        """
        self._action_type = action_type
        self._parameters = parameters

    @property
    def action_type(self) -> str:
        """
        Get the type of the action.
        :return: The type of the action.
        """
        return self._action_type

    @property
    def parameters(self) -> Dict[str, Any]:
        """
        Get the parameters of the action.
        :return: The parameters of the action.
        """
        return self._parameters

    def to_string(self) -> str:
        """
        Convert the action to a string.
        :return: The string representation of the action.
        """

        parameters_str = " ".join(
            f"{key}: {value}" for key, value in self.parameters.items()
        )

        return f"{self.action_type} {parameters_str}"


if __name__ == "__main__":
    # Create a sequence generator
    sequence_generator = RobinActionSequenceGenerator()

    # Create a list of Robin actions
    actions = [
        RobinAction("Click", {"x": 100, "y": 200}),
        RobinAction("Type", {"text": "Hello, World!"}),
        RobinAction("Wait", {"seconds": 2}),
    ]

    # Generate and save the sequence of actions to a file
    result = sequence_generator.generate(actions)
    print(result)
