import logging
import re
import time

from fuzzywuzzy import fuzz
from pywinauto import Desktop
from pywinauto.controls.uiawrapper import UIAWrapper

from instantiation.config.config import Config
from ufo.automator.puppeteer import ReceiverManager
from ufo.automator.ui_control.inspector import ControlInspectorFacade

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
        super().__init__()
        # FIX: 私有属性修改
        self.app_window = None
        self.app_root_name = app_object.app_root_name
        self.app_name = app_object.description.lower()
        self.win_app = app_object.win_app
        self._receive_factory = ReceiverManager._receiver_factory_registry["COM"][
            "factory"
        ]
        self.win_com_receiver = self._receive_factory.create_receiver(
            self.app_root_name, self.app_name
        )
        self._control_inspector = ControlInspectorFacade(_BACKEND)
        self._control_inspector = ControlInspectorFacade(_BACKEND)

        self._all_controls = None

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
        Closes the Windows environment.
        """
        try:
            com_object = self.win_com_receiver.get_object_from_process_name()
            com_object.Close()
            self.win_com_receiver.client.Quit()
            time.sleep(1)
        except Exception as e:
            logging.exception(f"Failed to close the application: {e}")
            raise

    def find_matching_window(self, doc_name: str) -> object:
        """
        Finds a matching window based on the process name and the configured matching strategy.
        :param doc_name: The document name associated with the application.
        :return: The matched window or None if no match is found.
        """
        desktop = Desktop(backend=_BACKEND)
        windows_list = desktop.windows()
        # windows_list = self._control_inspector.get_desktop_windows()
        for window in windows_list:
            window_title = window.element_info.name.lower()
            if self._match_window_name(window_title, doc_name):
                # Cache all controls for the window
                self._all_controls = window.children()
                self.app_window = window
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

    def find_matching_controller(self, control_label: str, control_text: str) -> object:
        """
        Finds a matching controller based on the control label and control text.
        :param control_label: The label of the control to identify it.
        :param control_text: The text content of the control for additional context.
        :return: The matched controller object or None if no match is found.
        """
        # self._all_controls = self._control_inspector.find_control_elements_in_descendants(self.win_com_receiver)
        try:
            # Retrieve controls to match against
            for control in self._all_controls:
                if self._match_controller(control, control_label, control_text):
                    return control
        except Exception as e:
            # Log the error or handle it as needed
            logging.exception(f"Error finding matching controller: {e}")
            # Assume log_error is a method for logging errors
            raise
        # No match found
        return None

    def _match_controller(
        self, control_to_match: UIAWrapper, control_label: str, control_text: str
    ) -> bool:
        """
        Matches the controller based on the strategy specified in the config file.
        :param control_to_match: The control object to match against.
        :param control_label: The label of the control to identify it.
        :param control_text: The text content of the control for additional context.
        :return: True if a match is found based on the strategy; False otherwise.
        """
        control_name = (
            control_to_match.class_name() if control_to_match.class_name() else ""
        )  # 默认空字符串
        control_content = (
            control_to_match.window_text() if control_to_match.window_text() else ""
        )  # 默认空字符串

        if _MATCH_STRATEGY == "contains":
            return control_label in control_name and control_text in control_content
        elif _MATCH_STRATEGY == "fuzzy":
            similarity_label = fuzz.partial_ratio(control_name, control_label)
            similarity_text = fuzz.partial_ratio(control_content, control_text)
            return similarity_label >= 70 and similarity_text >= 70
        elif _MATCH_STRATEGY == "regex":
            combined_name_1 = f"{control_label}.*{control_text}"
            combined_name_2 = f"{control_text}.*{control_label}"
            pattern_1 = re.compile(combined_name_1, flags=re.IGNORECASE)
            pattern_2 = re.compile(combined_name_2, flags=re.IGNORECASE)

            return (re.search(pattern_1, control_name) is not None) or (
                re.search(pattern_2, control_name) is not None
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
