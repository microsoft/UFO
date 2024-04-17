# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import time
import warnings

from ...config.config import Config
from ...utils import print_with_color
from ..basic import CommandBasic, ReceiverBasic, ReceiverFactory
from .utils import get_control_info

from typing import Dict, List
from abc import abstractmethod

configs = Config.get_instance().config_data



class ControlReceiver(ReceiverBasic):
    def __init__(self, control, application):
        """
        Initialize the control receiver.
        :param control: The control element.
        :param application: The application element.
        """
        super().__init__()

        self.control = control

        if control:
            self.control_info = get_control_info(control)
            self.control.set_focus()
            self.wait_enabled()
        self.application = application


    def get_default_command_registry(self):
        """
        The default command registry.
        """
        return {
            "click_input": ClickInputCommand,
            "summary": SummaryCommand,
            "set_edit_text": SetEditTextCommand,
            "texts": GetTextsCommand,
            "wheel_mouse_input": WheelMouseInputCommand,
            "annotation": AnnotationCommand,
            "": NoActionCommand
        }


    def atomic_execution(self, method_name:str, params:Dict) -> str:
        """
        Atomic execution of the action on the control elements.
        :param control: The control element to execute the action.
        :param method: The method to execute.
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
    

    def click_input(self, params:Dict):
        """
        Click the control element.
        :param params: The arguments of the click method.
        :return: The result of the click action.
        """
        return self.atomic_execution(self.control, "click_input", params)
    

    def summary(self, params:Dict):
        """
        Visual summary of the control element.
        :param params: The arguments of the visual summary method. should contain a key "text" with the text summary.
        :return: The result of the visual summary action.
        """

        return params.get("text")
    

    def set_edit_text(self, params:Dict):
        """
        Set the edit text of the control element.
        :param params: The arguments of the set edit text method.
        :return: The result of the set edit text action.
        """
        
        if configs["INPUT_TEXT_API"] == "set_text":
            method_name = "set_text"
            args = {"text": params["text"]}   
        else:
            method_name = "type_keys"
            args = {"keys": params["text"], "pause": 0.1, "with_spaces": True}
        try:
            result = self.atomic_execution(self.control, method_name, args)
            if method_name == "set_text" and args["text"] not in self.control.window_text():
                raise Exception(f"Failed to use set_text: {args['text']}")
            if configs["INPUT_TEXT_ENTER"] and method_name in ["type_keys", "set_text"]:
                self.atomic_execution(self.control, "type_keys", args = {"keys": "{ENTER}"})
            return result
        except Exception as e:
            if method_name == "set_text":
                print_with_color(f"{self.control} doesn't have a method named {method_name}, trying default input method", "yellow")
                method_name = "type_keys"
                clear_text_keys = "^a{BACKSPACE}"
                text_to_type = args["text"]
                keys_to_send = clear_text_keys + text_to_type
                method_name = "type_keys"
                args = {"keys": keys_to_send, "pause": 0.1, "with_spaces": True}
                return self.atomic_execution(self.control, method_name, args)
            else:
                return f"An error occurred: {e}"
 

    def texts(self) -> str:
        """
        Get the text of the control element.
        :param args: The arguments of the text method.
        :return: The text of the control element.
        """
        return self.control.texts()
    


    def wheel_mouse_input(self, params:dict):
        """
        Wheel mouse input on the control element.
        :param params: The arguments of the wheel mouse input method.
        :return: The result of the wheel mouse input action.
        """
        return self.atomic_execution(self.control, "wheel_mouse_input", params)
    

    def no_action(self):
        """
        No action on the control element.
        :return: The result of the no action.
        """

        return ""
    

    def annotation(self, params:Dict, annotation_dict:Dict) -> List[str]:
        """
        Take a screenshot of the current application window and annotate the control item on the screenshot.
        :param args_dict: The arguments of the annotation method.
        :param annotation_dict: The dictionary of the control labels.
        """
        selected_controls_labels = params.get("control_labels", [])

        control_reannotate = [annotation_dict[str(label)] for label in selected_controls_labels]

        return control_reannotate
    


    def wait_enabled(self, timeout:int=10, retry_interval:int=0.5):
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

    
    def wait_visible(self, timeout:int=10, retry_interval:int=0.5):
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



class AtomicCommand(ControlCommand):
    """
    The atomic command class.
    """
    def __init__(self, receiver: ControlReceiver,  method_name: str, params=None) -> None:
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
        :param args_dict: The arguments of the method.
        :return: The result of the atomic command.
        """
        return self.receiver.atomic_execution(self.method_name, self.params)
    



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
    

class AnnotationCommand(ControlCommand):
    """
    The annotation command class.
    """

    def __init__(self, receiver: ControlReceiver, params:Dict, annotation_dict:Dict) -> None:
        """
        Initialize the annotation command.
        :param receiver: The receiver of the command.
        :param args_dict: The arguments of the annotation method.
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
    