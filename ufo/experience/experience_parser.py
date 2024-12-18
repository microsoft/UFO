# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from typing import Any, Dict, List
from collections import defaultdict

from ufo.trajectory import parser
from ufo.automator.ui_control.screenshot import PhotographerFacade


class ExperienceLogLoader:
    """
    Loading the logs from previous runs.
    """

    _subtask_key = "Subtask"
    _application_key = "Application"
    _image_url_key = "ScreenshotURLs"

    def __init__(self, log_path: str):
        """
        Initialize the LogLoader.
        :param log_path: The path of the log file.
        """
        self._log_path = log_path
        trajectory = parser.Trajectory(log_path)
        self._subtask_partition = self.group_by_subtask(trajectory.app_agent_log)

    @classmethod
    def group_by_subtask(
        cls, step_log: List[Dict[str, Any]]
    ) -> List[List[Dict[str, Any]]]:
        """
        Group the logs by the value of the "Subtask" field.
        :param step_log: The step log.
        :return: The grouped logs.
        """

        grouped = defaultdict(list)
        for log in step_log:
            # Group by the value of the "Subtask" field
            image_urls = {}
            for key in parser.Trajectory._screenshot_keys:
                image_urls[key] = PhotographerFacade.encode_image(
                    log.get(parser.Trajectory._step_screenshot_key, {}).get(key)
                )
            log[cls._image_url_key] = image_urls
            subtask = log.get(cls._subtask_key)
            grouped[subtask].append(log)

        # Build the desired output structure
        result = [
            {
                "subtask_index": index,
                "subtask": subtask,
                "logs": logs,
                "application": logs[0][cls._application_key],
            }
            for index, (subtask, logs) in enumerate(grouped.items())
        ]

        return result

    @property
    def subtask_partition(self) -> List[Dict[str, Any]]:
        """
        :return: The subtask partition.
        """
        return self._subtask_partition

    @property
    def log_path(self) -> str:
        """
        :return: The log path.
        """
        return self._log_path
