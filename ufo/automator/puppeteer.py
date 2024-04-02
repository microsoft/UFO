# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from .ui_control.controller import UIController
from word.wordclient import Word


class AppPuppeteer():
    """
    The base class for the app expert.
    """

    def __init__(self, process_name, app_root_name, ui_control_interface) -> None:
        
        self._process_name = process_name
        self._app_root_name = app_root_name
        self.ui_control_interface = ui_control_interface


    def get_com_client(self) -> None:
        """
        Get the COM client.
        :param app_root_name: The app root name.
        :param process_name: The process name.
        """
        win_com_client_mapping = {
            "WINWORD.EXE": Word(self._app_root_name, self._app_root_name),

        }

        return win_com_client_mapping.get(self._app_root_name, None)


    def create_ui_controller(self, control: object) -> UIController:
        """
        Build the UI controller.
        :param control: The control element.
        :return: The UI controller.
        """
        return UIController(control, self.ui_control_interface)