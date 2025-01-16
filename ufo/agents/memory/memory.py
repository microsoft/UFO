# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class MemoryItem:
    """
    This data class represents a memory item of an agent at one step.
    """

    _memory_attributes = []

    def to_dict(self) -> Dict[str, str]:
        """
        Convert the MemoryItem to a dictionary.
        :return: The dictionary.
        """

        return {
            key: value
            for key, value in self.__dict__.items()
            if key in self._memory_attributes
        }

    def from_dict(self, data: Dict[str, str]) -> None:
        """
        Convert the dictionary to a MemoryItem.
        :param data: The dictionary.
        """
        for key, value in data.items():
            self.set_value(key, value)

    def to_json(self) -> str:
        """
        Convert the memory item to a JSON string.
        :return: The JSON string.
        """
        return json.dumps(self.to_dict())

    def filter(self, keys: List[str] = []) -> None:
        """
        Fetch the memory item.
        :param keys: The keys to fetch.
        :return: The filtered memory item.
        """

        return {key: value for key, value in self.to_dict().items() if key in keys}

    def set_value(self, key: str, value: str) -> None:
        """
        Add a field to the memory item.
        :param key: The key of the field.
        :param value: The value of the field.
        """
        setattr(self, key, value)

        if key not in self._memory_attributes:
            self._memory_attributes.append(key)

    def add_values_from_dict(self, values: Dict[str, Any]) -> None:
        """
        Add fields to the memory item.
        :param values: The values of the fields.
        """
        for key, value in values.items():
            self.set_value(key, value)

    def get_value(self, key: str) -> Optional[str]:
        """
        Get the value of the field.
        :param key: The key of the field.
        :return: The value of the field.
        """

        return getattr(self, key, None)

    def get_values(self, keys: List[str]) -> dict:
        """
        Get the values of the fields.
        :param keys: The keys of the fields.
        :return: The values of the fields.
        """
        return {key: self.get_value(key) for key in keys}

    @property
    def attributes(self) -> List[str]:
        """
        Get the attributes of the memory item.
        :return: The attributes.
        """
        return self._memory_attributes


@dataclass
class Memory:
    """
    This data class represents a memory of an agent.
    """

    _content: List[MemoryItem] = field(default_factory=list)

    def load(self, content: List[MemoryItem]) -> None:
        """
        Load the data from the memory.
        :param content: The content to load.
        """
        self._content = content

    def filter_memory_from_steps(self, steps: List[int]) -> List[Dict[str, str]]:
        """
        Filter the memory from the steps.
        :param steps: The steps to filter.
        :return: The filtered memory.
        """
        return [item.to_dict() for item in self._content if item.step in steps]

    def filter_memory_from_keys(self, keys: List[str]) -> List[Dict[str, str]]:
        """
        Filter the memory from the keys. If an item does not have the key, the key will be ignored.
        :param keys: The keys to filter.
        :return: The filtered memory.
        """
        return [item.filter(keys) for item in self._content]

    def add_memory_item(self, memory_item: MemoryItem) -> None:
        """
        Add a memory item to the memory.
        :param memory_item: The memory item to add.
        """
        self._content.append(memory_item)

    def clear(self) -> None:
        """
        Clear the memory.
        """
        self._content = []

    @property
    def length(self) -> int:
        """
        Get the length of the memory.
        :return: The length of the memory.
        """
        return len(self._content)

    def delete_memory_item(self, step: int) -> None:
        """
        Delete a memory item from the memory.
        :param step: The step of the memory item to delete.
        """
        self._content = [item for item in self._content if item.step != step]

    def to_json(self) -> str:
        """
        Convert the memory to a JSON string.
        :return: The JSON string.
        """

        return json.dumps(
            [item.to_dict() for item in self._content if item is not None]
        )

    def to_list_of_dicts(self) -> List[Dict[str, str]]:
        """
        Convert the memory to a list of dictionaries.
        :return: The list of dictionaries.
        """
        return [item.to_dict() for item in self._content]

    def from_list_of_dicts(self, data: List[Dict[str, str]]) -> None:
        """
        Convert the list of dictionaries to the memory.
        :param data: The list of dictionaries.
        """
        self._content = []
        for item in data:
            memory_item = MemoryItem()
            memory_item.from_dict(item)
            self._content.append(memory_item)

    def get_latest_item(self) -> MemoryItem:
        """
        Get the latest memory item.
        :return: The latest memory item.
        """
        if self.length == 0:
            return None
        return self._content[-1]

    @property
    def content(self) -> List[MemoryItem]:
        """
        Get the content of the memory.
        :return: The content of the memory.
        """
        return self._content

    @property
    def list_content(self) -> List[Dict[str, str]]:
        """
        List the content of the memory.
        :return: The content of the memory.
        """
        return [item.to_dict() for item in self._content]

    def is_empty(self) -> bool:
        """
        Check if the memory is empty.
        :return: The boolean value indicating if the memory is empty.
        """
        return self.length == 0
