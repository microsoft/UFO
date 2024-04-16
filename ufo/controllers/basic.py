# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from abc import ABC, abstractmethod
from typing import Dict, List
from .ui_control.controller import UIAutomator


class AutomatorBasic(ABC):
    """
    The base class for Automator.
    """

    def __init__(self) -> None:
        """
        Initialize the Automator.
        """
        self.commands = {}
        self.receiver = self.create_receiver()
        self.register_commands()


    @abstractmethod
    def create_receiver(self):
        """
        Create the receiver.
        :return: The receiver.
        """
        pass

    @abstractmethod
    def register_commands(self):
        """
        Register the commands.
        """
        pass


    def get_supported_commands(self) -> List:
        """
        Get the supported commands.
        :return: The supported commands.
        """
        return list(self.commands.keys())


    def execution(self, command_name:str, params:Dict, *args, **kwargs) -> str:
        """
        Execute the command.
        :param command_name: The command name.
        :param params: The arguments.
        :return: The execution result.
        """

        command = self.commands.get(command_name.lower(), None)
        if command is None:
            return f"Command {command_name} is not supported."
        
        return command(self.receiver, params, *args, **kwargs).execute()
    

    @staticmethod
    def get_command_string(command_name:str, params:Dict):
        """
        Generate a function call string.
        :param func: The function name.
        :param args: The arguments as a dictionary.
        :return: The function call string.
        """
        # Format the arguments
        args_str = ', '.join(f'{k}={v!r}' for k, v in params.items())

        # Return the function call string
        return f'{command_name}({args_str})'
    


class AutomatorFactory(ABC):
    """
    The base class for Automator Factory.
    """

    @abstractmethod
    def create_automator(automator_type: str, *args, **kwargs):
        """
        Create the Automator.
        :param automator_type: The type of the Automator.
        :return: The Automator.
        """
        if automator_type == "ui_automator":
            return UIAutomator(*args, **kwargs)
        
        elif automator_type == "com":
            # return COMController(*args, **kwargs)
            pass
        else:
            raise ValueError(f"Automator type {automator_type} is not supported.")


