# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import time
import warnings
from abc import abstractmethod
from typing import Any, Dict, List, Optional, Tuple, Type, Union

import pyautogui
import pywinauto
from pywinauto import keyboard
from pywinauto.controls.uiawrapper import UIAWrapper
from pywinauto.win32structures import RECT

from ufo.automator.basic import CommandBasic, ReceiverBasic, ReceiverFactory
from ufo.automator.puppeteer import ReceiverManager
from ufo.config.config import Config
from ufo.utils import print_with_color

configs = Config.get_instance().config_data

if configs is not None and configs.get("AFTER_CLICK_WAIT", None) is not None:
    pywinauto.timings.Timings.after_clickinput_wait = configs["AFTER_CLICK_WAIT"]
    pywinauto.timings.Timings.after_click_wait = configs["AFTER_CLICK_WAIT"]

pyautogui.FAILSAFE = False


class ControlReceiver(ReceiverBasic):
    """
    The control receiver class.
    """

    _command_registry: Dict[str, Type[CommandBasic]] = {}

    def __init__(
        self, control: Optional[UIAWrapper], application: Optional[UIAWrapper]
    ) -> None:
        """
        Initialize the control receiver.
        :param control: The control element.
        :param application: The application element.
        """

        self.control = control
        self.application = application

        if control:
            self.control.set_focus()
            self.wait_enabled()
        elif application:
            self.application.set_focus()

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

        import traceback

        try:
            method = getattr(self.control, method_name)
            result = method(**params)
        except AttributeError:
            message = f"{self.control} doesn't have a method named {method_name}"
            print_with_color(f"Warning: {message}", "yellow")
            result = message
        except Exception as e:
            full_traceback = traceback.format_exc()
            message = f"An error occurred: {full_traceback}"
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

    def click_on_coordinates(self, params: Dict[str, str]) -> str:
        """
        Click on the coordinates of the control element.
        :param params: The arguments of the click on coordinates method.
        :return: The result of the click on coordinates action.
        """

        # Get the relative coordinates fraction of the application window.
        x = float(params.get("x", 0))
        y = float(params.get("y", 0))

        button = params.get("button", "left")
        double = params.get("double", False)

        # Get the absolute coordinates of the application window.
        tranformed_x, tranformed_y = self.transform_point(x, y)

        # print(f"Clicking on {tranformed_x}, {tranformed_y}")

        self.application.set_focus()

        pyautogui.click(
            tranformed_x, tranformed_y, button=button, clicks=2 if double else 1
        )

        return ""

    def drag_on_coordinates(self, params: Dict[str, str]) -> str:
        """
        Drag on the coordinates of the control element.
        :param params: The arguments of the drag on coordinates method.
        :return: The result of the drag on coordinates action.
        """

        start = self.transform_point(
            float(params.get("start_x", 0)), float(params.get("start_y", 0))
        )
        end = self.transform_point(
            float(params.get("end_x", 0)), float(params.get("end_y", 0))
        )

        duration = float(params.get("duration", 1))

        button = params.get("button", "left")

        key_hold = params.get("key_hold", None)

        self.application.set_focus()

        if key_hold:
            pyautogui.keyDown(key_hold)

        pyautogui.moveTo(start[0], start[1])
        pyautogui.dragTo(end[0], end[1], button=button, duration=duration)

        if key_hold:
            pyautogui.keyUp(key_hold)

        return ""

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
        inter_key_pause = configs.get("INPUT_TEXT_INTER_KEY_PAUSE", 0.1)

        if params.get("clear_current_text", False):
            self.control.type_keys("^a", pause=inter_key_pause)
            self.control.type_keys("{DELETE}", pause=inter_key_pause)

        if configs["INPUT_TEXT_API"] == "set_text":
            method_name = "set_edit_text"
            args = {"text": text}
        else:
            method_name = "type_keys"

            # Transform the text according to the tags.
            text = TextTransformer.transform_text(text, "all")

            args = {"keys": text, "pause": inter_key_pause, "with_spaces": True}
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
                args = {
                    "keys": keys_to_send,
                    "pause": inter_key_pause,
                    "with_spaces": True,
                }
                return self.atomic_execution(method_name, args)
            else:
                return f"An error occurred: {e}"

    def keyboard_input(self, params: Dict[str, str]) -> str:
        """
        Keyboard input on the control element.
        :param params: The arguments of the keyboard input method.
        :return: The result of the keyboard input action.
        """

        control_focus = params.get("control_focus", True)
        keys = params.get("keys", "")
        keys = TextTransformer.transform_text(keys, "all")

        if control_focus:
            self.atomic_execution("type_keys", {"keys": keys})
        else:
            self.application.type_keys(keys=keys)
        return keys

    def key_press(self, params: Dict[str, str]) -> str:
        """
        Key press on the control element.
        :param params: The arguments of the key press method.
        :return: The result of the key press action.
        """

        keys = params.get("keys", [])

        for key in keys:
            key = key.lower()
            pyautogui.keyDown(key)
        for key in keys:
            key = key.lower()
            pyautogui.keyUp(key)

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

        if self.control is not None:
            return self.atomic_execution("wheel_mouse_input", params)
        else:
            keyboard.send_keys("{VK_CONTROL up}")
            dist = int(params.get("wheel_dist", 0))
            return self.application.wheel_mouse_input(wheel_dist=dist)

    def scroll(self, params: Dict[str, str]) -> str:
        """
        Scroll on the control element.
        :param params: The arguments of the scroll method.
        :return: The result of the scroll action.
        """

        x = int(params.get("x", 0))
        y = int(params.get("y", 0))

        new_x, new_y = self.transform_point(x, y)

        scroll_x = int(params.get("scroll_x", 0))
        scroll_y = int(params.get("scroll_y", 0))

        pyautogui.vscroll(scroll_y, x=new_x, y=new_y)
        pyautogui.hscroll(scroll_x, x=new_x, y=new_y)

    def mouse_move(self, params: Dict[str, str]) -> str:
        """
        Mouse move on the control element.
        :param params: The arguments of the mouse move method.
        :return: The result of the mouse move action.
        """

        x = int(params.get("x", 0))
        y = int(params.get("y", 0))

        new_x, new_y = self.transform_point(x, y)

        pyautogui.moveTo(new_x, new_y, duration=0.1)

    def type(self, params: Dict[str, str]) -> str:
        """
        Type on the control element.
        :param params: The arguments of the type method.
        :return: The result of the type action.
        """

        text = params.get("text", "")
        pyautogui.write(text, interval=0.1)

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

    def transform_point(self, fraction_x: float, fraction_y: float) -> Tuple[int, int]:
        """
        Transform the relative coordinates to the absolute coordinates.
        :param fraction_x: The relative x coordinate.
        :param fraction_y: The relative y coordinate.
        :return: The absolute coordinates.
        """
        application_rect: RECT = self.application.rectangle()
        application_x = application_rect.left
        application_y = application_rect.top
        application_width = application_rect.width()
        application_height = application_rect.height()

        x = application_x + int(application_width * fraction_x)
        y = application_y + int(application_height * fraction_y)

        return x, y

    def transfrom_absolute_point_to_fractional(self, x: int, y: int) -> Tuple[int, int]:
        """
        Transform the absolute coordinates to the relative coordinates.
        :param x: The absolute x coordinate on the application window.
        :param y: The absolute y coordinate on the application window.
        :return: The relative coordinates fraction.
        """
        application_rect: RECT = self.application.rectangle()
        # application_x = application_rect.left
        # application_y = application_rect.top

        application_width = application_rect.width()
        application_height = application_rect.height()

        fraction_x = x / application_width
        fraction_y = y / application_height

        return fraction_x, fraction_y

    def transform_scaled_point_to_raw(
        self,
        scaled_x: int,
        scaled_y: int,
        scaled_width: int,
        scaled_height: int,
        raw_width: int,
        raw_height: int,
    ) -> Tuple[int, int]:
        """
        Transform the scaled coordinates to the raw coordinates.
        :param scaled_x: The scaled x coordinate.
        :param scaled_y: The scaled y coordinate.
        :param raw_width: The raw width of the application window.
        :param raw_height: The raw height of the application window.
        :param scaled_width: The scaled width of the application window.
        :param scaled_height: The scaled height of the application window.
        """

        ratio = min(scaled_width / raw_width, scaled_height / raw_height)
        raw_x = scaled_x / ratio
        raw_y = scaled_y / ratio

        return int(raw_x), int(raw_y)


