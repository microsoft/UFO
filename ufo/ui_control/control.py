# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import ast
import time
import warnings
from typing import List
import psutil
from pywinauto import Desktop

from ..config.config import load_config

configs = load_config()

BACKEND = configs["CONTROL_BACKEND"]


def get_desktop_app_info(remove_empty:bool=True):
    """
    Get titles and control types of all the apps on the desktop.
    :param remove_empty: Whether to remove empty titles.
    :return: The titles and control types of all the apps on the desktop.
    """
    app_list = Desktop(backend=BACKEND).windows()
    app_titles = [app.window_text() for app in app_list]
    app_control_types = [app.element_info.control_type for app in app_list]

    if remove_empty:
        app_control_types = [app_control_types[i] for i, title in enumerate(app_titles) if title != ""]
        app_titles = [title for title in app_titles if title != ""]
    return [app_titles, app_control_types]




def get_desktop_app_info_dict(remove_empty:bool=True, field_list:List[str]=["control_text", "control_type"]):
    """
    Get titles and control types of all the apps on the desktop.
    :param remove_empty: Whether to remove empty titles.
    :return: The titles and control types of all the apps on the desktop.
    """
    desktop_windows = Desktop(BACKEND).windows()
        
    if remove_empty:
         desktop_windows = [app for app in desktop_windows if app.window_text()!= "" and app.element_info.class_name not in ["IME", "MSCTFIME UI", "TXGuiFoundation"]]
    desktop_windows_dict = dict(zip([str(i+1) for i in range(len(desktop_windows))], desktop_windows))
    desktop_windows_info = get_control_info_dict(desktop_windows_dict, field_list)
    return desktop_windows_dict, desktop_windows_info


    
def find_control_elements_in_descendants(window, control_type_list:List[str]=[], class_name_list:List[str]=[], title_list:List[str]=[], is_visible:bool=True, is_enabled:bool=True, depth:int=0):
    """
    Find control elements in descendants of the window.
    :param window: The window to find control elements.
    :param control_type_list: The control types to find.
    :param class_name_list: The class names to find.
    :param title_list: The titles to find.
    :param is_visible: Whether the control elements are visible.
    :param is_enabled: Whether the control elements are enabled.
    :param depth: The depth of the descendants to find.
    :return: The control elements found.
    """
    control_elements = []
    if len(control_type_list) == 0:
        control_elements += window.descendants()
    else:
        for control_type in control_type_list:
            if depth == 0:
                subcontrols = window.descendants(control_type=control_type)
            else:
                subcontrols = window.descendants(control_type=control_type, depth=depth)
            control_elements += subcontrols

    if is_visible:
        control_elements = [control for control in control_elements if control.is_visible()]
    if is_enabled:
        control_elements = [control for control in control_elements if control.is_enabled()]
    if len(title_list) > 0:
        control_elements = [control for control in control_elements if control.window_text() in title_list]
    if len(class_name_list) > 0:
        control_elements = [control for control in control_elements if control.element_info.class_name in class_name_list]

    return control_elements
    


def get_control_info(window, field_list:List[str]=[]):
    """
    Get control info of the window.
    :param window: The window to get control info.
    :param field_list: The fields to get.
    return: The control info of the window.
    """
    control_info = {}
    try:
        control_info["control_type"] = window.element_info.control_type
        control_info["control_id"] = window.element_info.control_id
        control_info["control_class"] = window.element_info.class_name
        control_info["control_name"] = window.element_info.name
        control_info["control_rect"] = window.element_info.rectangle
        control_info["control_text"] = window.element_info.name
        control_info["control_title"] = window.window_text()
    except:
        return {}

    if len(field_list) > 0:
        control_info = {field: control_info[field] for field in field_list}
    return control_info



