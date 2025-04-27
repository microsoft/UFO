import logging
import re
from time import sleep
from typing import Optional, Tuple, Dict
import psutil

from fuzzywuzzy import fuzz
from pywinauto import Desktop
from pywinauto.controls.uiawrapper import UIAWrapper

from dataflow.config.config import Config
from ufo.config.config import Config as UFOConfig

# Load configuration settings
_configs = Config.get_instance().config_data
_ufo_configs = UFOConfig.get_instance().config_data

if _ufo_configs is not None:
    _BACKEND = "uia"
if _configs is not None:
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
            # Gracefully close the application window
            if self.app_window and self.app_window.process_id():
                self.app_window.close()
            sleep(1)
            # Forcefully close the application window
            if self.app_window.element_info.name.lower() != "":
                self._check_and_kill_process()
        except Exception as e:
            logging.warning(
                f"Graceful close failed: {e}. Attempting to forcefully terminate the process."
            )
            self._check_and_kill_process()
            raise e

    def _check_and_kill_process(self) -> None:
        """
        Checks if the process is still running and kills it if it is.
        """

        try:
            if self.app_window and self.app_window.process_id():
                process = psutil.Process(self.app_window.process_id())
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

    def _calculate_match_score(self, control, control_text) -> int:
        """
        Calculate the match score between a control and the given text.
        :param control: The control object to evaluate.
        :param control_text: The target text to match.
        :return: An integer score representing the match quality (higher is better).
        """
        control_content = control.window_text() or ""

        # Matching strategies
        if _MATCH_STRATEGY == "contains":
            return 100 if control_text in control_content else 0
        elif _MATCH_STRATEGY == "fuzzy":
            return fuzz.partial_ratio(control_content, control_text)
        elif _MATCH_STRATEGY == "regex":
            pattern = re.compile(f"{re.escape(control_text)}", flags=re.IGNORECASE)
            return 100 if re.search(pattern, control_content) else 0
        else:
            raise ValueError(f"Unknown match strategy: {_MATCH_STRATEGY}")

    def find_matching_controller(
        self, filtered_annotation_dict: Dict[int, UIAWrapper], control_text: str
    ) -> Tuple[str, UIAWrapper]:
        """ "
        Select the best matched controller.
        :param filtered_annotation_dict: The filtered annotation dictionary.
        :param control_text: The text content of the control for additional context.
        :return: Tuple containing the key of the selected controller and the control object.s
        """
        control_selected = None
        controller_key = None
        highest_score = 0

        # Iterate through the filtered annotation dictionary to find the best match
        for key, control in filtered_annotation_dict.items():
            # Calculate the matching score using the match function
            score = self._calculate_match_score(control, control_text)

            # Update the selected control if the score is higher
            if score > highest_score:
                highest_score = score
                controller_key = key
                control_selected = control

        return controller_key, control_selected
