# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import json
import os
from typing import Any, Dict, List, Optional

from PIL import Image

from ufo.automator.ui_control.screenshot import PhotographerFacade


class Trajectory:
    """
    A class to structure the trajectory data.
    """

    _response_file = "response.json"
    _evaluation_file = "evaluation.json"

    _screenshot_keys = [
        "CleanScreenshot",
        "AnnotatedScreenshot",
        "ConcatScreenshot",
        "SelectedControlScreenshot",
    ]

    def __init__(self, file_path: str) -> None:
        """
        :param file_path: The file path to the trajectory data.
        """
        self.file_path = file_path
        self._response_file_path = os.path.join(self.file_path, self._response_file)
        self._step_log = self._load_response_data()
        self._evaluation_log = self._load_evaluation_data()

    def _load_response_data(self) -> List[Dict[str, Any]]:
        """
        Load the textual data from the file.
        :return: The textual data.
        """

        step_data = []

        with open(self.response_file_path, "r", encoding="utf-8") as file:
            textual_logs = file.readlines()

        for log in enumerate(textual_logs):
            step_log = json.loads(log)
            step_log["ScreenshotImages"] = self._load_step_screenshots(step_log)

            step_data.append(step_log)

        return step_data

    @staticmethod
    def load_screenshot(screenshot_path: str) -> Image.Image:
        """
        Load the screenshot from the file.
        :screenshot_path: The path to the screenshot, e.g. "screenshot.png".
        :return: The screenshot data.
        """
        image = PhotographerFacade.load_image(screenshot_path)
        return image

    def _load_single_screenshot(
        self, step_log: Dict[str, Any], key: str
    ) -> Optional[Image.Image]:
        """
        Load a single screenshot from the file.
        :param step_log: The step log.
        :param key: The key to the screenshot.
        :return: The screenshot data.
        """
        screenshot_log_path = step_log.get(key)

        if screenshot_log_path is not None:
            screenshot_file_name = os.path.basename(screenshot_log_path)
            screenshot_file_path = os.path.join(self.file_path, screenshot_file_name)
            screenshot = self.load_screenshot(screenshot_file_path)
            return screenshot

        return None

    def _load_step_screenshots(
        self, step_log: Dict[str, Any]
    ) -> Dict[str, Image.Image]:
        """
        Load the screenshot data from the file.
        :param step_log: The step log.
        :return: The screenshot data.
        """
        screenshot_data = {
            key: self._load_single_screenshot(step_log, key)
            for key in self._screenshot_keys
        }

        return screenshot_data

    def _load_evaluation_data(self) -> Dict[str, Any]:
        """
        Load the evaluation data from the file.
        :return: The evaluation data.
        """
        evaluation_log_path = os.path.join(self.file_path, self._evaluation_file)

        if os.path.exists(evaluation_log_path):
            with open(evaluation_log_path, "r", encoding="utf-8") as file:

                try:
                    evaluation_data = json.load(file)
                except:
                    evaluation_data = {}

        return evaluation_data

    @property
    def response_file_path(self) -> str:
        """
        :return: The file path to the response file.
        """
        return self._response_file_path

    @property
    def step_log(self) -> List[Dict[str, Any]]:
        """
        :return: The step log.
        """
        return self._step_log

    @property
    def evaluation_log(self) -> Dict[str, Any]:
        """
        :return: The evaluation log.
        """
        return self._evaluation_log

    @property
    def host_agent_log(self) -> Dict[str, Any]:
        """
        :return: The host agent log.
        """

        host_agent_log = []

        for step in self.step_log:
            if step.get("Agent") == "HostAgent":
                host_agent_log.append(step)

        return host_agent_log

    @property
    def app_agent_log(self) -> Dict[str, Any]:
        """
        :return: The app agent log.
        """

        app_agent_log = []

        for step in self.step_log:
            if step.get("Agent") == "AppAgent":
                app_agent_log.append(step)

        return app_agent_log
