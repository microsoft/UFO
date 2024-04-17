# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import time
import warnings

from ...config.config import Config
from .utils import get_control_info, AppMappings
from ... import utils
import psutil
from pywinauto import Desktop


configs = Config.get_instance().config_data



class UIController:
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
            utils.print_with_color(message, "red")
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
        
        if configs["INPUT_TEXT_API"] == "set_text":
            method_name = "set_text"
            args = {"text": args_dict["text"]}   
        else:
            method_name = "type_keys"
            args = {"keys": args_dict["text"], "pause": 0.1, "with_spaces": True}
        try:
            result = self.atomic_execution(self.control, method_name, args)
            if method_name == "set_text" and args["text"] not in self.control.window_text():
                raise Exception(f"Failed to use set_text: {args['text']}")
            if configs["INPUT_TEXT_ENTER"] and method_name in ["type_keys", "set_text"]:
                self.atomic_execution(self.control, "type_keys", args = {"keys": "{ENTER}"})
            return result
        except Exception as e:
            if method_name == "set_text":
                utils.print_with_color(f"{self.control} doesn't have a method named {method_name}, trying default input method", "yellow")
                method_name = "type_keys"
                clear_text_keys = "^a{BACKSPACE}"
                text_to_type = args["text"]
                keys_to_send = clear_text_keys + text_to_type
                method_name = "type_keys"
                args = {"keys": keys_to_send, "pause": 0.1, "with_spaces": True}
                return self.atomic_execution(self.control, method_name, args)
            else:
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
            utils.print_with_color(f"Warning: {message}", "yellow")
            result = message
        except Exception as e:
            message = f"An error occurred: {e}"
            utils.print_with_color(f"Warning: {message}", "yellow")
            result = message
        return result
    

configs = Config.get_instance().config_data

BACKEND = configs["CONTROL_BACKEND"]
class FileController():
    """
    Control block for open file / specific APP and proceed the operation.
    """
    def __init__(self):

        self.backend = BACKEND
        self.file_path = ""
        self.APP = ""
        self.apptype = ""
        self.openstatus = False
        self.error = ""
        self.win_app = ["powerpnt", "winword", "outlook", "ms-settings:", "explorer", "notepad", "msteams:", "ms-todo:"]

    def execute_code(self, args: dict) -> bool:
        """
        Execute the code to open some files.
        :param args: The arguments of the code, which should at least contains name of APP and the file path we want to open
        (ps. filepath can be empty.)
        :return: The result of the execution or error.
        """
        self.APP = args["APP"]
        self.file_path = args.get("file_path", "")
        self.check_open_status()
        if self.openstatus:
            if self.file_path == "":
                return True
            else:
                if self.is_file_open_in_app():
                    return True
        if self.APP in self.win_app: #if fine with the app, then open it
            if "Desktop" in self.file_path:
                desktop_path = utils.find_desktop_path()
                self.file_path = self.file_path.replace("Desktop", desktop_path) #locate actual desktop path
            if self.file_path == "":
                code_snippet = f"import os\nos.system('start {self.APP}')"
            else:
                code_snippet = f"import os\nos.system('start {self.APP} \"{self.file_path}\"')"
            code_snippet = code_snippet.replace("\\", "\\\\")
            try:
                exec(code_snippet, globals())
                time.sleep(3) #wait for the app to boot
                return True

            except Exception as e:
                utils.print_with_color(f"An error occurred: {e}", "red")
                return False
        else:
            utils.print_with_color(f"Third party APP: {self.APP} is not supported yet.", "green")
            return False

    def check_open_status(self) -> bool:
        """
        Check the open status of the file.
        :return: The open status of the file.
        """
        if self.APP == "explorer":
            self.openstatus = False
            return
        app_map = AppMappings()
        likely_process_names = app_map.get_process_names(self.APP.lower())  # Get the likely process names of the app
        for proc in psutil.process_iter(['name']):
            if proc.info['name'] in likely_process_names:
                self.openstatus = True
                print(f"{self.APP} is already open.")
                return
        self.openstatus = False
    

    def is_file_open_in_app(self) -> bool:
        """
        Check if the specific file is opened in the app.
        :return: Open status of file, not correlated with self.openstatus.
        """
        app_map = AppMappings()
        app_name = app_map.get_app_name(self.APP.lower())
        file_name = self.file_path
        if "\\" in self.file_path:
            file_name = self.file_path.split("\\")[-1]
        desktop = Desktop(backend="uia")
        for window in desktop.windows():
            if app_name in window.window_text() and file_name in window.window_text():      #make sure the file is successfully opened in the app
                return True
        return False


    def open_third_party_APP(self, args: dict) -> bool:
        # TODO: open third party app
        pass
    

