# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.


from typing import List, Tuple

import psutil
from pywinauto import Desktop

from ...config.config import Config


configs = Config.get_instance().config_data

BACKEND = configs["CONTROL_BACKEND"]


def get_desktop_app_info(remove_empty: bool=True) -> Tuple[dict, List[dict]]:
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
    return app_titles, app_control_types




def get_desktop_app_info_dict(remove_empty: bool=True, field_list: List[str]=["control_text", "control_type"]) -> Tuple[dict, List[dict]]:
    """
    Get titles and control types of all the apps on the desktop.
    :param remove_empty: Whether to remove empty titles.
    :return: The titles and control types of all the apps on the desktop.
    """
    desktop_windows = Desktop(BACKEND).windows()
    
    # Remove the not visible applications for win32 backend
    if(BACKEND == "win32"):
        desktop_windows = [app for app in desktop_windows if app.is_visible()]

    if remove_empty:
        desktop_windows = [app for app in desktop_windows if app.window_text()!= "" and app.element_info.class_name not in ["IME", "MSCTFIME UI"]]
         
    desktop_windows_dict = dict(zip([str(i+1) for i in range(len(desktop_windows))], desktop_windows))
    desktop_windows_info = get_control_info_dict(desktop_windows_dict, field_list)
    return desktop_windows_dict, desktop_windows_info

    
def find_uia_control_elements_in_descendants(window, control_type_list:List[str]=[], class_name_list:List[str]=[], title_list:List[str]=[], is_visible:bool=True, is_enabled:bool=True, depth:int=0) -> List:
    """
    Find control elements in descendants of the window for uia backend.
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
    
def find_win32_control_elements_in_descendants(window, control_type_list:List[str]=[], class_name_list:List[str]=[], title_list:List[str]=[], is_visible:bool=True, is_enabled:bool=True, depth:int=0) -> List:
    """
    Find control elements in descendants of the window for win32 backend.
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
    if len(class_name_list) == 0:
        control_elements += window.descendants()
    else:
        for class_name in class_name_list:
            if depth == 0:
                subcontrols = window.descendants(class_name=class_name)
            else:
                subcontrols = window.descendants(class_name=class_name, depth=depth)
            control_elements += subcontrols

    if is_visible:
        control_elements = [control for control in control_elements if control.is_visible()]
    if is_enabled:
        control_elements = [control for control in control_elements if control.is_enabled()]
    if len(title_list) > 0:
        control_elements = [control for control in control_elements if control.window_text() in title_list]
    if len(control_type_list) > 0:
        control_elements = [control for control in control_elements if control.element_info.control_type in control_type_list]

    return [control for control in control_elements if control.element_info.name != '']

def get_control_info(window, field_list:List[str]=[]) -> dict:
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



def get_control_info_batch(window_list:List, field_list:List[str]=[]) -> List:
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



def get_control_info_dict(window_dict:dict, field_list:List[str]=[]) -> List[dict]:
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


def replace_newline(input_str : str) -> str:
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