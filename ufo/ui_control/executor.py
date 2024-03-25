# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import time
import warnings

from ..config.config import load_config
from .control import get_control_info
from ..utils import print_with_color


configs = load_config()



class ActionExecutor:
    """
    The action executor class.
    """

    def __init__(self, control: object, application: object) -> None:
        """
        Initialize the action executor.
        :param control: The control element to execute the action.
        :param application: The application of the control element.
        """
        
        self.control = control
        if control:
            self.control_info = get_control_info(control)
            self.control.set_focus()
            self.wait_enabled()

        self.application = application



    def get_method(self, method_name:str) -> callable:
        """
        Get the method of the control element.
        :param method_name: The name of the method.
        :return: The method of the control element.
        """
        method_name = str(method_name)

        mappping = {
            "click_input": self.__click_input,
            "summary": self.__summary,
            "set_edit_text": self.__set_edit_text,
            "texts": self.__texts,
            "wheel_mouse_input": self.__wheel_mouse_input,
            "": self.__no_action
        }

        return mappping.get(method_name.lower(), None)
    

    def execution(self, method_name:str, args_dict:dict) -> str:
        """
        Execute the action on the control elements.
        :param method: The method to execute.
        :param args: The arguments of the method.
        :return: The result of the action.
        """
        method = self.get_method(method_name)

        if not method:
            message = f"{self.control} doesn't have a method named {method_name}"
            print_with_color(message, "red")
            return message
        
        return method(args_dict)
    
    
    
    def __click_input(self, args_dict:dict):
        """
        Click the control element.
        :param args: The arguments of the click method.
        :return: The result of the click action.
        """
        return self.atomic_execution(self.control, "click_input", args_dict)
    

    def __summary(self, args_dict):
        """
        Visual summary of the control element.
        :param args_dict: The arguments of the visual summary method. should contain a key "text" with the text summary.
        :return: The result of the visual summary action.
        """

        return args_dict.get("text")
    


    def __set_edit_text(self, args_dict:dict):
        """
        Set the edit text of the control element.
        :param args: The arguments of the set edit text method.
        :return: The result of the set edit text action.
        """
        if configs["INPUT_TEXT_API"] == "type_keys":
            method_name = "type_keys"
            args = {"keys": args_dict["text"], "pause": 0.1, "with_spaces": True}
        else:
            args = {"text": args_dict["text"]}

        try:
            result = self.atomic_execution(self.control, method_name, args)
            if configs["INPUT_TEXT_ENTER"] and method_name in ["type_keys", "set_edit_text"]:
                self.atomic_execution(self.control, "type_keys", args = {"keys": "{ENTER}"})
            return result
        except Exception as e:
            return f"An error occurred: {e}"
    


    def __texts(self, args_dict:dict) -> str:
        """
        Get the text of the control element.
        :param args: The arguments of the text method.
        :return: The text of the control element.
        """
        return self.control.texts()
    


    def __wheel_mouse_input(self, args_dict:dict):
        """
        Wheel mouse input on the control element.
        :param args: The arguments of the wheel mouse input method.
        :return: The result of the wheel mouse input action.
        """
        return self.atomic_execution(self.control, "wheel_mouse_input", args_dict)
    

    def __no_action(self, args_dict:dict):

        return ""
    

    def annotation(self, args_dict:dict, annotation_dict:dict):
        """
        Take a screenshot of the current application window and annotate the control item on the screenshot.
        :param args_dict: The arguments of the annotation method.
        :param annotation_dict: The dictionary of the control labels.
        """

        selected_controls_labels = args_dict.get("control_labels", [])
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
    


    @staticmethod
    def atomic_execution(control, method_name:str, args:dict) -> str:
        """
        Atomic execution of the action on the control elements.
        :param control: The control element to execute the action.
        :param method: The method to execute.
        :param args: The arguments of the method.
        :return: The result of the action.
        """
        try:
            method = getattr(control, method_name)
            result = method(**args)
        except AttributeError:
            message = f"{control} doesn't have a method named {method_name}"
            print_with_color(f"Warning: {message}", "yellow")
            result = message
        except Exception as e:
            message = f"An error occurred: {e}"
            print_with_color(f"Warning: {message}", "yellow")
            result = message
        return result
    

