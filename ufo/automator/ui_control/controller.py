# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import time
import warnings
from abc import abstractmethod
from typing import Any, Dict, List, Optional, Type, Union

from pywinauto.controls.uiawrapper import UIAWrapper

from ufo.automator.basic import CommandBasic, ReceiverBasic, ReceiverFactory
from ufo.config.config import Config
from ufo.utils import print_with_color

configs = Config.get_instance().config_data


class ControlReceiver(ReceiverBasic):
    """
    The control receiver class.
    """

    _command_registry: Dict[str, Type[CommandBasic]] = {}

    def __init__(self, control: UIAWrapper, application: UIAWrapper):
        """
        Initialize the control receiver.
        :param control: The control element.
        :param application: The application element.
        """

        self.control = control

        if control:
            self.control.set_focus()
            self.wait_enabled()
        self.application = application

    @property
    def type_name(self):
        return "UIControl"

    def atomic_execution(self, method_name: str, params: Dict[str, Any]) -> str:
        """
        Atomic execution of the action on the control elements.
        :param method_name: The name of the method to execute.
        :param params: The arguments of the method.
        :return: The result of the action.
        """

        try:
            method = getattr(self.control, method_name)
            result = method(**params)
        except AttributeError:
            message = f"{self.control} doesn't have a method named {method_name}"
            print_with_color(f"Warning: {message}", "yellow")
            result = message
        except Exception as e:
            message = f"An error occurred: {e}"
            print_with_color(f"Warning: {message}", "yellow")
            result = message
        return result

    def click_input(self, params: Dict[str, Union[str, bool]]) -> str:
        """
        Click the control element.
        :param params: The arguments of the click method.
        :return: The result of the click action.
        """

        api_name = configs.get("CLICK_API", "click_input")

        if api_name == "click":
            return self.atomic_execution("click", params)
        else:
            return self.atomic_execution("click_input", params)

    def summary(self, params: Dict[str, str]) -> str:
        """
        Visual summary of the control element.
        :param params: The arguments of the visual summary method. should contain a key "text" with the text summary.
        :return: The result of the visual summary action.
        """

        return params.get("text")

    def set_edit_text(self, params: Dict[str, str]) -> str:
        """
        Set the edit text of the control element.
        :param params: The arguments of the set edit text method.
        :return: The result of the set edit text action.
        """

        text = params.get("text", "")

        if configs["INPUT_TEXT_API"] == "set_text":
            method_name = "set_edit_text"
            args = {"text": text}
        else:
            method_name = "type_keys"
            text = text.replace("\n", "{ENTER}")
            text = text.replace("\t", "{TAB}")

            args = {"keys": text, "pause": 0.1, "with_spaces": True}
        try:
            result = self.atomic_execution(method_name, args)
            if (
                method_name == "set_text"
                and args["text"] not in self.control.window_text()
            ):
                raise Exception(f"Failed to use set_text: {args['text']}")
            if configs["INPUT_TEXT_ENTER"] and method_name in ["type_keys", "set_text"]:

                self.atomic_execution("type_keys", params={"keys": "{ENTER}"})
            return result
        except Exception as e:
            if method_name == "set_text":
                print_with_color(
                    f"{self.control} doesn't have a method named {method_name}, trying default input method",
                    "yellow",
                )
                method_name = "type_keys"
                clear_text_keys = "^a{BACKSPACE}"
                text_to_type = args["text"]
                keys_to_send = clear_text_keys + text_to_type
                method_name = "type_keys"
                args = {"keys": keys_to_send, "pause": 0.1, "with_spaces": True}
                return self.atomic_execution(method_name, args)
            else:
                return f"An error occurred: {e}"

    def keyboard_input(self, params: Dict[str, str]) -> str:
        """
        Keyboard input on the control element.
        :param params: The arguments of the keyboard input method.
        :return: The result of the keyboard input action.
        """
        return self.atomic_execution("type_keys", params)

    def texts(self) -> str:
        """
        Get the text of the control element.
        :return: The text of the control element.
        """
        return self.control.texts()

    def wheel_mouse_input(self, params: Dict[str, str]):
        """
        Wheel mouse input on the control element.
        :param params: The arguments of the wheel mouse input method.
        :return: The result of the wheel mouse input action.
        """
        return self.atomic_execution("wheel_mouse_input", params)

    def no_action(self):
        """
        No action on the control element.
        :return: The result of the no action.
        """

        return ""

    def annotation(
        self, params: Dict[str, str], annotation_dict: Dict[str, UIAWrapper]
    ) -> List[str]:
        """
        Take a screenshot of the current application window and annotate the control item on the screenshot.
        :param params: The arguments of the annotation method.
        :param annotation_dict: The dictionary of the control labels.
        """
        selected_controls_labels = params.get("control_labels", [])

        control_reannotate = [
            annotation_dict[str(label)] for label in selected_controls_labels
        ]

        return control_reannotate

    def wait_enabled(self, timeout: int = 10, retry_interval: int = 0.5) -> None:
        """
        Wait until the control is enabled.
        :param timeout: The timeout to wait.
        :param retry_interval: The retry interval to wait.
        """
        while not self.control.is_enabled():
            time.sleep(retry_interval)
            timeout -= retry_interval
            if timeout <= 0:
                warnings.warn(f"Timeout: {self.control} is not enabled.")
                break

    def wait_visible(self, timeout: int = 10, retry_interval: int = 0.5) -> None:
        """
        Wait until the window is enabled.
        :param timeout: The timeout to wait.
        :param retry_interval: The retry interval to wait.
        """
        while not self.control.is_visible():
            time.sleep(retry_interval)
            timeout -= retry_interval
            if timeout <= 0:
                warnings.warn(f"Timeout: {self.control} is not visible.")
                break


