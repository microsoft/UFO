# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Constellation Parser for creating and updating TaskConstellation from various sources.

This module handles the parsing and creation logic for TaskConstellation objects,
separating this responsibility from orchestration logic.
"""

import json
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from .enums import TaskPriority
from .task_constellation import TaskConstellation
from .task_star import TaskStar
from .task_star_line import TaskStarLine
from .constellation_serializer import ConstellationSerializer
from .constellation_updater import ConstellationUpdater


class ConstellationParser:
    """
    Responsible for parsing and creating TaskConstellation objects from various sources.

    This class handles:
    - Creating constellations from LLM output
    - Parsing from JSON/YAML/other formats
    - Updating existing constellations
    - Validating constellation structure
    """

    def __init__(self, enable_logging: bool = True):
        """
        Initialize the ConstellationParser.

        :param enable_logging: Whether to enable logging
        """
        self._logger = logging.getLogger(__name__) if enable_logging else None
        self._updater = ConstellationUpdater(self._logger)

    async def create_from_llm(
        self,
        llm_output: str,
        constellation_name: Optional[str] = None,
    ) -> TaskConstellation:
        """
        Create a TaskConstellation from LLM output.

        :param llm_output: Raw LLM output describing tasks and dependencies
        :param constellation_name: Optional name for the constellation
        :return: TaskConstellation instance
        """
        if self._logger:
            self._logger.info(
                f"Creating constellation from LLM output: {constellation_name}"
            )

        # Create empty constellation
        constellation = TaskConstellation(
            name=constellation_name or "LLM Generated Constellation"
        )

        # Simple parsing logic - in a real implementation this would be more sophisticated
        lines = llm_output.strip().split("\n")
        current_task = None
        task_counter = 1

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Look for task definitions
            if line.lower().startswith(("task", "step")):
                # Extract task name and description
                if ":" in line:
                    task_name = line.split(":", 1)[1].strip()
                else:
                    task_name = line.strip()

                task_id = f"task_{task_counter}"
                current_task = TaskStar(task_id=task_id, description=task_name)
                constellation.add_task(current_task)
                task_counter += 1

            elif line.lower().startswith("description") and current_task:
                # Update task description
                if ":" in line:
                    description = line.split(":", 1)[1].strip()
                    current_task.description = description

            elif line.lower().startswith("dependencies") and current_task:
                # Parse dependencies - simplified logic
                if ":" in line:
                    deps_text = line.split(":", 1)[1].strip()
                    # Look for task references
                    for i in range(1, task_counter):
                        prev_task_id = f"task_{i}"
                        if (
                            prev_task_id in constellation.tasks
                            and prev_task_id != current_task.task_id
                        ):
                            # Create dependency
                            dep = TaskStarLine.create_unconditional(
                                prev_task_id,
                                current_task.task_id,
                                f"LLM dependency: {prev_task_id} -> {current_task.task_id}",
                            )
                            constellation.add_dependency(dep)
                            break

        if self._logger:
            self._logger.info(
                f"Created constellation '{constellation.name}' with {constellation.task_count} tasks "
                f"and {constellation.dependency_count} dependencies"
            )

        return constellation

    def create_from_json(
        self,
        json_data: str,
        constellation_name: Optional[str] = None,
    ) -> TaskConstellation:
        """
        Create a TaskConstellation from JSON data.

        :param json_data: JSON string representing constellation
        :param constellation_name: Optional name override for the constellation
        :return: TaskConstellation instance
        """
        if self._logger:
            self._logger.info(f"Creating constellation from JSON: {constellation_name}")

        try:
            # Parse JSON data
            data = json.loads(json_data) if isinstance(json_data, str) else json_data

            # Normalize the data format
            normalized_data = ConstellationSerializer.normalize_json_data(data)

            # Create constellation using the serializer
            constellation = ConstellationSerializer.from_dict(normalized_data)

        except (json.JSONDecodeError, ValueError) as e:
            if self._logger:
                self._logger.error(f"Failed to parse JSON data: {e}")
            raise ValueError(f"Invalid JSON data: {e}")

        # Override name if provided
        if constellation_name:
            constellation.name = constellation_name

        if self._logger:
            self._logger.info(
                f"Created constellation '{constellation.name}' with {constellation.task_count} tasks "
                f"and {constellation.dependency_count} dependencies"
            )

        return constellation

    def create_simple_sequential(
        self,
        task_descriptions: List[str],
        constellation_name: str = "Sequential Constellation",
    ) -> TaskConstellation:
        """
        Create a simple sequential constellation from task descriptions.

        :param task_descriptions: List of task descriptions
        :param constellation_name: Name for the constellation
        :return: TaskConstellation instance
        """
        if self._logger:
            self._logger.info(
                f"Creating sequential constellation '{constellation_name}' with {len(task_descriptions)} tasks"
            )

        constellation = TaskConstellation(name=constellation_name)

        # Create tasks
        tasks = []
        for i, description in enumerate(task_descriptions):
            task = TaskStar(
                task_id=f"task_{i+1}",
                description=description,
                priority=TaskPriority.MEDIUM,
            )
            constellation.add_task(task)
            tasks.append(task)

        # Add sequential dependencies
        if len(tasks) > 1:
            for i in range(len(tasks) - 1):
                dep = TaskStarLine.create_unconditional(
                    tasks[i].task_id,
                    tasks[i + 1].task_id,
                    f"Sequential dependency: {tasks[i].task_id} -> {tasks[i + 1].task_id}",
                )
                constellation.add_dependency(dep)

        return constellation

    def create_simple_parallel(
        self,
        task_descriptions: List[str],
        constellation_name: str = "Parallel Constellation",
    ) -> TaskConstellation:
        """
        Create a simple parallel constellation from task descriptions.

        :param task_descriptions: List of task descriptions
        :param constellation_name: Name for the constellation
        :return: TaskConstellation instance
        """
        if self._logger:
            self._logger.info(
                f"Creating parallel constellation '{constellation_name}' with {len(task_descriptions)} tasks"
            )

        constellation = TaskConstellation(name=constellation_name)

        # Create tasks without dependencies (parallel execution)
        for i, description in enumerate(task_descriptions):
            task = TaskStar(
                task_id=f"task_{i+1}",
                description=description,
                priority=TaskPriority.MEDIUM,
            )
            constellation.add_task(task)

        return constellation

    def update_from_llm(
        self,
        constellation: TaskConstellation,
        modification_request: str,
    ) -> TaskConstellation:
        """
        Update an existing constellation based on LLM modification request.

        :param constellation: Existing TaskConstellation
        :param modification_request: LLM request for modifications
        :return: Updated TaskConstellation (may be a new instance)
        """
        if self._logger:
            self._logger.info(
                f"Updating constellation '{constellation.name}' with LLM request"
            )

        # Use the updater to handle the LLM-based updates
        self._updater.update_from_llm_output(constellation, modification_request)

        return constellation

    def add_task_to_constellation(
        self,
        constellation: TaskConstellation,
        task: TaskStar,
        dependencies: Optional[List[str]] = None,
    ) -> bool:
        """
        Add a task to an existing constellation.

        :param constellation: Target constellation
        :param task: TaskStar to add
        :param dependencies: Optional list of task IDs that this task depends on
        :return: True if task was added successfully
        """
        try:
            # Add the task
            constellation.add_task(task)

            # Add dependencies if specified using the updater
            if dependencies:
                dep_specs = []
                for dep_task_id in dependencies:
                    if dep_task_id in constellation.tasks:
                        dep_specs.append(
                            {
                                "from_task_id": dep_task_id,
                                "to_task_id": task.task_id,
                                "description": f"Dependency: {dep_task_id} -> {task.task_id}",
                            }
                        )

                if dep_specs:
                    self._updater.add_dependencies(constellation, dep_specs)

            if self._logger:
                self._logger.info(
                    f"Added task '{task.task_id}' to constellation '{constellation.name}'"
                )

            return True

        except Exception as e:
            if self._logger:
                self._logger.error(f"Failed to add task '{task.task_id}': {e}")
            return False

    def remove_task_from_constellation(
        self,
        constellation: TaskConstellation,
        task_id: str,
    ) -> bool:
        """
        Remove a task from a constellation.

        :param constellation: Target constellation
        :param task_id: ID of task to remove
        :return: True if task was removed successfully
        """
        try:
            if task_id in constellation.tasks:
                # Use the updater to handle removal with dependencies
                self._updater.remove_tasks(
                    constellation, [task_id], remove_dependencies=True
                )
                if self._logger:
                    self._logger.info(
                        f"Removed task '{task_id}' from constellation '{constellation.name}'"
                    )
                return True
            return False

        except Exception as e:
            if self._logger:
                self._logger.error(f"Failed to remove task '{task_id}': {e}")
            return False

    def validate_constellation(
        self, constellation: TaskConstellation
    ) -> tuple[bool, List[str]]:
        """
        Validate a constellation structure.

        :param constellation: TaskConstellation to validate
        :return: Tuple of (is_valid, list_of_errors)
        """
        errors = []

        # Check if constellation has tasks
        if constellation.task_count == 0:
            errors.append("Constellation has no tasks")

        # Validate DAG structure
        is_dag_valid, dag_errors = constellation.validate_dag()
        if not is_dag_valid:
            errors.extend(dag_errors)

        is_valid = len(errors) == 0

        if self._logger:
            if is_valid:
                self._logger.info(f"Constellation '{constellation.name}' is valid")
            else:
                self._logger.warning(
                    f"Constellation '{constellation.name}' has {len(errors)} validation errors"
                )

        return is_valid, errors

    def export_constellation(
        self,
        constellation: TaskConstellation,
        format: str = "json",
    ) -> str:
        """
        Export constellation to various formats.

        :param constellation: TaskConstellation to export
        :param format: Export format ("json", "yaml", "llm")
        :return: Exported string representation
        """
        if format.lower() == "json":
            return ConstellationSerializer.to_json(constellation, indent=2)
        elif format.lower() == "llm":
            return constellation.to_llm_string()
        elif format.lower() == "yaml":
            # For YAML export, you would need PyYAML
            # For now, return JSON with a note
            return f"# YAML export not implemented, returning JSON:\n{ConstellationSerializer.to_json(constellation, indent=2)}"
        else:
            raise ValueError(f"Unsupported export format: {format}")

    def clone_constellation(
        self,
        constellation: TaskConstellation,
        new_name: Optional[str] = None,
    ) -> TaskConstellation:
        """
        Clone a constellation.

        :param constellation: Constellation to clone
        :param new_name: Optional new name for the cloned constellation
        :return: Cloned TaskConstellation
        """
        # Export to JSON and re-import to create a deep copy
        json_data = ConstellationSerializer.to_json(constellation)
        cloned = ConstellationSerializer.from_json(json_data)

        # Set new name
        if new_name:
            cloned.name = new_name
        else:
            cloned.name = f"{constellation.name} (Copy)"

        # Force new constellation ID
        cloned._constellation_id = f"constellation_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"

        if self._logger:
            self._logger.info(
                f"Cloned constellation '{constellation.name}' as '{cloned.name}'"
            )

        return cloned

    def merge_constellations(
        self,
        constellation1: TaskConstellation,
        constellation2: TaskConstellation,
        merged_name: Optional[str] = None,
    ) -> TaskConstellation:
        """
        Merge two constellations into a new one.

        :param constellation1: First constellation
        :param constellation2: Second constellation
        :param merged_name: Optional name for merged constellation
        :return: Merged TaskConstellation
        """
        if merged_name is None:
            merged_name = f"{constellation1.name} + {constellation2.name}"

        if self._logger:
            self._logger.info(
                f"Merging constellations '{constellation1.name}' and '{constellation2.name}' into '{merged_name}'"
            )

        merged = TaskConstellation(name=merged_name)

        # Add tasks from first constellation
        for task_id, task in constellation1.tasks.items():
            new_task = TaskStar(
                task_id=f"c1_{task_id}",
                description=task.description,
                priority=task.priority,
                device_type=task.device_type,
            )
            merged.add_task(new_task)

        # Add tasks from second constellation
        for task_id, task in constellation2.tasks.items():
            new_task = TaskStar(
                task_id=f"c2_{task_id}",
                description=task.description,
                priority=task.priority,
                device_type=task.device_type,
            )
            merged.add_task(new_task)

        # Add dependencies from both constellations (with adjusted task IDs)
        for dep in constellation1.dependencies.values():
            new_dep = TaskStarLine(
                from_task_id=f"c1_{dep.from_task_id}",
                to_task_id=f"c1_{dep.to_task_id}",
                dependency_type=dep.dependency_type,
                condition_description=dep.condition_description,
            )
            merged.add_dependency(new_dep)

        for dep in constellation2.dependencies.values():
            new_dep = TaskStarLine(
                from_task_id=f"c2_{dep.from_task_id}",
                to_task_id=f"c2_{dep.to_task_id}",
                dependency_type=dep.dependency_type,
                condition_description=dep.condition_description,
            )
            merged.add_dependency(new_dep)

        if self._logger:
            self._logger.info(
                f"Created merged constellation with {merged.task_count} tasks and {merged.dependency_count} dependencies"
            )

        return merged
