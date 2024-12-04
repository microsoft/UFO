import logging
from multiprocessing import process
import re
from time import sleep
from typing import Optional
import psutil

from fuzzywuzzy import fuzz
from pywinauto import Desktop
from pywinauto.controls.uiawrapper import UIAWrapper

from dataflow.config.config import Config

# Load configuration settings
_configs = Config.get_instance().config_data
if _configs is not None:
    _BACKEND = _configs["CONTROL_BACKEND"]
    _MATCH_STRATEGY = _configs.get("MATCH_STRATEGY", "contains")


class WindowsAppEnv:
    """
    Represents the Windows Application Environment.
    """

    def __init__(self, app_object: object) -> None:
        """
        Initializes the Windows Application Environment.
        :param app_object: The app object containing information about the application.
        """

        self.app_window = None
        self.app_root_name = app_object.app_root_name
        self.app_name = app_object.description.lower()
        self.win_app = app_object.win_app

    def start(self, copied_template_path: str) -> None:
        """
        Starts the Windows environment.
        :param copied_template_path: The file path to the copied template to start the environment.
        """

        from ufo.automator.ui_control import openfile

        file_controller = openfile.FileController(_BACKEND)
        try:
            file_controller.execute_code(
                {"APP": self.win_app, "file_path": copied_template_path}
            )
        except Exception as e:
            logging.exception(f"Failed to start the application: {e}")
            raise

    def close(self) -> None:
        """
        Tries to gracefully close the application; if it fails or is not closed, forcefully terminates the process.
        """

        try:
            # Attempt to close gracefully
            if self.app_window:
                self.app_window.close()
            
            self._check_and_kill_process()
            sleep(1)
        except Exception as e:
            logging.warning(f"Graceful close failed: {e}. Attempting to forcefully terminate the process.")
            self._check_and_kill_process()
            raise e
    
    def _check_and_kill_process(self) -> None:
        """
        Checks if the process is still running and kills it if it is.
        """

        try:
            # Ensure the app_window object is still valid and visible
            if self.app_window and not self.app_window.is_visible():
                process = psutil.Process(self.app_window.process_id)
                if process.is_running():
                    print(f"Killing process: {self.app_window.process_id}")
                    process.terminate()
        except Exception as e:
            logging.error(f"Error while checking window status: {e}")
            raise e

    def find_matching_window(self, doc_name: str) -> Optional[UIAWrapper]:
        """
        Finds a matching window based on the process name and the configured matching strategy.
        :param doc_name: The document name associated with the application.
        :return: The matched window or None if no match is found.
        """

        desktop = Desktop(backend=_BACKEND)
        windows_list = desktop.windows()
        for window in windows_list:
            window_title = window.element_info.name.lower()
            if self._match_window_name(window_title, doc_name):
                self.app_window = window
                return window
        return None

    def _match_window_name(self, window_title: str, doc_name: str) -> bool:
        """
        Matches the window name based on the strategy specified in the config file.
        :param window_title: The title of the window.
        :param doc_name: The document name associated with the application.
        :return: True if a match is found based on the strategy; False otherwise.
        """

        app_name = self.app_name
        doc_name = doc_name.lower()

        if _MATCH_STRATEGY == "contains":
            return app_name in window_title and doc_name in window_title
        elif _MATCH_STRATEGY == "fuzzy":
            similarity_app = fuzz.partial_ratio(window_title, app_name)
            similarity_doc = fuzz.partial_ratio(window_title, doc_name)
            return similarity_app >= 70 and similarity_doc >= 70
        elif _MATCH_STRATEGY == "regex":
            combined_name_1 = f"{app_name}.*{doc_name}"
            combined_name_2 = f"{doc_name}.*{app_name}"
            pattern_1 = re.compile(combined_name_1, flags=re.IGNORECASE)
            pattern_2 = re.compile(combined_name_2, flags=re.IGNORECASE)
            return (
                re.search(pattern_1, window_title) is not None
                or re.search(pattern_2, window_title) is not None
            )
        else:
            logging.exception(f"Unknown match strategy: {_MATCH_STRATEGY}")
            raise ValueError(f"Unknown match strategy: {_MATCH_STRATEGY}")

    def is_matched_controller( 
        self, control_to_match: UIAWrapper, control_text: str
    ) -> bool:
        """
        Matches the controller based on the strategy specified in the config file.
        :param control_to_match: The control object to match against.
        :param control_text: The text content of the control for additional context.
        :return: True if a match is found based on the strategy; False otherwise.
        """

        control_content = (
            control_to_match.window_text() if control_to_match.window_text() else ""
        )  # Default to empty string

        # Match strategies based on the configured _MATCH_STRATEGY
        if _MATCH_STRATEGY == "contains":
            return (
                control_text in control_content
            )  # Check if the control's content contains the target text
        elif _MATCH_STRATEGY == "fuzzy":
            # Fuzzy matching to compare the content
            similarity_text = fuzz.partial_ratio(control_content, control_text)
            return similarity_text >= 70  # Set a threshold for fuzzy matching
        elif _MATCH_STRATEGY == "regex":
            # Use regular expressions for more flexible matching
            pattern = re.compile(f"{re.escape(control_text)}", flags=re.IGNORECASE)
            return (
                re.search(pattern, control_content) is not None
            )  # Return True if pattern matches control content
        else:
            logging.exception(f"Unknown match strategy: {_MATCH_STRATEGY}")
            raise ValueError(f"Unknown match strategy: {_MATCH_STRATEGY}")
