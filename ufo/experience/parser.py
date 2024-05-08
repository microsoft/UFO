# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import json
import os
import re

from ufo.automator.ui_control.screenshot import PhotographerFacade
from ufo.utils import print_with_color


class ExperienceLogLoader:
    """
    Loading the logs from previous runs.
    """

    def __init__(self, log_path: str):
        """
        Initialize the LogLoader.
        :param log_path: The path of the log file.
        """
        self.log_path = log_path
        self.response = self.load_response_log()
        self.max_stepnum = self.find_max_number_in_filenames(log_path)
        self.request_partition = self.get_request_partition()
        self.screenshots = {}

        self.logs = []

    def load_response_log(self):
        """
        Load the response log.
        :return: The response log.
        """

        response = []
        response_log_path = os.path.join(self.log_path, "response.log")
        with open(response_log_path, "r", encoding="utf-8") as file:
            # Read the lines and split them into a list
            response_log = file.readlines()
        for response_string in response_log:
            try:
                response.append(json.loads(response_string))
            except json.JSONDecodeError:
                print_with_color(
                    f"Error loading response log: {response_string}", "yellow"
                )
        return response

    @staticmethod
    def find_max_number_in_filenames(log_path) -> int:
        """
        Find the maximum number in the filenames.
        :return: The maximum number in the filenames.
        """

        # Get the list of files in the folder
        files = os.listdir(log_path)

        # Initialize an empty list to store extracted numbers
        numbers = []

        # Iterate through each file
        for file in files:
            # Extract the number from the filename
            number = ExperienceLogLoader.extract_action_step_count(file)
            if number is not None:
                # Append the extracted number to the list
                numbers.append(number)

        if numbers:
            # Return the maximum number if numbers list is not empty
            return max(numbers)
        else:
            # Return None if no numbers are found in filenames
            return None

    def load_screenshot(self, stepnum: int = 0, version: str = "") -> str:
        """
        Load the screenshot.
        :param stepnum: The step number of the screenshot.
        :param version: The version of the screenshot.
        :return: The screenshot.
        """

        # create version tag
        if version:
            version_tag = "_" + version
        else:
            version_tag = ""

        # Get the filename of the screenshot
        filename = "action_step{stepnum}{version}.png".format(
            stepnum=stepnum, version=version_tag
        )
        screenshot_path = os.path.join(self.log_path, filename)

        # Check if the screenshot exists
        if os.path.exists(screenshot_path):
            image_url = PhotographerFacade.encode_image_from_path(screenshot_path)
        else:
            image_url = None

        return image_url

    def create_logs(self) -> list:
        """
        Create the response log.
        :return: The response log.
        """
        self.logs = []
        for partition in self.request_partition:
            request = self.response[partition[0]]["Request"]
            nround = self.response[partition[0]]["Round"]
            partitioned_logs = {
                "request": request,
                "round": nround,
                "step_num": len(partition),
                **{
                    "step_%s"
                    % local_step: {
                        "response": self.response[step],
                        "is_first_action": local_step == 1,
                        "screenshot": {
                            version: self.load_screenshot(
                                step, "" if version == "raw" else version
                            )
                            for version in ["raw", "selected_controls"]
                        },
                    }
                    for local_step, step in enumerate(partition)
                },
                "application": list(
                    {self.response[step]["Application"] for step in partition}
                ),
            }
            self.logs.append(partitioned_logs)
        return self.logs

    def get_request_partition(self) -> list:
        """
        Partition the logs.
        :return: The partitioned logs.
        """
        request_partition = []
        current_round = 0
        current_partition = []

        for step in range(self.max_stepnum):
            nround = self.response[step]["Round"]

            if nround != current_round:
                if current_partition:
                    request_partition.append(current_partition)
                current_partition = [step]
                current_round = nround
            else:
                current_partition.append(step)

        if current_partition:
            request_partition.append(current_partition)

        return request_partition

    @staticmethod
    def get_user_request(log_partition: dict) -> str:
        """
        Get the user request.
        :param log_partition: The log partition.
        :return: The user request.
        """
        return log_partition.get("request")

    @staticmethod
    def get_app_list(log_partition: dict) -> list:
        """
        Get the user request.
        :param log_partition: The log partition.
        :return: The application list.
        """
        return log_partition.get("application")

    @staticmethod
    def extract_action_step_count(filename: str) -> int:
        """
        Extract the action step count from the filename.
        :param filename: The filename.
        :return: The number extracted from the filename.
        """

        # Define a regular expression pattern to extract numbers
        pattern = r"action_step(\d+)\.png"
        # Use re.search to find the matching pattern in the filename
        match = re.search(pattern, filename)
        if match:
            # Return the extracted number as an integer
            return int(match.group(1))
        else:
            # Return None if no match is found
            return None
