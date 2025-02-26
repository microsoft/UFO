# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import json
import os
import re
import sys
from typing import Any, Dict, List, Optional

from PIL import Image

sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))

from ufo.automator.ui_control.screenshot import PhotographerFacade
from ufo.utils import print_with_color


class Trajectory:
    """
    A class to structure the trajectory data.
    """

    _response_file = "response.log"
    _evaluation_file = "evaluation.log"

    _screenshot_keys = [
        "CleanScreenshot",
        "AnnotatedScreenshot",
        "ConcatScreenshot",
        "SelectedControlScreenshot",
    ]

    _step_screenshot_key = "ScreenshotImages"

    def __init__(self, file_path: str) -> None:
        """
        :param file_path: The file path to the trajectory data.
        """
        self.file_path = file_path
        self._response_file_path = os.path.join(self.file_path, self._response_file)
        if not os.path.exists(self._response_file_path):
            raise ValueError(
                f"The response file '{self._response_file_path}' does not exist."
            )
        self._step_log = self._load_response_data()
        self._evaluation_log = self._load_evaluation_data()
        self._structured_data = self._load_all_data()

    def _load_response_data(self) -> List[Dict[str, Any]]:
        """
        Load the textual data from the file.
        :return: The textual data.
        """

        step_data = []

        with open(self.response_file_path, "r", encoding="utf-8") as file:
            textual_logs = file.readlines()

        for log in textual_logs:
            try:
                log = log.strip()
                step_log = json.loads(log)
                step_log[self._step_screenshot_key] = self._load_step_screenshots(
                    step_log
                )

            except json.JSONDecodeError:
                continue

            step_data.append(step_log)

        return step_data

    def _load_all_data(self) -> Dict[str, Any]:
        """
        Load all the data from the file.
        :return: The data.
        """
        data = {
            "StepLog": self._load_response_data(),
            "EvaluationLog": self._load_evaluation_data(),
            "RoundScreenshots": self.round_screenshots,
            "FinalScreenshotPath": self.final_screenshot_path,
            "FinalScreenshotImage": self.final_screenshot_image,
        }

        return data

    @staticmethod
    def load_screenshot(screenshot_path: str) -> Image.Image:
        """
        Load the screenshot from the file.
        :screenshot_path: The path to the screenshot, e.g. "screenshot.png".
        :return: The screenshot data.
        """
        if os.path.exists(screenshot_path):
            image = PhotographerFacade.load_image(screenshot_path)
        else:
            image = None
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
            if os.path.exists(screenshot_file_path):
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

        else:
            print_with_color(
                f"Warning: Evaluation log not found at {evaluation_log_path}.", "yellow"
            )
            evaluation_data = {}

        return evaluation_data

    def _load_round_screenshot(self, round_number: int) -> Optional[Image.Image]:
        """
        Load the screenshot for a specific round.
        :param round_number: The round number.
        :param key: The key to the screenshot.
        :return: The screenshot data.
        """

        round_screenshots = {}

        round_final_screenshot_path = os.path.join(
            self.file_path, f"action_round_{round_number}_final.png"
        )

        if os.path.exists(round_final_screenshot_path):
            round_final_screenshot = self.load_screenshot(round_final_screenshot_path)
        else:
            round_final_screenshot = None

        subtask_number = self.get_subtask(self.file_path, round_number)
        subtask_final_screenshot_paths = []
        subtask_final_screenshot_images = []

        for i in range(subtask_number):
            subtask_final_screenshot_path = os.path.join(
                self.file_path, f"action_round_{round_number}_sub_round_{i}_final.png"
            )
            subtask_final_screenshot_image = self.load_screenshot(
                subtask_final_screenshot_path
            )

            subtask_final_screenshot_paths.append(subtask_final_screenshot_path)
            subtask_final_screenshot_images.append(subtask_final_screenshot_image)

        round_screenshots["RoundFinalScreenshotPath"] = round_final_screenshot_path
        round_screenshots["RoundFinalScreenshot"] = round_final_screenshot
        round_screenshots["SubtaskFinalScreenshotPaths"] = (
            subtask_final_screenshot_paths
        )
        round_screenshots["SubtaskFinalScreenshotImages"] = (
            subtask_final_screenshot_images
        )

        return round_screenshots

    @property
    def round_screenshots(self) -> Dict[int, Dict[str, Any]]:
        """
        :return: The round screenshots.
        """

        round_screenshots = {}

        for round_number in range(self.round_number):
            round_screenshots[round_number] = self._load_round_screenshot(round_number)

        return round_screenshots

    @property
    def request(self) -> str:
        """
        :return: The request data.
        """
        if len(self.step_log) == 0:
            return None
        return self.step_log[0].get("Request")

    @classmethod
    def get_subtask(cls, folder_path: str, round_number: int) -> int:
        """
        Get the maximum subtask number for a specific round.

        :param folder_path: The folder path to scan for files.
        :param round_number: The round number to search for.
        :return: The maximum subtask number if found, otherwise -1.
        """
        if not os.path.isdir(folder_path):
            raise ValueError(
                f"The provided folder path '{folder_path}' does not exist or is not a directory."
            )

        # Define the regex pattern to match the file names
        pattern = re.compile(rf"action_round_{round_number}_sub_round_(\d+)_final\.png")
        max_subtask = -1  # Initialize to -1 to indicate no matches found

        # Iterate over files in the folder
        for file_name in os.listdir(folder_path):
            # Check if the file name matches the pattern
            match = pattern.match(file_name)
            if match:
                # Extract the value of x and update max_subtask
                subtask_number = int(match.group(1))
                max_subtask = max(max_subtask, subtask_number)

        return max_subtask + 1

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

    @property
    def final_screenshot_path(self) -> str:
        """
        :return: The path to the final screenshot.
        """
        file_name = "action_step_final.png"
        return os.path.join(self.file_path, file_name)

    @property
    def final_screenshot_image(self) -> Image.Image:
        """
        :return: The final screenshot image.
        """
        return self.load_screenshot(self.final_screenshot_path)

    @property
    def round_number(self) -> int:
        """
        :return: The total number of rounds.
        """

        round_numbers = [
            self.step_log[i].get("Round")
            for i in range(len(self.step_log))
            if isinstance(self.step_log[i].get("Round"), int)
        ]

        if len(round_numbers) == 0:
            return 0

        return max(round_numbers) + 1

    @property
    def step_number(self) -> int:
        """
        :return: The total number of steps.
        """
        return (
            max(
                [
                    self.step_log[i].get("Step")
                    for i in range(len(self.step_log))
                    if isinstance(self.step_log[i].get("Step"), int)
                ]
            )
            + 1
        )

    @property
    def structured_data(self) -> Dict[str, Any]:
        """
        :return: The structured data of the entire trajectory.
        """
        return self._structured_data

    def to_markdown(
        self,
        output_path: str,
        key_shown: List[str] = [
            "Request",
            "Subtask",
            "Thought",
            "Status",
            "Action",
            "ControlLabel",
            "ControlText",
            "error",
        ],
    ) -> None:
        """
        Save the structured data to a markdown file.
        :param output_path: The output path to save the markdown file.
        :param key_shown: The keys to show at each step.
        """
        with open(output_path, "w", encoding="utf-8") as file:
            file.write("# Trajectory Data\n\n")

            file.write("## Evaluation Results\n\n")
            for key, value in self.evaluation_log.items():
                file.write(f"- **{key}**: {value}\n")

            file.write("\n")

            for data in self.app_agent_log:
                step = data.get("Step")
                file.write(f"### Step {step}:\n")
                for key, value in data.items():
                    if key in key_shown:
                        file.write(f"- **{key}**: {value}\n")
                file.write("\n")

                annotated_screenshot_filename = os.path.basename(
                    data.get("AnnotatedScreenshot", "")
                )
                selected_control_screenshot_filename = os.path.basename(
                    data.get("SelectedControlScreenshot", "")
                )

                file.write(
                    f'<div style="display: flex; justify-content: center;">\n'
                    f'  <img src="{os.path.join("./", annotated_screenshot_filename)}" width="45%" />\n'
                    f'  <img src="{os.path.join("./", selected_control_screenshot_filename)}" width="45%" />\n'
                    f"</div>\n\n"
                )

        print_with_color(f"Markdown file saved to {output_path}.", "green")


if __name__ == "__main__":
    file_path = r"ufo/trajectory/data"
    trajectory = Trajectory(file_path)
    trajectory.to_markdown(file_path + "/output.md")
