# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Type

from ufo.utils import print_with_color


class ReceiverBasic(ABC):
    """
    The abstract receiver interface.
    """

    def __init__(self) -> None:
        """
        Initialize the receiver.
        """

        self.command_registry = self.get_default_command_registry()
        self.supported_command_names = self.get_supported_command_names()

    @abstractmethod
    def get_default_command_registry(self) -> Dict:
        """
        The default command registry.
        """
        pass

    def get_command_registry(self) -> Dict:
        """
        Get the command registry.
        """
        return self.command_registry

    def register_command(self, command_name: str, command: CommandBasic) -> None:
        """
        Add to the command registry.
        :param command_name: The command name.
        :param command: The command.
        """

        self.command_registry[command_name] = command

    def get_supported_command_names(self) -> List[str]:
        """
        Get the command name list.
        """
        return list(self.command_registry.keys())

    def self_command_mapping(self) -> Dict[str, CommandBasic]:
        """
        Get the command-receiver mapping.
        """
        return {command_name: self for command_name in self.supported_command_names}

    @staticmethod
    def name_to_command_class(
        global_namespace: Dict[str, Any], class_name_mapping: Dict[str, str]
    ) -> Dict[str, Type[CommandBasic]]:
        """
        Convert the class name to the command class.
        :param class_name_mapping: The class name mapping {api_key: class_name}.
        :return: The command class mapping.
        """

        api_class_registry = {}

        for key, command_class_name in class_name_mapping.items():
            if command_class_name in global_namespace:
                api_class_registry[key] = global_namespace[command_class_name]
            else:
                print_with_color(
                    "Warning: The command class {command_class_name} with api key {key} is not found in the global namespace.",
                    "yellow",
                )

        return api_class_registry

    @property
    def type_name(self):

        return self.__class__.__name__


class CommandBasic(ABC):
    """
    The abstract command interface.
    """

    def __init__(self, receiver: ReceiverBasic, params: Dict = None) -> None:
        """
        Initialize the command.
        :param receiver: The receiver of the command.
        """
        self.receiver = receiver
        self.params = params if params is not None else {}

    @abstractmethod
    def execute(self):
        pass

    def undo(self):
        pass

    def redo(self):
        self.execute()

    @property
    def name(self):
        return self.__class__.__name__


class ReceiverFactory(ABC):
    """
    The abstract receiver factory interface.
    """

    @abstractmethod
    def create_receiver(self, *args, **kwargs):
        pass