@ReceiverManager.register
class UIControlReceiverFactory(ReceiverFactory):
    """
    The factory class for the control receiver.
    """

    def create_receiver(self, control, application):
        """
        Create the control receiver.
        :param control: The control element.
        :param application: The application element.
        :return: The control receiver.
        """
        return ControlReceiver(control, application)

    @classmethod
    def name(cls) -> str:
        """
        Get the name of the receiver factory.
        :return: The name of the receiver factory.
        """
        return "UIControl"


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
class ClickOnCoordinatesCommand(ControlCommand):
    """
    The click on coordinates command class.
    """

    def execute(self) -> str:
        """
        Execute the click on coordinates command.
        :return: The result of the click on coordinates command.
        """
        return self.receiver.click_on_coordinates(self.params)

    @classmethod
    def name(cls) -> str:
        """
        Get the name of the atomic command.
        :return: The name of the atomic command.
        """
        return "click_on_coordinates"


@ControlReceiver.register
class DragOnCoordinatesCommand(ControlCommand):
    """
    The drag on coordinates command class.
    """

    def execute(self) -> str:
        """
        Execute the drag on coordinates command.
        :return: The result of the drag on coordinates command.
        """

        return self.receiver.drag_on_coordinates(self.params)

    @classmethod
    def name(cls) -> str:
        """
        Get the name of the atomic command.
        :return: The name of the atomic command.
        """
        return "drag_on_coordinates"


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


