import time
from typing import Dict

import psutil
from pywinauto import Desktop

from ufo import utils
from ufo.config.config import Config

configs = Config.get_instance().config_data

BACKEND = "uia"


class FileController:
    """
    Control block for open file / specific APP and proceed the operation.
    """

    def __init__(self, backend=BACKEND):

        self.backend = backend
        self.file_path = ""
        self.APP = ""
        self.apptype = ""
        self.openstatus = False
        self.error = ""
        self.win_app = [
            "powerpnt",
            "winword",
            "outlook",
            "ms-settings:",
            "explorer",
            "notepad",
            "msteams:",
            "ms-todo:",
            "calc",
            "ms-clock:",
            "mspaint",
        ]
        self.app_map = AppMappings()

    def execute_code(self, args: Dict) -> bool:
        """
        Execute the code to open some files.
        :param args: The arguments of the code, which should at least contains name of APP and the file path we want to open
        (ps. filepath can be empty.)
        :return: The result of the execution or error.
        """

        self.APP = args.get("APP", "")
        self.file_path = args.get("file_path", "")
        self.check_open_status()
        if self.openstatus:
            if self.file_path == "":
                return True
            else:
                if self.is_file_open_in_app():
                    return True
        if self.APP in self.win_app:  # if fine with the app, then open it
            if "Desktop" in self.file_path:
                desktop_path = utils.find_desktop_path()
                self.file_path = self.file_path.replace(
                    "Desktop", desktop_path
                )  # locate actual desktop path
            if self.file_path == "":
                code_snippet = f"import os\nos.system('start {self.APP}')"
            else:
                code_snippet = (
                    f"import os\nos.system('start {self.APP} \"{self.file_path}\"')"
                )
            code_snippet = code_snippet.replace("\\", "\\\\")
            try:
                exec(code_snippet, globals())
                time.sleep(3)  # wait for the app to boot
                return True

            except Exception as e:
                utils.print_with_color(f"An error occurred: {e}", "red")
                return False
        else:
            utils.print_with_color(
                f"Third party APP: {self.APP} is not supported yet.", "green"
            )
            return False

    def check_open_status(self) -> bool:
        """
        Check the open status of the file.
        :return: The open status of the file.
        """
        if self.APP == "explorer":
            self.openstatus = False
            return
        likely_process_names = self.app_map.get_process_names(
            self.APP.lower()
        )  # Get the likely process names of the app
        for proc in psutil.process_iter(["name"]):
            if proc.info["name"] in likely_process_names:
                self.openstatus = True
                print(f"{self.APP} is already open.")
                return
        self.openstatus = False

    def is_file_open_in_app(self) -> bool:
        """
        Check if the specific file is opened in the app.
        :return: Open status of file, not correlated with self.openstatus.
        """
        app_name = self.app_map.get_app_name(self.APP.lower())
        file_name = self.file_path
        if "\\" in self.file_path:
            file_name = self.file_path.split("\\")[-1]
        desktop = Desktop(backend="uia")
        for window in desktop.windows():
            if (
                app_name in window.window_text() and file_name in window.window_text()
            ):  # make sure the file is successfully opened in the app
                return True
        return False

    def open_third_party_APP(self, args: Dict) -> bool:
        # TODO: open third party app
        pass

    def find_window_by_app_name(self, desktop_windows_dict):
        """
        Find the window on windows control panel by the app name.
        :param desktop_windows_dict: The windows on the desktop.
        :param app_name: The app name to find.
        """
        title_pattern = self.app_map.get_app_name(self.APP)
        if title_pattern is None:
            return None
        for window_id, window_wrapper in desktop_windows_dict.items():
            if (
                title_pattern in window_wrapper.window_text()
                or "Home" in window_wrapper.window_text()
                and title_pattern == "Explorer"
            ):
                return window_wrapper
        print("Window not found.")
        return None


class AppMappings:
    """
    Mappings for OpenFile class.
    app_name_map: a mapping from the key/command to the name of the app.
    app_process_map: a mapping from the key/command to the process name of the app.
    """

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
        "ms-settings:": "Settings",
        "calc": "Calculator",
        "ms-clock:": "Clock",
        "mspaint": "Paint",
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
        "ms-clock": ["Time.exe", "ms-clock"],
        "calc": ["CalculatorApp.exe", "calc"],
        "mspaint": ["mspaint.exe", "mspaint"],
    }

    @classmethod
    def get_app_name(cls, key):
        return cls.app_name_map.get(key, "Unknown App")

    @classmethod
    def get_process_names(cls, key):
        return cls.app_process_map.get(key, [key])
