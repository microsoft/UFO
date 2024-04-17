# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from abc import ABC, abstractmethod
from collections import deque
from typing import Dict, List, Type
from .ui_control.controller import UIAutomator


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

    def register_command(self, command_name:str, command:Type) -> None:
        """
        Add to the command registry.
        :param command_name: The command name.
        :param command: The command.
        """

        self.command_registry[command_name] = command
        
    
    def get_supported_command_names(self) -> List:
        """
        Get the command name list.
        """
        return list(self.command_registry.keys())
    
    
    def self_command_mapping(self) -> Dict:
        """
        Get the command-receiver mapping.
        """
        return {command_name: self for command_name in self.supported_command_names}


class ReceiverFactory(ABC):
    """
    The abstract receiver factory interface.
    """

    @abstractmethod  
    def create_receiver(self, *args, **kwargs):  
        pass 



class CommandBasic(ABC):
    """
    The abstract command interface.
    """

    def __init__(self, receiver: ReceiverBasic, params=None) -> None:
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
    


class AutomatorBasic(ABC):
    """
    The base class for Automator.
    """

    def __init__(self) -> None:
        """
        Initialize the Automator.
        """
        self.command_queue = deque()


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
    


class InvokerBasic(ABC):
    """
    The base class for Automator Invoker.
    """

    def __init__(self) -> None:
        """
        Initialize the Automator Invoker.
        :param automator: The Automator.
        """
        self.queue = deque()


    def execute_command(self, command_name:str, params:Dict, *args, **kwargs) -> str:
        """
        Execute the command.
        :param command_name: The command name.
        :param params: The arguments.
        :return: The execution result.
        """
        return self.automator.execution(command_name, params, *args, **kwargs)


    def get_supported_commands(self) -> List:
        """
        Get the supported commands.
        :return: The supported commands.
        """
        return self.automator.get_supported_commands()


    @staticmethod
    def get_command_string(command_name:str, params:Dict):
        """
        Generate a function call string.
        :param func: The function name.
        :param args: The arguments as a dictionary.
        :return: The function call string.
        """
        return AutomatorBasic.get_command_string(command_name, params)
    

