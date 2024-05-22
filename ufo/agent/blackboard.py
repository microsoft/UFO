# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import sys

sys.path.append("../ufo")

import json
import os
from dataclasses import dataclass
from typing import Dict, List, Optional, Union

from ufo.agent.basic import Memory, MemoryItem
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
        self._data: Memory = Memory()
        self._screenshots: Memory = Memory()

    @property
    def data(self) -> Memory:
        """
        Get the data from the blackboard.
        :return: The data from the blackboard.
        """
        return self._data

    @property
    def screenshots(self) -> Memory:
        """
        Get the images from the blackboard.
        :return: The images from the blackboard.
        """
        return self._screenshots

    def add_data(self, data: Union[MemoryItem, Dict[str, str]]) -> None:
        """
        Add the data to the blackboard.
        :param data: The data to be added. It can be a dictionary or a MemoryItem.
        """

        if isinstance(data, dict):
            data_memory = MemoryItem()
            data_memory.set_values_from_dict(data)
            self._data.add_memory_item(data_memory)
        elif isinstance(data, MemoryItem):
            self._data.add_memory_item(data)

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

    def data_to_json(self) -> str:
        """
        Convert the data to a dictionary.
        :return: The data in the dictionary format.
        """
        return self._data.to_json()

    def screenshots_to_json(self) -> str:
        """
        Convert the images to a dictionary.
        :return: The images in the dictionary format.
        """
        return self.screenshots.to_json()

    def data_to_prompt(self) -> List[str]:
        """
        Convert the data to a prompt.
        :return: The prompt.
        """
        user_content = []
        for data_dict in self.data.list_content:
            user_content.append(
                {
                    "type": "text",
                    "text": json.dumps(data_dict),
                }
            )

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

        return prefix + self.data_to_prompt() + self.screenshots_to_prompt()

    def is_empty(self) -> bool:
        """
        Check if the blackboard is empty.
        :return: True if the blackboard is empty, False otherwise.
        """
        return self._data.is_empty() and self._screenshots.is_empty()

    def clear(self) -> None:
        """
        Clear the blackboard.
        """
        self._data.clear()
        self._screenshots.clear()


if __name__ == "__main__":

    blackboard = Blackboard()
    blackboard.add_data({"key1": "value1", "key2": "value2"})
    print(blackboard.blackboard_to_prompt())
