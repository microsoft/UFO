# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from collections import deque
from typing import Dict, List, Optional

from pywinauto.controls.uiawrapper import UIAWrapper

from ufo.automator.app_apis.basic import WinCOMReceiverBasic
from ufo.automator.app_apis.factory import COMReceiverFactory
from ufo.automator.basic import CommandBasic, ReceiverBasic, ReceiverFactory
from ufo.automator.ui_control.controller import (
    ControlReceiver,
    UIControlReceiverFactory,
)


class AppPuppeteer:
    """
    The class for the app puppeteer to automate the app in the Windows environment.
    """

    def __init__(self, process_name: str, app_root_name: str) -> None:
        """
        Initialize the app puppeteer.
        :param process_name: The process name of the app.
        :param app_root_name: The app root name, e.g., WINWORD.EXE.
        :param ui_control_interface: The UI control interface instance in pywinauto.
        """

        self._process_name = process_name
        self._app_root_name = app_root_name
        self.command_queue = deque()
        self.receiver_manager = ReceiverManager()

    def create_command(
        self, command_name: str, params: Dict, *args, **kwargs
    ) -> Optional[CommandBasic]:
        """
        Create the command.
        :param command_name: The command name.
        :param params: The arguments for the command.
        """
        receiver = self.receiver_manager.get_receiver(command_name)
        command = receiver.get_command_registry().get(command_name.lower(), None)

        if receiver is None:
            raise ValueError(f"Receiver for command {command_name} is not found.")

        if command is None:
            raise ValueError(f"Command {command_name} is not supported.")

        return command(receiver, params, *args, **kwargs)

    def get_command_types(self, command_name: str) -> str:
        """
        Get the command types.
        :param command_name: The command name.
        :return: The command types.
        """
        receiver = self.receiver_manager.get_receiver(command_name)

        return receiver.type_name

    def execute_command(self, command_name: str, params: Dict, *args, **kwargs) -> str:
        """
        Execute the command.
        :param command_name: The command name.
        :param params: The arguments.
        :return: The execution result.
        """

        command = self.create_command(command_name, params, *args, **kwargs)
        return command.execute()

    def execute_all_commands(self) -> List:
        """
        Execute all the commands in the command queue.
        :return: The execution results.
        """
        results = []
        while self.command_queue:
            command = self.command_queue.popleft()
            results.append(command.execute())

    def add_command(self, command_name: str, params: Dict, *args, **kwargs) -> None:
        """
        Add the command to the command queue.
        :param command_name: The command name.
        :param params: The arguments.
        """
        command = self.create_command(command_name, params, *args, **kwargs)
        self.command_queue.append(command)

    def get_command_queue_length(self) -> int:
        """
        Get the length of the command queue.
        :return: The length of the command queue.
        """
        return len(self.command_queue)

    @staticmethod
    def get_command_string(command_name: str, params: Dict) -> str:
        """
        Generate a function call string.
        :param command_name: The function name.
        :param params: The arguments as a dictionary.
        :return: The function call string.
        """
        # Format the arguments
        args_str = ", ".join(f"{k}={v!r}" for k, v in params.items())

        # Return the function call string
        return f"{command_name}({args_str})"


class ReceiverManager:
    """
    The class for the receiver manager.
    """

    def __init__(self):
        """
        Initialize the receiver manager.
        """

        self.receiver_registry = {}
        self.receiver_factories = {}
        self.ui_control_receiver = None
        self.com_receiver = None

        self.load_receiver_factories()

    def load_receiver_factories(self) -> None:
        """
        Load the receiver factories. Now we have two types of receiver factories: UI control receiver factory and COM receiver factory.
        A receiver factory is responsible for creating the receiver for the specific type of receiver.
        """

        self.__register_receiver_factory("UIControl", UIControlReceiverFactory())
        self.__register_receiver_factory("COM", COMReceiverFactory())

    def __register_receiver_factory(
        self, factory_name: str, factory: ReceiverFactory
    ) -> None:
        """
        Register the receiver factory.
        :param factory_name: The factory name.
        :param factory: The factory instance.
        """
        self.receiver_factories[factory_name] = factory

    def create_ui_control_receiver(
        self, control: UIAWrapper, application: UIAWrapper
    ) -> ControlReceiver:
        """
        Build the UI controller.
        :param control: The control element.
        :return: The UI controller.
        """
        factory = self.receiver_factories.get("UIControl")
        self.ui_control_receiver = factory.create_receiver(control, application)
        self.__update_receiver_registry()

        return self.ui_control_receiver

    def create_com_receiver(self, app_root_name, process_name) -> WinCOMReceiverBasic:
        """
        Get the COM client.
        :param app_root_name: The app root name.
        :param process_name: The process name.

        """
        factory = self.receiver_factories.get("COM")
        self.com_receiver = factory.create_receiver(app_root_name, process_name)
        self.__update_receiver_registry()
        return self.com_receiver

    def __update_receiver_registry(self) -> None:
        """
        Update the receiver registry. A receiver registry is a dictionary that maps the command name to the receiver.
        """

        if self.ui_control_receiver is not None:
            self.receiver_registry.update(
                self.ui_control_receiver.self_command_mapping()
            )
        if self.com_receiver is not None:
            self.receiver_registry.update(self.com_receiver.self_command_mapping())

    def get_receiver(self, command_name: str) -> ReceiverBasic:
        """
        Get the receiver from the command name.
        :param command_name: The command name.
        :return: The mapped receiver.
        """
        receiver = self.receiver_registry.get(command_name, None)
        if receiver is None:
            raise ValueError(f"Receiver for command {command_name} is not found.")
        return receiver
