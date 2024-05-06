# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, List

import psutil
from pywinauto import Desktop
from pywinauto.controls.uiawrapper import UIAWrapper

from ufo.config.config import Config

configs = Config.get_instance().config_data


class BackendFactory:
    """
    A factory class to create backend strategies.
    """

    @staticmethod
    def create_backend(backend: str) -> BackendStrategy:
        """
        Create a backend strategy.
        :param backend: The backend to use.
        :return: The backend strategy.
        """
        if backend == "uia":
            return UIABackendStrategy()
        elif backend == "win32":
            return Win32BackendStrategy()
        else:
            raise ValueError(f"Backend {backend} not supported")


class BackendStrategy(ABC):
    """
    Define an interface for backend strategies.
    """

    @abstractmethod
    def get_desktop_windows(self, remove_empty: bool) -> List[UIAWrapper]:
        """
        Get all the apps on the desktop.
        :param remove_empty: Whether to remove empty titles.
        :return: The apps on the desktop.
        """
        pass

    @abstractmethod
    def find_control_elements_in_descendants(
        self,
        window: UIAWrapper,
        control_type_list: List[str] = [],
        class_name_list: List[str] = [],
        title_list: List[str] = [],
        is_visible: bool = True,
        is_enabled: bool = True,
        depth: int = 0,
    ) -> List[UIAWrapper]:
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

        pass


class UIABackendStrategy(BackendStrategy):
    """
    The backend strategy for UIA.
    """

    def get_desktop_windows(self, remove_empty: bool) -> List[UIAWrapper]:
        """
        Get all the apps on the desktop.
        :param remove_empty: Whether to remove empty titles.
        :return: The apps on the desktop.
        """
        desktop_windows = Desktop(backend="uia").windows()
        if remove_empty:
            desktop_windows = [
                app
                for app in desktop_windows
                if app.window_text() != ""
                and app.element_info.class_name not in ["IME", "MSCTFIME UI"]
            ]
        return desktop_windows

    def find_control_elements_in_descendants(
        self,
        window: UIAWrapper,
        control_type_list: List[str] = [],
        class_name_list: List[str] = [],
        title_list: List[str] = [],
        is_visible: bool = True,
        is_enabled: bool = True,
        depth: int = 0,
    ) -> List[UIAWrapper]:
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

        if window == None:
            return []

        control_elements = []
        if len(control_type_list) == 0:
            control_elements += window.descendants()
        else:
            for control_type in control_type_list:
                if depth == 0:
                    subcontrols = window.descendants(control_type=control_type)
                else:
                    subcontrols = window.descendants(
                        control_type=control_type, depth=depth
                    )
                control_elements += subcontrols

        if is_visible:
            control_elements = [
                control for control in control_elements if control.is_visible()
            ]
        if is_enabled:
            control_elements = [
                control for control in control_elements if control.is_enabled()
            ]
        if len(title_list) > 0:
            control_elements = [
                control
                for control in control_elements
                if control.window_text() in title_list
            ]
        if len(class_name_list) > 0:
            control_elements = [
                control
                for control in control_elements
                if control.element_info.class_name in class_name_list
            ]

        return control_elements


class Win32BackendStrategy(BackendStrategy):
    """
    The backend strategy for Win32.
    """

    def get_desktop_windows(self, remove_empty: bool) -> List[UIAWrapper]:
        """
        Get all the apps on the desktop.
        :param remove_empty: Whether to remove empty titles.
        :return: The apps on the desktop.
        """

        desktop_windows = Desktop(backend="win32").windows()
        desktop_windows = [app for app in desktop_windows if app.is_visible()]

        if remove_empty:
            desktop_windows = [
                app
                for app in desktop_windows
                if app.window_text() != ""
                and app.element_info.class_name not in ["IME", "MSCTFIME UI"]
            ]
        return desktop_windows

    def find_control_elements_in_descendants(
        self,
        window: UIAWrapper,
        control_type_list: List[str] = [],
        class_name_list: List[str] = [],
        title_list: List[str] = [],
        is_visible: bool = True,
        is_enabled: bool = True,
        depth: int = 0,
    ) -> List[UIAWrapper]:
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

        if window == None:
            return []

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
            control_elements = [
                control for control in control_elements if control.is_visible()
            ]
        if is_enabled:
            control_elements = [
                control for control in control_elements if control.is_enabled()
            ]
        if len(title_list) > 0:
            control_elements = [
                control
                for control in control_elements
                if control.window_text() in title_list
            ]
        if len(control_type_list) > 0:
            control_elements = [
                control
                for control in control_elements
                if control.element_info.control_type in control_type_list
            ]

        return [
            control for control in control_elements if control.element_info.name != ""
        ]