# Register the command classes for OpenAI Operator.


@ControlReceiver.register
class ClickCommand(ControlCommand):
    """
    The click command class on coordinates.
    """

    def execute(self) -> str:
        """
        Execute the click command.
        :return: The result of the command.
        """

        # Get the absolute coordinates of the application window.
        x = int(self.params.get("x", 0))
        y = int(self.params.get("y", 0))

        if self.params.get("scaler", None) and self.receiver.application:
            scaled_width = self.params["scaler"][0]
            scaled_height = self.params["scaler"][1]
            raw_width = self.receiver.application.rectangle().width()
            raw_height = self.receiver.application.rectangle().height()

            x, y = self.receiver.transform_scaled_point_to_raw(
                x, y, scaled_width, scaled_height, raw_width, raw_height
            )

        new_x, new_y = self.receiver.transfrom_absolute_point_to_fractional(x, y)

        # print(f"Clicking on {new_x}, {new_y}")

        button = self.params.get("button", "left")
        button = "middle" if button == "wheel" else button

        params = {"x": new_x, "y": new_y, "button": button}

        return self.receiver.click_on_coordinates(params)

    @classmethod
    def name(cls) -> str:
        """
        Get the name of the command.
        :return: The name of the command.
        """
        return "click"


@ControlReceiver.register
class DoubleClickCommand(ControlCommand):
    """
    The double click command class on coordinates.
    """

    def execute(self) -> str:
        """
        Execute the double click command.
        :return: The result of the command.
        """

        # Get the absolute coordinates of the application window.
        x = int(self.params.get("x", 0))
        y = int(self.params.get("y", 0))

        if self.params.get("scaler", None) and self.receiver.application:
            scaled_width = self.params["scaler"][0]
            scaled_height = self.params["scaler"][1]
            raw_width = self.receiver.application.rectangle().width()
            raw_height = self.receiver.application.rectangle().height()

            x, y = self.receiver.transform_scaled_point_to_raw(
                x, y, scaled_width, scaled_height, raw_width, raw_height
            )

        new_x, new_y = self.receiver.transfrom_absolute_point_to_fractional(x, y)

        button = self.params.get("button", "left")
        button = "middle" if button == "wheel" else button

        params = {"x": new_x, "y": new_y, "button": button, "double": True}

        return self.receiver.click_on_coordinates(params)

    @classmethod
    def name(cls) -> str:
        """
        Get the name of the command.
        :return: The name of the command.
        """
        return "double_click"