class UIControlReceiverFactory(ReceiverFactory):
    """
    The factory class for the control receiver.
    """

    def create_receiver(self, control, application):
        return ControlReceiver(control, application)


class ControlCommand(CommandBasic):
    """
    The abstract command interface.
    """

    def __init__(self, receiver: ControlReceiver, params=None) -> None:
        """
        Initialize the command.
        :param receiver: The receiver of the command.
        """
        self.receiver = receiver
        self.params = params if params is not None else {}

    @abstractmethod
    def execute(self):
        pass

    @classmethod
    def name(cls) -> str:
        """
        Get the name of the atomic command.
        :return: The name of the atomic command.
        """
        return "control_command"


class AtomicCommand(ControlCommand):
    """
    The atomic command class.
    """

    def __init__(
        self,
        receiver: ControlReceiver,
        method_name: str,
        params=Optional[Dict[str, str]],
    ) -> None:
        """
        Initialize the atomic command.
        :param receiver: The receiver of the command.
        :param method_name: The method to execute.
        :param params: The parameters of the method.
        """

        super().__init__(receiver, params)
        self.method_name = method_name

    def execute(self) -> str:
        """
        Execute the atomic command.
        :param method_name: The method to execute.
        :param params: The arguments of the method.
        :return: The result of the atomic command.
        """
        return self.receiver.atomic_execution(self.method_name, self.params)

    @classmethod
    def name(cls) -> str:
        """
        Get the name of the atomic command.
        :return: The name of the atomic command.
        """
        return "atomic_command"


@ControlReceiver.register
class ClickInputCommand(ControlCommand):
    """
    The click input command class.
    """

    def execute(self) -> str:
        """
        Execute the click input command.
        :return: The result of the click input command.
        """
        return self.receiver.click_input(self.params)

    @classmethod
    def name(cls) -> str:
        """
        Get the name of the atomic command.
        :return: The name of the atomic command.
        """
        return "click_input"


@ControlReceiver.register
class SummaryCommand(ControlCommand):
    """
    The summary command class to summarize the application screenshot.
    """

    def execute(self) -> str:
        """
        Execute the summary command.
        :return: The result of the summary command.
        """
        return self.receiver.summary(self.params)

    @classmethod
    def name(cls) -> str:
        """
        Get the name of the atomic command.
        :return: The name of the atomic command.
        """
        return "summary"


@ControlReceiver.register
class SetEditTextCommand(ControlCommand):
    """
    The set edit text command class.
    """

    def execute(self) -> str:
        """
        Execute the set edit text command.
        :return: The result of the set edit text command.
        """

        return self.receiver.set_edit_text(self.params)

    @classmethod
    def name(cls) -> str:
        """
        Get the name of the atomic command.
        :return: The name of the atomic command.
        """
        return "set_edit_text"


@ControlReceiver.register
class GetTextsCommand(ControlCommand):
    """
    The get texts command class.
    """

    def execute(self) -> str:
        """
        Execute the get texts command.
        :return: The texts of the control element.
        """
        return self.receiver.texts()

    @classmethod
    def name(cls) -> str:
        """
        Get the name of the atomic command.
        :return: The name of the atomic command.
        """
        return "texts"


@ControlReceiver.register
class WheelMouseInputCommand(ControlCommand):
    """
    The wheel mouse input command class.
    """

    def execute(self) -> str:
        """
        Execute the wheel mouse input command.
        :return: The result of the wheel mouse input command.
        """
        return self.receiver.wheel_mouse_input(self.params)

    @classmethod
    def name(cls) -> str:
        """
        Get the name of the atomic command.
        :return: The name of the atomic command.
        """
        return "wheel_mouse_input"


@ControlReceiver.register
class AnnotationCommand(ControlCommand):
    """
    The annotation command class.
    """

    def __init__(
        self,
        receiver: ControlReceiver,
        params: Dict[str, str],
        annotation_dict: Dict[str, UIAWrapper],
    ) -> None:
        """
        Initialize the annotation command.
        :param receiver: The receiver of the command.
        :param params: The arguments of the annotation method.
        :param annotation_dict: The dictionary of the control labels.
        """
        super().__init__(receiver, params)
        self.annotation_dict = annotation_dict

    def execute(self) -> str:
        """
        Execute the annotation command.
        :return: The result of the annotation command.
        """
        return self.receiver.annotation(self.params, self.annotation_dict)

    @classmethod
    def name(cls) -> str:
        """
        Get the name of the atomic command.
        :return: The name of the atomic command.
        """
        return "annotation"


@ControlReceiver.register
class keyboardInputCommand(ControlCommand):
    """
    The keyborad input command class.
    """

    def execute(self) -> str:
        """
        Execute the keyborad input command.
        :return: The result of the keyborad input command.
        """
        return self.receiver.keyboard_input(self.params)

    @classmethod
    def name(cls) -> str:
        """
        Get the name of the atomic command.
        :return: The name of the atomic command.
        """
        return "keyboard_input"


@ControlReceiver.register
class NoActionCommand(ControlCommand):
    """
    The no action command class.
    """

    def execute(self) -> str:
        """
        Execute the no action command.
        :return: The result of the no action command.
        """
        return self.receiver.no_action()

    @classmethod
    def name(cls) -> str:
        """
        Get the name of the atomic command.
        :return: The name of the atomic command.
        """
        return ""
