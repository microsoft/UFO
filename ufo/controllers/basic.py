# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from abc import ABC, abstractmethod
from typing import Dict, List, Type


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



class ReceiverFactory(ABC):
    """
    The abstract receiver factory interface.
    """

    @abstractmethod  
    def create_receiver(self, *args, **kwargs):  
        pass 
    
    

