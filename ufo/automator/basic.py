# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, List, Type


class ReceiverBasic(ABC):
    """
    The abstract receiver interface.
    """

    _command_registry: Dict[str, Type[CommandBasic]] = {}

    @property
    def command_registry(self) -> Dict[str, Type[CommandBasic]]:
        """
        Get the command registry.
        """
        return self._command_registry

    def register_command(self, command_name: str, command: CommandBasic) -> None:
        """
        Add to the command registry.
        :param command_name: The command name.
        :param command: The command.
        """

        self.command_registry[command_name] = command

    @property
    def supported_command_names(self) -> List[str]:
        """
        Get the command name list.
        """
        return list(self.command_registry.keys())

    def self_command_mapping(self) -> Dict[str, CommandBasic]:
        """
        Get the command-receiver mapping.
        """
        return {command_name: self for command_name in self.supported_command_names}

    @classmethod
    def register(cls, command_class: Type[CommandBasic]) -> Type[CommandBasic]:
        """
        Decorator to register the state class to the state manager.
        :param command_class: The state class to be registered.
        :return: The state class.
        """
        cls._command_registry[command_class.name()] = command_class
        return command_class

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
        """
        Execute the command.
        """
        pass

    def undo(self):
        """
        Undo the command.
        """
        pass

    def redo(self):
        """
        Redo the command.
        """
        self.execute()

    @classmethod
    @abstractmethod
    def name(cls):
        return cls.__class__.__name__


class ReceiverFactory(ABC):
    """
    The abstract receiver factory interface.
    """

    @abstractmethod
    def create_receiver(self, *args, **kwargs):
        pass

    @classmethod
    def name(cls) -> str:
        """
        The name of the receiver factory.
        """
        return cls.__class__.__name__

    @classmethod
    def is_api(cls) -> bool:
        """
        Check if the receiver factory is to create an API receiver.
        """
        return False
