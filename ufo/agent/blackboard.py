# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.


from typing import Dict, List, Union

from ufo.agent.basic import Memory, MemoryItem


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
        :param data: The data to be added.
        """
        self._data.add_memory_item(data)

    def add_image(
        self, image: Union[MemoryItem, Dict[str, str]], from_path: bool = True
    ) -> None:
        """
        Add the image to the blackboard.
        :param image: The image or the path to the image to be added.
        :param from_path: Whether the image is from the path.
        """
        self.screenshots.add_memory_item(image)

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
        pass

    def screenshots_to_prompt(self) -> List[str]:
        """
        Convert the images to a prompt.
        :return: The prompt.
        """
        pass

    def blackboard_to_prompt(self) -> List[str]:
        """
        Convert the blackboard to a prompt.
        :return: The prompt.
        """
        pass
