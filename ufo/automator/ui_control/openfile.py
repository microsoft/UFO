# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import time
from typing import List

import psutil
from pywinauto import Desktop

from ...config.config import Config
from ... import utils 


configs = Config.get_instance().config_data

BACKEND = configs["CONTROL_BACKEND"]

class AppMappings:
    """
    Mappings for OpenFile class.
    app_name_map: a mapping from the key/command to the name of the app.
    app_process_map: a mapping from the key/command to the process name of the app."""
    app_name_map = {
        "powerpnt": "PowerPoint",
        "winword": "Word",
        "outlook": "Outlook",
        "explorer": "Explorer",
        "notepad": "Notepad",
        "msteams:": "Microsoft Teams",
        "ms-todo:": "Microsoft To Do",
        "edge": "Microsoft Edge",
        "chrome": "Google Chrome",
        "firefox": "Firefox",
        "excel": "Excel",
        "ms-settings:": "Settings"
    }

    app_process_map = {
        "powerpnt": ["POWERPNT.EXE", "powerpnt"],
        "winword": ["WINWORD.EXE", "winword"],
        "outlook": ["OUTLOOK.EXE", "outlook"],
        "explorer": ["explorer.exe"],
        "notepad": ["notepad.exe", "notepad"],
        "msteams:": ["Teams.exe", "teams", "msteams"],
        "ms-todo:": ["Todo.exe", "todo", "ms-todo"],
        "edge": ["msedge.exe", "edge"],
        "chrome": ["chrome.exe", "chrome"],
        "firefox": ["firefox.exe", "firefox"],
        "excel": ["EXCEL.EXE", "excel"],
        "ms-settings:": ["SystemSettings.exe", "ms-settings"],
    }

    @classmethod
    def get_app_name(cls, key):
        return cls.app_name_map.get(key, "Unknown App")

    @classmethod
    def get_process_names(cls, key):
        return cls.app_process_map.get(key, [key])

class OpenFile:
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
        if self.APP in self.win_app:
            if "Desktop" in self.file_path:
                desktop_path = utils.find_desktop_path()
                self.file_path = self.file_path.replace("Desktop", desktop_path)
            if self.file_path == "":
                code_snippet = f"import os\nos.system('start {self.APP}')"
            else:
                code_snippet = f"import os\nos.system('start {self.APP} \"{self.file_path}\"')"
            code_snippet = code_snippet.replace("\\", "\\\\")
            try:
                exec(code_snippet, globals())
                time.sleep(3)
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
        likely_process_names = app_map.get_process_names(self.APP.lower())
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
            if app_name in window.window_text() and file_name in window.window_text():
                return True
        return False


    def open_third_party_APP(self, args: dict) -> bool:
        # TODO: open third party app
        pass