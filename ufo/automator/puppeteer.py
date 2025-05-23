# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import os
from collections import deque
from typing import TYPE_CHECKING, Any, Deque, Dict, List, Optional, Type, Union

from pywinauto.controls.uiawrapper import UIAWrapper

from ufo.automator.app_apis.basic import WinCOMReceiverBasic
from ufo.automator.basic import CommandBasic, ReceiverBasic, ReceiverFactory

if TYPE_CHECKING:
    from ufo.automator.ui_control.controller import ControlReceiver


class AppPuppeteer:
    """
    The class for the app puppeteer to automate the app in the Windows environment.
    """

    def __init__(self, process_name: str, app_root_name: str) -> None:
        """
        Initialize the app puppeteer.
        :param process_name: The process name of the app.
        :param app_root_name: The app root name, e.g., WINWORD.EXE.
        """

        self._process_name = process_name
        self._app_root_name = app_root_name
        self.command_queue: Deque[CommandBasic] = deque()
        self.receiver_manager = ReceiverManager()

    def create_command(
        self, command_name: str, params: Dict[str, Any], *args, **kwargs
    ) -> Optional[CommandBasic]:
        """
        Create the command.
        :param command_name: The command name.
        :param params: The arguments for the command.
        """
        receiver = self.receiver_manager.get_receiver_from_command_name(command_name)
        command = receiver.command_registry.get(command_name.lower(), None)

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

        try:
            receiver = self.receiver_manager.get_receiver_from_command_name(
                command_name
            )
            return receiver.type_name
        except:
            return ""

    def execute_command(
        self, command_name: str, params: Dict[str, Any], *args, **kwargs
    ) -> str:
        """
        Execute the command.
        :param command_name: The command name.
        :param params: The arguments.
        :return: The execution result.
        """

        command = self.create_command(command_name, params, *args, **kwargs)

        return command.execute()

    def execute_all_commands(self) -> List[Any]:
        """
        Execute all the commands in the command queue.
        :return: The execution results.
        """
        results = []
        while self.command_queue:
            command = self.command_queue.popleft()
            results.append(command.execute())

        return results

    def add_command(
        self, command_name: str, params: Dict[str, Any], *args, **kwargs
    ) -> None:
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

    @property
    def full_path(self) -> str:
        """
        Get the full path of the process. Only works for COM receiver.
        :return: The full path of the process.
        """
        com_receiver = self.receiver_manager.com_receiver
        if com_receiver is not None:
            return com_receiver.full_path

        return ""

    def save(self) -> None:
        """
        Save the current state of the app. Only works for COM receiver.
        """
        com_receiver = self.receiver_manager.com_receiver
        if com_receiver is not None:
            com_receiver.save()

    def save_to_xml(self, file_path: str) -> None:
        """
        Save the current state of the app to XML. Only works for COM receiver.
        :param file_path: The file path to save the XML.
        """
        com_receiver = self.receiver_manager.com_receiver
        dir_path = os.path.dirname(file_path)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)

        if com_receiver is not None:
            com_receiver.save_to_xml(file_path)

    def close(self) -> None:
        """
        Close the app. Only works for COM receiver.
        """
        com_receiver = self.receiver_manager.com_receiver
        if com_receiver is not None:
            com_receiver.close()

    @staticmethod
    def get_command_string(command_name: str, params: Dict[str, str]) -> str:
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

    _receiver_factory_registry: Dict[str, Dict[str, Union[str, ReceiverFactory]]] = {}

    def __init__(self):
        """
        Initialize the receiver manager.
        """

        self.receiver_registry = {}
        self.ui_control_receiver: Optional[ControlReceiver] = None

        self._receiver_list: List[ReceiverBasic] = []

    def create_ui_control_receiver(
        self, control: UIAWrapper, application: UIAWrapper
    ) -> "ControlReceiver":
        """
        Build the UI controller.
        :param control: The control element.
        :param application: The application window.
        :return: The UI controller receiver.
        """

        # control can be None
        if not application:
            return None

        factory: ReceiverFactory = self.receiver_factory_registry.get("UIControl").get(
            "factory"
        )
        self.ui_control_receiver = factory.create_receiver(control, application)
        self.receiver_list.append(self.ui_control_receiver)
        self._update_receiver_registry()

        return self.ui_control_receiver

    def create_api_receiver(self, app_root_name: str, process_name: str) -> None:
        """
        Get the API receiver.
        :param app_root_name: The app root name.
        :param process_name: The process name.
        """
        for receiver_factory_dict in self.receiver_factory_registry.values():

            # Check if the receiver is API
            if receiver_factory_dict.get("is_api"):
                receiver = receiver_factory_dict.get("factory").create_receiver(
                    app_root_name, process_name
                )
                if receiver is not None:
                    self.receiver_list.append(receiver)

        self._update_receiver_registry()

    def _update_receiver_registry(self) -> None:
        """
        Update the receiver registry. A receiver registry is a dictionary that maps the command name to the receiver.
        """

        for receiver in self.receiver_list:
            if receiver is not None:
                self.receiver_registry.update(receiver.self_command_mapping())

    def get_receiver_from_command_name(self, command_name: str) -> ReceiverBasic:
        """
        Get the receiver from the command name.
        :param command_name: The command name.
        :return: The mapped receiver.
        """
        receiver = self.receiver_registry.get(command_name, None)
        if receiver is None:
            raise ValueError(f"Receiver for command {command_name} is not found.")
        return receiver

    @property
    def receiver_list(self) -> List[ReceiverBasic]:
        """
        Get the receiver list.
        :return: The receiver list.
        """
        return self._receiver_list

    @property
    def receiver_factory_registry(
        self,
    ) -> Dict[str, Dict[str, Union[str, ReceiverFactory]]]:
        """
        Get the receiver factory registry.
        :return: The receiver factory registry.
        """
        return self._receiver_factory_registry

    @property
    def com_receiver(self) -> WinCOMReceiverBasic:
        """
        Get the COM receiver.
        :return: The COM receiver.
        """
        for receiver in self.receiver_list:
            if issubclass(receiver.__class__, WinCOMReceiverBasic):
                return receiver

        return None

    @classmethod
    def register(cls, receiver_factory_class: Type[ReceiverFactory]) -> ReceiverFactory:
        """
        Decorator to register the receiver factory class to the receiver manager.
        :param receiver_factory_class: The receiver factory class to be registered.
        :return: The receiver factory class instance.
        """

        cls._receiver_factory_registry[receiver_factory_class.name()] = {
            "factory": receiver_factory_class(),
            "is_api": receiver_factory_class.is_api(),
        }

        return receiver_factory_class()