@ControlReceiver.register
class DragCommand(ControlCommand):
    """
    The drag command class on coordinates.
    """

    def execute(self) -> str:
        """
        Execute the drag command.
        :return: The result of the command.
        """

        path = self.params.get("path", [])

        for i in range(len(path)):
            start_x, start_y = path[i].get("x", 0), path[i].get("y", 0)
            end_x, end_y = path[i + 1].get("x", 0), (
                path[i + 1].get("y", 0) if i + 1 < len(path) else path[i]
            )

            # print(f"Dragging from {start_x}, {start_y} to {end_x}, {end_y}")

            if self.params.get("scaler", None) and self.receiver.application:
                scaled_width = self.params["scaler"][0]
                scaled_height = self.params["scaler"][1]
                raw_width = self.receiver.application.rectangle().width()
                raw_height = self.receiver.application.rectangle().height()

                start_x, start_y = self.receiver.transform_scaled_point_to_raw(
                    start_x, start_y, scaled_width, scaled_height, raw_width, raw_height
                )

                end_x, end_y = self.receiver.transform_scaled_point_to_raw(
                    end_x, end_y, scaled_width, scaled_height, raw_width, raw_height
                )

            new_start_x, new_start_y = (
                self.receiver.transfrom_absolute_point_to_fractional(start_x, start_y)
            )

            new_end_x, new_end_y = self.receiver.transfrom_absolute_point_to_fractional(
                end_x, end_y
            )

            params = {
                "start_x": new_start_x,
                "start_y": new_start_y,
                "end_x": new_end_x,
                "end_y": new_end_y,
            }

            self.receiver.drag_on_coordinates(params)

    @classmethod
    def name(cls) -> str:
        """
        Get the name of the command.
        :return: The name of the command.
        """
        return "drag"


@ControlReceiver.register
class KeyPressCommand(ControlCommand):
    """
    The key press command class.
    """

    def execute(self) -> str:
        """
        Execute the key press command.
        :return: The result of the command.
        """

        return self.receiver.key_press(self.params)

    @classmethod
    def name(cls) -> str:
        """
        Get the name of the command.
        :return: The name of the command.
        """
        return "keypress"


@ControlReceiver.register
class MouseMoveCommand(ControlCommand):
    """
    The mouse move command class.
    """

    def execute(self) -> str:
        """
        Execute the mouse move command.
        :return: The result of the command.
        """

        # Get the absolute coordinates of the application window.
        x = int(self.params.get("x", 0))
        y = int(self.params.get("y", 0))

        if self.params.get("scaler", None) and self.receiver.application:
            scaled_width = self.params["scaler"][0]
            scaled_height = self.params["scaler"][1]
            raw_width = self.receiver.application.rectangle().width()
            raw_height = self.receiver.application.rectangle().height()

            x, y = self.receiver.transform_scaled_point_to_raw(
                x, y, scaled_width, scaled_height, raw_width, raw_height
            )

        new_x, new_y = self.receiver.transfrom_absolute_point_to_fractional(x, y)

        params = {"x": new_x, "y": new_y}

        return self.receiver.mouse_move(params)

    @classmethod
    def name(cls) -> str:
        """
        Get the name of the command.
        :return: The name of the command.
        """
        return "move"


@ControlReceiver.register
class ScrollCommand(ControlCommand):
    """
    The scroll command class.
    """

    def execute(self) -> str:
        """
        Execute the scroll command.
        :return: The result of the command.
        """

        # Get the absolute coordinates of the application window.
        x = int(self.params.get("x", 0))
        y = int(self.params.get("y", 0))

        if self.params.get("scaler", None) and self.receiver.application:
            scaled_width = self.params["scaler"][0]
            scaled_height = self.params["scaler"][1]
            raw_width = self.receiver.application.rectangle().width()
            raw_height = self.receiver.application.rectangle().height()

            x, y = self.receiver.transform_scaled_point_to_raw(
                x, y, scaled_width, scaled_height, raw_width, raw_height
            )

        new_x, new_y = self.receiver.transfrom_absolute_point_to_fractional(x, y)

        scroll_x = int(self.params.get("scroll_x", 0))
        scroll_y = int(self.params.get("scroll_y", 0))

        params = {"x": new_x, "y": new_y, "scroll_x": scroll_x, "scroll_y": scroll_y}

        return self.receiver.scroll(params)

    @classmethod
    def name(cls) -> str:
        """
        Get the name of the command.
        :return: The name of the command.
        """
        return "scroll"


