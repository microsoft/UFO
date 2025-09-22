"""
Constellation serialization and deserialization utilities.
Handles conversion between TaskConstellation objects and JSON/dict formats.
"""

import json
from datetime import datetime
from typing import Dict, Any, Optional

from ..task_constellation import TaskConstellation, ConstellationState
from ..task_star import TaskStar
from ..task_star_line import TaskStarLine


class ConstellationSerializer:
    """
    Handles serialization and deserialization of TaskConstellation objects.
    Responsible for converting between constellation objects and JSON/dict formats.
    """

    @staticmethod
    def to_dict(constellation: TaskConstellation) -> Dict[str, Any]:
        """
        Convert a constellation to a dictionary representation.

        :param constellation: TaskConstellation to serialize
        :return: Dictionary representation of the constellation
        """
        return {
            "constellation_id": constellation.constellation_id,
            "name": constellation.name,
            "state": constellation.state.value,
            "tasks": {
                task_id: task.to_dict() for task_id, task in constellation.tasks.items()
            },
            "dependencies": {
                dep_id: dep.to_dict()
                for dep_id, dep in constellation.dependencies.items()
            },
            "metadata": constellation.metadata,
            "llm_source": constellation.llm_source,
            "created_at": constellation.created_at.isoformat(),
            "updated_at": constellation.updated_at.isoformat(),
            "execution_start_time": (
                constellation.execution_start_time.isoformat()
                if constellation.execution_start_time
                else None
            ),
            "execution_end_time": (
                constellation.execution_end_time.isoformat()
                if constellation.execution_end_time
                else None
            ),
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> TaskConstellation:
        """
        Create a TaskConstellation from a dictionary representation.

        :param data: Dictionary representation
        :return: TaskConstellation instance
        """
        constellation = TaskConstellation(
            constellation_id=data.get("constellation_id"),
            name=data.get("name"),
        )

        # Use the internal restore method to set all state
        constellation._restore_from_data(data)

        return constellation

    @staticmethod
    def to_json(constellation: TaskConstellation, indent: Optional[int] = 2) -> str:
        """
        Convert a constellation to JSON string.

        :param constellation: TaskConstellation to serialize
        :param indent: JSON indentation level
        :return: JSON string representation
        """
        data = ConstellationSerializer.to_dict(constellation)
        return json.dumps(data, indent=indent, default=str)

    @staticmethod
    def from_json(json_str: str) -> TaskConstellation:
        """
        Create a TaskConstellation from JSON string.

        :param json_str: JSON string representation
        :return: TaskConstellation instance
        """
        data = json.loads(json_str)
        return ConstellationSerializer.from_dict(data)

    @staticmethod
    def normalize_json_data(data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize JSON data to ensure consistent format.
        Handles various input formats and converts them to standard format.

        :param data: Raw dictionary data
        :return: Normalized dictionary data
        """
        normalized = data.copy()

        # Handle dependencies as list (convert to dict format)
        if "dependencies" in normalized and isinstance(
            normalized["dependencies"], list
        ):
            deps_dict = {}
            for i, dep in enumerate(normalized["dependencies"]):
                dep_id = f"dep_{i}"
                # Convert from test format to TaskStarLine format
                deps_dict[dep_id] = {
                    "line_id": dep_id,
                    "from_task_id": dep.get("predecessor_id"),
                    "to_task_id": dep.get("successor_id"),
                    "dependency_type": dep.get("dependency_type", "unconditional"),
                    "condition_description": dep.get("condition_description"),
                }
            normalized["dependencies"] = deps_dict

        return normalized