def get_control_info_batch(window_list:List, field_list:List[str]=[]):
    """
    Get control info of the window.
    :param window: The list of windows to get control info.
    :param field_list: The fields to get.
    return: The list of control info of the window.
    """
    control_info_list = []
    for window in window_list:
        control_info_list.append(get_control_info(window, field_list))
    return control_info_list



def get_control_info_dict(window_dict:dict, field_list:List[str]=[]):
    """
    Get control info of the window.
    :param window: The list of windows to get control info.
    :param field_list: The fields to get.
    return: The list of control info of the window.
    """
    control_info_list = []
    for key in window_dict.keys():
        window = window_dict[key]  
        control_info = get_control_info(window, field_list)
        control_info["label"] = key
        control_info_list.append(control_info)
    return control_info_list


def replace_newline(input_str):
    """
    Replace \n with \\n.
    :param input_str: The string to replace.
    :return: The replaced string.
    """
    # Replace \n with \\n
    result_str = input_str.replace('\n', '\\n')

    # Check if there are already \\n in the string
    if '\\\\n' in result_str:
        # If found, revert \\n to \n
        result_str = result_str.replace('\\\\n', '\\n')

    return result_str


def parse_function_call(call):
    """
    Parse the function call.
    :param call: The function call.
    :return: The function name and arguments."""

    node = ast.parse(call)

    # Get the function name and arguments
    func_name = node.body[0].value.func.id
    args = {arg.arg: ast.literal_eval(arg.value) for arg in node.body[0].value.keywords}

    return func_name, args



def atomic_execution(window, method_name:str, args:dict):
    """
    Atomic execution of the action on the control elements.
    :param window: The window variable to execute the action.
    :param method: The method to execute.
    :param args: The arguments of the method.
    :return: The result of the action.
    """
    try:
        method = getattr(window, method_name)
        result = method(**args)
    except AttributeError:
        result = f"{window} doesn't have a method named {method_name}"
    except Exception as e:
        result = f"An error occurred: {e}"
    return result


def execution(window, method_name:str, args:dict):
    """
    Execute the action on the control elements.
    :param window: The window variable to execute the action.
    :param method: The method to execute.
    :param args: The arguments of the method.
    :return: The result of the action.
    """


    if method_name == "set_edit_text":
        if configs["INPUT_TEXT_API"] == "type_keys":
            method_name = "type_keys"
            args = {"keys": args["text"], "pause": 0.1, "with_spaces": True}
    try:
        result = atomic_execution(window, method_name, args)
        if configs["INPUT_TEXT_ENTER"] and method_name in ["type_keys", "set_edit_text"]:
            atomic_execution(window, "type_keys", args = {"keys": "{ENTER}"})
        return result
    except Exception as e:
        return f"An error occurred: {e}"
    


def wait_enabled(window, timeout:int=10, retry_interval:int=0.5):
    """
    Wait until the window is enabled.
    :param window: The window to wait.
    :param timeout: The timeout to wait.
    :param retry_interval: The retry interval to wait.
    """
    while not window.is_enabled():
        time.sleep(retry_interval)
        timeout -= retry_interval
        if timeout <= 0:
            warnings.warn(f"Timeout: {window} is not enabled.")
            break
    return



def wait_visible(window, timeout:int=10, retry_interval:int=0.5):
    """
    Wait until the window is enabled.
    :param window: The window to wait.
    :param timeout: The timeout to wait.
    :param retry_interval: The retry interval to wait.
    """
    while not window.is_visible():
        time.sleep(retry_interval)
        timeout -= retry_interval
        if timeout <= 0:
            warnings.warn(f"Timeout: {window} is not visible.")
            break
    return

   

def get_application_name(window) -> str:
    """
    Get the application name of the window.
    :param window: The window to get the application name.
    :return: The application name of the window. Empty string ("") if failed to get the name.
    """
    if window == None:
        return ""
    process_id = window.process_id()
    try:
        process = psutil.Process(process_id)
        return process.name()
    except psutil.NoSuchProcess:
        return ""