@ControlReceiver.register
class TypeCommand(ControlCommand):
    """
    The type command class.
    """

    def execute(self) -> str:
        """
        Execute the type command.
        :return: The result of the command.
        """

        return self.receiver.type(self.params)

    @classmethod
    def name(cls) -> str:
        """
        Get the name of the command.
        :return: The name of the command.
        """
        return "type"


@ControlReceiver.register
class WaitCommand(ControlCommand):
    """
    The wait command class.
    """

    def execute(self) -> str:
        """
        Execute the wait command.
        :return: The result of the command.
        """

        time.sleep(3)

    @classmethod
    def name(cls) -> str:
        """
        Get the name of the command.
        :return: The name of the command.
        """
        return "wait"


class TextTransformer:
    """
    The text transformer class.
    """

    @staticmethod
    def transform_text(text: str, transform_tag: str) -> str:
        """
        Transform the text.
        :param text: The text to transform.
        :param transform_tag: The tag to transform.
        :return: The transformed text.
        """

        if transform_tag == "all":
            transform_tag = "+\n\t^%{VK_CONTROL}{VK_SHIFT}{VK_MENU}()"

        if "\n" in transform_tag:
            text = TextTransformer.transform_enter(text)
        if "\t" in transform_tag:
            text = TextTransformer.transform_tab(text)
        if "+" in transform_tag:
            text = TextTransformer.transform_plus(text)
        if "^" in transform_tag:
            text = TextTransformer.transform_caret(text)
        if "%" in transform_tag:
            text = TextTransformer.transform_percent(text)
        if "{VK_CONTROL}" in transform_tag:
            text = TextTransformer.transform_control(text)
        if "{VK_SHIFT}" in transform_tag:
            text = TextTransformer.transform_shift(text)
        if "{VK_MENU}" in transform_tag:
            text = TextTransformer.transform_alt(text)
        if "(" in transform_tag or ")" in transform_tag:
            text = TextTransformer.transform_brace(text)

        return text

    @staticmethod
    def transform_enter(text: str) -> str:
        """
        Transform the enter key.
        :param text: The text to transform.
        :return: The transformed text.
        """
        return text.replace("\n", "{ENTER}")

    @staticmethod
    def transform_tab(text: str) -> str:
        """
        Transform the tab key.
        :param text: The text to transform.
        :return: The transformed text.
        """
        return text.replace("\t", "{TAB}")

    @staticmethod
    def transform_plus(text: str) -> str:
        """
        Transform the plus key.
        :param text: The text to transform.
        :return: The transformed text.
        """
        return text.replace("+", "{+}")

    @staticmethod
    def transform_caret(text: str) -> str:
        """
        Transform the caret key.
        :param text: The text to transform.
        :return: The transformed text.
        """
        return text.replace("^", "{^}")

    @staticmethod
    def transform_brace(text: str) -> str:
        """
        Transform the brace key.
        :param text: The text to transform.
        :return: The transformed text.
        """
        return text.replace("(", "{(}").replace(")", "{)}")

    @staticmethod
    def transform_percent(text: str) -> str:
        """
        Transform the percent key.
        :param text: The text to transform.
        :return: The transformed text.
        """
        return text.replace("%", "{%}")

    @staticmethod
    def transform_control(text: str) -> str:
        """
        Transform the control key.
        :param text: The text to transform.
        :return: The transformed text.
        """
        return text.replace("{VK_CONTROL}", "^")

    @staticmethod
    def transform_shift(text: str) -> str:
        """
        Transform the shift key.
        :param text: The text to transform.
        :return: The transformed text.
        """
        return text.replace("{VK_SHIFT}", "+")

    @staticmethod
    def transform_alt(text: str) -> str:
        """
        Transform the alt key.
        :param text: The text to transform.
        :return: The transformed text.
        """
        return text.replace("{VK_MENU}", "%")
