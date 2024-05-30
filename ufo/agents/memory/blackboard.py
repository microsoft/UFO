# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import json
import os
from dataclasses import dataclass
from typing import Dict, List, Optional, Union

from ufo.agents.memory.memory import Memory, MemoryItem
from ufo.automator.ui_control.screenshot import PhotographerFacade


@dataclass
class ImageMemoryItemNames:
    """
    The variables for the image memory item.
    """

    METADATA: str = "metadata"
    IMAGE_PATH: str = "image_path"
    IMAGE_STR: str = "image_str"


@dataclass
class ImageMemoryItem(MemoryItem):
    """
    The class for the image memory item.
    """

    _memory_attributes = list(ImageMemoryItemNames.__annotations__.keys())


class Blackboard:
    """
    Class for the blackboard, which stores the data and images which are visible to all the agents.
    """

    def __init__(self) -> None:
        """
        Initialize the blackboard.
        """
        self._questions: Memory = Memory()
        self._requests: Memory = Memory()
        self._trajectories: Memory = Memory()
        self._screenshots: Memory = Memory()

    @property
    def questions(self) -> Memory:
        """
        Get the data from the blackboard.
        :return: The questions from the blackboard.
        """
        return self._questions

    @property
    def requests(self) -> Memory:
        """
        Get the data from the blackboard.
        :return: The requests from the blackboard.
        """
        return self._requests

    @property
    def trajectories(self) -> Memory:
        """
        Get the data from the blackboard.
        :return: The trajectories from the blackboard.
        """
        return self._trajectories

    @property
    def screenshots(self) -> Memory:
        """
        Get the images from the blackboard.
        :return: The images from the blackboard.
        """
        return self._screenshots

    def add_data(
        self, data: Union[MemoryItem, Dict[str, str], str], memory: Memory
    ) -> None:
        """
        Add the data to the a memory in the blackboard.
        :param data: The data to be added. It can be a dictionary or a MemoryItem or a string.
        :param memory: The memory to add the data to.
        """

        if isinstance(data, dict):
            data_memory = MemoryItem()
            data_memory.set_values_from_dict(data)
            memory.add_memory_item(data_memory)
        elif isinstance(data, MemoryItem):
            memory.add_memory_item(data)
        elif isinstance(data, str):
            data_memory = MemoryItem()
            data_memory.set_values_from_dict({"text": data})
            memory.add_memory_item(data_memory)

    def add_questions(self, questions: Union[MemoryItem, Dict[str, str]]) -> None:
        """
        Add the data to the blackboard.
        :param questions: The data to be added. It can be a dictionary or a MemoryItem or a string.
        """

        self.add_data(questions, self.questions)

    def add_requests(self, requests: Union[MemoryItem, Dict[str, str]]) -> None:
        """
        Add the data to the blackboard.
        :param requests: The data to be added. It can be a dictionary or a MemoryItem or a string.
        """

        self.add_data(requests, self.requests)

    def add_trajectories(self, trajectories: Union[MemoryItem, Dict[str, str]]) -> None:
        """
        Add the data to the blackboard.
        :param trajectories: The data to be added. It can be a dictionary or a MemoryItem or a string.
        """

        self.add_data(trajectories, self.trajectories)

    def add_image(
        self,
        screenshot_path: str = "",
        metadata: Optional[Dict[str, str]] = None,
    ) -> None:
        """
        Add the image to the blackboard.
        :param screenshot_path: The path of the image.
        :param screenshot_str: The string of the image, optional.
        :param metadata: The metadata of the image.
        """

        if os.path.exists(screenshot_path):

            screenshot_str = PhotographerFacade().encode_image_from_path(
                screenshot_path
            )
        else:
            screenshot_str = ""

        image_memory_item = ImageMemoryItem()
        image_memory_item.set_values_from_dict(
            {
                ImageMemoryItemNames.METADATA: metadata.get(
                    ImageMemoryItemNames.METADATA
                ),
                ImageMemoryItemNames.IMAGE_PATH: screenshot_path,
                ImageMemoryItemNames.IMAGE_STR: screenshot_str,
            }
        )

        self.screenshots.add_memory_item(image_memory_item)

    def questions_to_json(self) -> str:
        """
        Convert the data to a dictionary.
        :return: The data in the dictionary format.
        """
        return self.questions.to_json()

    def requests_to_json(self) -> str:
        """
        Convert the data to a dictionary.
        :return: The data in the dictionary format.
        """
        return self.requests.to_json()

    def trajectories_to_json(self) -> str:
        """
        Convert the data to a dictionary.
        :return: The data in the dictionary format.
        """
        return self.trajectories.to_json()

    def screenshots_to_json(self) -> str:
        """
        Convert the images to a dictionary.
        :return: The images in the dictionary format.
        """
        return self.screenshots.to_json()

    def texts_to_prompt(self, memory: Memory, prefix: str) -> List[str]:
        """
        Convert the data to a prompt.
        :return: The prompt.
        """

        user_content = [
            {"type": "text", "text": f"{prefix}\n {json.dumps(memory.list_content)}"}
        ]

        return user_content

    def screenshots_to_prompt(self) -> List[str]:
        """
        Convert the images to a prompt.
        :return: The prompt.
        """

        user_content = []
        for screenshot_dict in self.screenshots.list_content:
            user_content.append(
                {
                    "type": "text",
                    "text": json.dumps(
                        screenshot_dict.get(ImageMemoryItemNames.METADATA, "")
                    ),
                }
            )
            user_content.append(
                {
                    "type": "image_url",
                    "image_url": {
                        "url": screenshot_dict.get(ImageMemoryItemNames.IMAGE_STR, "")
                    },
                }
            )

        return user_content

    def blackboard_to_prompt(self) -> List[str]:
        """
        Convert the blackboard to a prompt.
        :return: The prompt.
        """
        prefix = [
            {
                "type": "text",
                "text": "[Blackboard:]",
            }
        ]

        blackboard_prompt = (
            prefix
            + self.texts_to_prompt(self.questions, "[Questions & Answers:]")
            + self.texts_to_prompt(self.requests, "[Request History:]")
            + self.texts_to_prompt(self.trajectories, "[Step Trajectories:]")
            + self.screenshots_to_prompt()
        )

        return blackboard_prompt

    def is_empty(self) -> bool:
        """
        Check if the blackboard is empty.
        :return: True if the blackboard is empty, False otherwise.
        """
        return (
            self.questions.is_empty()
            and self.requests.is_empty()
            and self.trajectories.is_empty()
            and self.screenshots.is_empty()
        )

    def clear(self) -> None:
        """
        Clear the blackboard.
        """
        self.questions.clear()
        self.requests.clear()
        self.trajectories.clear()
        self.screenshots.clear()


if __name__ == "__main__":

    blackboard = Blackboard()
    blackboard.add_data({"key1": "value1", "key2": "value2"})
    print(blackboard.blackboard_to_prompt())
