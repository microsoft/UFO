# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Visualization change detection and comparison utilities.

This module provides comprehensive change detection for visualization observers,
including task and dependency modifications, additions, and removals.
"""

from typing import TYPE_CHECKING, Any, Dict, Optional

if TYPE_CHECKING:
    from ..constellation.task_constellation import TaskConstellation

from ..constellation.task_star_line import TaskStarLine


class VisualizationChangeDetector:
    """
    Utility class for detecting and analyzing changes between constellation states.

    Provides comprehensive change detection for visualization observers,
    including task and dependency modifications, additions, and removals.
    """

    @staticmethod
    def calculate_constellation_changes(
        old_constellation: Optional["TaskConstellation"],
        new_constellation: "TaskConstellation",
    ) -> Dict[str, Any]:
        """
        Calculate detailed changes between old and new constellation by comparing their structure.

        :param old_constellation: Previous constellation state (can be None for new constellation)
        :param new_constellation: Current constellation state
        :return: Dictionary containing detailed changes
        """
        changes = {
            "modification_type": "constellation_created",
            "added_tasks": [],
            "removed_tasks": [],
            "modified_tasks": [],
            "added_dependencies": [],
            "removed_dependencies": [],
            "modified_dependencies": [],
        }

        if not old_constellation:
            # New constellation - all tasks and dependencies are "added"
            changes["modification_type"] = "constellation_created"
            changes["added_tasks"] = [
                task.task_id for task in new_constellation.tasks.values()
            ]
            changes["added_dependencies"] = [
                f"{dep.from_task_id}->{dep.to_task_id}"
                for dep in new_constellation.dependencies.values()
            ]
            return changes

        # Get task IDs for comparison
        old_task_ids = set(old_constellation.tasks.keys())
        new_task_ids = set(new_constellation.tasks.keys())

        # Calculate task changes
        changes["added_tasks"] = list(new_task_ids - old_task_ids)
        changes["removed_tasks"] = list(old_task_ids - new_task_ids)

        # Find modified tasks (same ID but different properties)
        common_task_ids = old_task_ids & new_task_ids
        for task_id in common_task_ids:
            old_task = old_constellation.tasks[task_id]
            new_task = new_constellation.tasks[task_id]

            # Check if task properties have changed
            if VisualizationChangeDetector._task_properties_changed(old_task, new_task):
                changes["modified_tasks"].append(task_id)

        # Calculate dependency changes
        old_deps = set()
        new_deps = set()
        old_dep_details = {}  # Store full dependency details for comparison
        new_dep_details = {}

        for dep in old_constellation.dependencies.values():
            dep_key = (dep.from_task_id, dep.to_task_id)
            old_deps.add(dep_key)
            old_dep_details[dep_key] = dep

        for dep in new_constellation.dependencies.values():
            dep_key = (dep.from_task_id, dep.to_task_id)
            new_deps.add(dep_key)
            new_dep_details[dep_key] = dep

        added_dep_tuples = new_deps - old_deps
        removed_dep_tuples = old_deps - new_deps

        changes["added_dependencies"] = [
            f"{from_id}->{to_id}" for from_id, to_id in added_dep_tuples
        ]
        changes["removed_dependencies"] = [
            f"{from_id}->{to_id}" for from_id, to_id in removed_dep_tuples
        ]

        # Find modified dependencies (same from->to but different properties)
        common_deps = old_deps & new_deps
        for dep_key in common_deps:
            old_dep = old_dep_details[dep_key]
            new_dep = new_dep_details[dep_key]

            # Check if dependency properties have changed
            if VisualizationChangeDetector._dependency_properties_changed(
                old_dep, new_dep
            ):
                changes["modified_dependencies"].append(f"{dep_key[0]}->{dep_key[1]}")

        # Determine overall modification type
        changes["modification_type"] = (
            VisualizationChangeDetector._determine_modification_type(changes)
        )

        return changes

    @staticmethod
    def _determine_modification_type(changes: Dict[str, Any]) -> str:
        """
        Determine the overall type of modification based on detected changes.

        :param changes: Dictionary containing detected changes
        :return: String describing the modification type
        """
        if changes["added_tasks"] and changes["removed_tasks"]:
            return "tasks_added_and_removed"
        elif changes["added_tasks"]:
            return "tasks_added"
        elif changes["removed_tasks"]:
            return "tasks_removed"
        elif changes["added_dependencies"] and changes["removed_dependencies"]:
            return "dependencies_modified"
        elif changes["added_dependencies"]:
            return "dependencies_added"
        elif changes["removed_dependencies"]:
            return "dependencies_removed"
        elif changes["modified_dependencies"]:
            return "dependency_properties_updated"
        elif changes["modified_tasks"]:
            return "task_properties_updated"
        else:
            return "constellation_updated"

    @staticmethod
    def _task_properties_changed(old_task, new_task) -> bool:
        """
        Check if task properties have changed between old and new versions.

        :param old_task: Previous task state
        :param new_task: Current task state
        :return: True if properties have changed
        """
        # Compare key properties that would indicate a modification
        properties_to_check = [
            "name",
            "description",
            "status",
            "priority",
            "target_device_id",
            "timeout",
            "retry_count",
            "tips",
        ]

        for prop in properties_to_check:
            old_value = getattr(old_task, prop, None)
            new_value = getattr(new_task, prop, None)

            if old_value != new_value:
                return True

        # Check task_data if it exists
        if hasattr(old_task, "task_data") and hasattr(new_task, "task_data"):
            if old_task.task_data != new_task.task_data:
                return True

        return False

    @staticmethod
    def _dependency_properties_changed(
        old_dep: TaskStarLine, new_dep: TaskStarLine
    ) -> bool:
        """
        Check if dependency properties have changed between old and new versions.

        :param old_dep: Previous dependency state
        :param new_dep: Current dependency state
        :return: True if properties have changed
        """
        # Compare key properties that would indicate a modification
        properties_to_check = [
            "trigger_action",
            "trigger_actor",
            "condition",
            "keyword",
            "description",
            "priority",
        ]

        for prop in properties_to_check:
            old_value = getattr(old_dep, prop, None)
            new_value = getattr(new_dep, prop, None)

            if old_value != new_value:
                return True

        return False

    @staticmethod
    def format_change_summary(changes: Dict[str, Any]) -> Dict[str, str]:
        """
        Format change information into human-readable summary.

        :param changes: Dictionary containing detected changes
        :return: Dictionary with formatted change descriptions
        """
        summary = {}

        if changes["added_tasks"]:
            task_count = len(changes["added_tasks"])
            task_names = changes["added_tasks"][:3]  # Show first 3
            if task_count <= 3:
                summary["added_tasks"] = (
                    f"{task_count} tasks added: {', '.join(task_names)}"
                )
            else:
                summary["added_tasks"] = (
                    f"{task_count} tasks added: {', '.join(task_names)} and {task_count - 3} more"
                )

        if changes["removed_tasks"]:
            task_count = len(changes["removed_tasks"])
            task_names = changes["removed_tasks"][:3]  # Show first 3
            if task_count <= 3:
                summary["removed_tasks"] = (
                    f"{task_count} tasks removed: {', '.join(task_names)}"
                )
            else:
                summary["removed_tasks"] = (
                    f"{task_count} tasks removed: {', '.join(task_names)} and {task_count - 3} more"
                )

        if changes["modified_tasks"]:
            task_count = len(changes["modified_tasks"])
            summary["modified_tasks"] = f"{task_count} tasks modified"

        if changes["added_dependencies"]:
            dep_count = len(changes["added_dependencies"])
            summary["added_dependencies"] = f"{dep_count} dependencies added"

        if changes["removed_dependencies"]:
            dep_count = len(changes["removed_dependencies"])
            summary["removed_dependencies"] = f"{dep_count} dependencies removed"

        if changes["modified_dependencies"]:
            dep_count = len(changes["modified_dependencies"])
            summary["modified_dependencies"] = f"{dep_count} dependencies modified"

        return summary