class ControlInspectorFacade:
    """
    The facade class for control inspector.
    """

    def __init__(self, backend: str = "uia") -> None:
        """
        Initialize the control inspector.
        :param backend: The backend to use.
        """

        self.backend = backend
        self.backend_strategy = BackendFactory.create_backend(backend)

    def get_desktop_windows(self, remove_empty: bool = True) -> List[UIAWrapper]:
        """
        Get all the apps on the desktop.
        :param remove_empty: Whether to remove empty titles.
        :return: The apps on the desktop.
        """
        return self.backend_strategy.get_desktop_windows(remove_empty)

    def find_control_elements_in_descendants(
        self,
        window: UIAWrapper,
        control_type_list: List[str] = [],
        class_name_list: List[str] = [],
        title_list: List[str] = [],
        is_visible: bool = True,
        is_enabled: bool = True,
        depth: int = 0,
    ) -> List[UIAWrapper]:
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
        if self.backend == "uia":
            return self.backend_strategy.find_control_elements_in_descendants(
                window, control_type_list, [], title_list, is_visible, is_enabled, depth
            )
        elif self.backend == "win32":
            return self.backend_strategy.find_control_elements_in_descendants(
                window, [], class_name_list, title_list, is_visible, is_enabled, depth
            )
        else:
            return []

    def get_desktop_app_dict(self, remove_empty: bool = True) -> Dict[str, UIAWrapper]:
        """
        Get all the apps on the desktop and return as a dict.
        :param remove_empty: Whether to remove empty titles.
        :return: The apps on the desktop as a dict.
        """
        desktop_windows = self.get_desktop_windows(remove_empty)
        desktop_windows_dict = dict(
            zip([str(i + 1) for i in range(len(desktop_windows))], desktop_windows)
        )
        return desktop_windows_dict

    def get_desktop_app_info(
        self,
        desktop_windows_dict: Dict[str, UIAWrapper],
        field_list: List[str] = ["control_text", "control_type"],
    ) -> List[Dict[str, str]]:
        """
        Get control info of all the apps on the desktop.
        :param desktop_windows_dict: The dict of apps on the desktop.
        :param field_list: The fields of app info to get.
        :return: The control info of all the apps on the desktop.
        """
        desktop_windows_info = self.get_control_info_list_of_dict(
            desktop_windows_dict, field_list
        )
        return desktop_windows_info

    def get_control_info_batch(
        self, window_list: List[UIAWrapper], field_list: List[str] = []
    ) -> List[Dict[str, str]]:
        """
        Get control info of the window.
        :param window: The list of windows to get control info.
        :param field_list: The fields to get.
        return: The list of control info of the window.
        """
        control_info_list = []
        for window in window_list:
            control_info_list.append(self.get_control_info(window, field_list))
        return control_info_list

    def get_control_info_list_of_dict(
        self, window_dict: Dict[str, UIAWrapper], field_list: List[str] = []
    ) -> List[Dict[str, str]]:
        """
        Get control info of the window.
        :param window_dict: The dict of windows to get control info.
        :param field_list: The fields to get.
        return: The list of control info of the window.
        """
        control_info_list = []
        for key in window_dict.keys():
            window = window_dict[key]
            control_info = self.get_control_info(window, field_list)
            control_info["label"] = key
            control_info_list.append(control_info)
        return control_info_list

    @staticmethod
    def get_control_info(
        window: UIAWrapper, field_list: List[str] = []
    ) -> Dict[str, str]:
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

    @staticmethod
    def get_application_root_name(window: UIAWrapper) -> str:
        """
        Get the application name of the window.
        :param window: The window to get the application name.
        :return: The root application name of the window. Empty string ("") if failed to get the name.
        """
        if window == None:
            return ""
        process_id = window.process_id()
        try:
            process = psutil.Process(process_id)
            return process.name()
        except psutil.NoSuchProcess:
            return ""
