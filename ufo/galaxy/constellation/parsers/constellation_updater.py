"""
Constellation update utilities.
Handles updating existing TaskConstellation objects with new tasks, dependencies, or modifications.
"""

import logging
from typing import Any, Dict, List, Optional, Set

from .task_constellation import TaskConstellation
from .task_star import TaskStar, TaskPriority, TaskStatus
from .task_star_line import TaskStarLine


class ConstellationUpdater:
    """
    Handles updating existing TaskConstellation objects.
    Responsible for adding, removing, and modifying tasks and dependencies.
    """

    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize the constellation updater.

        Args:
            logger: Optional logger for debugging
        """
        self._logger = logger

    def update_from_llm_output(
        self,
        constellation: TaskConstellation,
        llm_output: str,
        preserve_existing: bool = True,
    ) -> None:
        """
        Update an existing constellation based on LLM output.

        Args:
            constellation: Existing constellation to update
            llm_output: LLM response with update instructions
            preserve_existing: Whether to preserve existing tasks/dependencies
        """
        if self._logger:
            self._logger.info(
                f"Updating constellation '{constellation.name}' from LLM output"
            )

        # Parse the LLM output for update instructions
        update_instructions = self._parse_llm_update_instructions(llm_output)

        # Apply updates based on instructions
        for instruction in update_instructions:
            self._apply_update_instruction(
                constellation, instruction, preserve_existing
            )

        if self._logger:
            self._logger.info(
                f"Updated constellation '{constellation.name}' - "
                f"Tasks: {constellation.task_count}, Dependencies: {constellation.dependency_count}"
            )

    def add_tasks(
        self,
        constellation: TaskConstellation,
        task_descriptions: List[str],
        priority: TaskPriority = TaskPriority.MEDIUM,
    ) -> List[TaskStar]:
        """
        Add new tasks to an existing constellation.

        Args:
            constellation: Target constellation
            task_descriptions: List of task descriptions to add
            priority: Priority for new tasks

        Returns:
            List of created TaskStar objects
        """
        created_tasks = []

        for i, description in enumerate(task_descriptions):
            # Generate unique task ID
            task_id = f"task_{constellation.task_count + i + 1}"

            task = TaskStar(
                task_id=task_id,
                description=description,
                priority=priority,
            )

            constellation.add_task(task)
            created_tasks.append(task)

        if self._logger:
            self._logger.info(
                f"Added {len(created_tasks)} tasks to constellation '{constellation.name}'"
            )

        return created_tasks

    def remove_tasks(
        self,
        constellation: TaskConstellation,
        task_ids: List[str],
        remove_dependencies: bool = True,
    ) -> None:
        """
        Remove tasks from a constellation.

        Args:
            constellation: Target constellation
            task_ids: List of task IDs to remove
            remove_dependencies: Whether to remove related dependencies
        """
        removed_count = 0

        for task_id in task_ids:
            if task_id in constellation.tasks:
                # Remove related dependencies if requested
                if remove_dependencies:
                    self._remove_task_dependencies(constellation, task_id)

                # Remove the task
                constellation.remove_task(task_id)
                removed_count += 1

        if self._logger:
            self._logger.info(
                f"Removed {removed_count} tasks from constellation '{constellation.name}'"
            )

    def add_dependencies(
        self,
        constellation: TaskConstellation,
        dependencies: List[Dict[str, Any]],
    ) -> List[TaskStarLine]:
        """
        Add new dependencies to a constellation.

        Args:
            constellation: Target constellation
            dependencies: List of dependency specifications

        Returns:
            List of created TaskStarLine objects
        """
        created_deps = []

        for dep_spec in dependencies:
            # Create dependency from specification
            dep = self._create_dependency_from_spec(constellation, dep_spec)
            if dep:
                constellation.add_dependency(dep)
                created_deps.append(dep)

        if self._logger:
            self._logger.info(
                f"Added {len(created_deps)} dependencies to constellation '{constellation.name}'"
            )

        return created_deps

    def _parse_llm_update_instructions(self, llm_output: str) -> List[Dict[str, Any]]:
        """
        Parse LLM output for update instructions.

        Args:
            llm_output: Raw LLM response

        Returns:
            List of parsed update instructions
        """
        # This is a simplified parser - in practice, this would be more sophisticated
        instructions = []

        # Look for common update patterns
        lines = llm_output.strip().split("\n")
        current_instruction = None

        for line in lines:
            line = line.strip()

            if line.startswith("ADD TASK:"):
                if current_instruction:
                    instructions.append(current_instruction)
                current_instruction = {
                    "type": "add_task",
                    "description": line.replace("ADD TASK:", "").strip(),
                }
            elif line.startswith("REMOVE TASK:"):
                if current_instruction:
                    instructions.append(current_instruction)
                current_instruction = {
                    "type": "remove_task",
                    "task_id": line.replace("REMOVE TASK:", "").strip(),
                }
            elif line.startswith("ADD DEPENDENCY:"):
                if current_instruction:
                    instructions.append(current_instruction)
                current_instruction = {
                    "type": "add_dependency",
                    "spec": line.replace("ADD DEPENDENCY:", "").strip(),
                }

        if current_instruction:
            instructions.append(current_instruction)

        return instructions

    def _apply_update_instruction(
        self,
        constellation: TaskConstellation,
        instruction: Dict[str, Any],
        preserve_existing: bool,
    ) -> None:
        """
        Apply a single update instruction to the constellation.

        Args:
            constellation: Target constellation
            instruction: Update instruction to apply
            preserve_existing: Whether to preserve existing elements
        """
        instruction_type = instruction.get("type")

        if instruction_type == "add_task":
            self.add_tasks(constellation, [instruction["description"]])
        elif instruction_type == "remove_task" and not preserve_existing:
            self.remove_tasks(constellation, [instruction["task_id"]])
        elif instruction_type == "add_dependency":
            # Parse dependency specification and add
            dep_spec = self._parse_dependency_spec(instruction["spec"])
            if dep_spec:
                self.add_dependencies(constellation, [dep_spec])

    def _remove_task_dependencies(
        self, constellation: TaskConstellation, task_id: str
    ) -> None:
        """
        Remove all dependencies related to a specific task.

        Args:
            constellation: Target constellation
            task_id: Task ID whose dependencies should be removed
        """
        deps_to_remove = []

        for dep_id, dep in constellation.dependencies.items():
            if dep.from_task_id == task_id or dep.to_task_id == task_id:
                deps_to_remove.append(dep_id)

        for dep_id in deps_to_remove:
            constellation.remove_dependency(dep_id)

    def _create_dependency_from_spec(
        self,
        constellation: TaskConstellation,
        dep_spec: Dict[str, Any],
    ) -> Optional[TaskStarLine]:
        """
        Create a TaskStarLine from a dependency specification.

        Args:
            constellation: Target constellation
            dep_spec: Dependency specification

        Returns:
            Created TaskStarLine or None if invalid
        """
        from_task_id = dep_spec.get("from_task_id") or dep_spec.get("predecessor_id")
        to_task_id = dep_spec.get("to_task_id") or dep_spec.get("successor_id")

        if not from_task_id or not to_task_id:
            return None

        # Verify tasks exist
        if (
            from_task_id not in constellation.tasks
            or to_task_id not in constellation.tasks
        ):
            return None

        # Create dependency
        return TaskStarLine.create_unconditional(
            from_task_id,
            to_task_id,
            dep_spec.get("description", f"Dependency: {from_task_id} -> {to_task_id}"),
        )

    def _parse_dependency_spec(self, spec_string: str) -> Optional[Dict[str, Any]]:
        """
        Parse a dependency specification string.

        Args:
            spec_string: String representation of dependency

        Returns:
            Parsed dependency specification or None
        """
        # Simple parser for "task1 -> task2" format
        if "->" in spec_string:
            parts = spec_string.split("->")
            if len(parts) == 2:
                return {
                    "from_task_id": parts[0].strip(),
                    "to_task_id": parts[1].strip(),
                    "description": f"Dependency: {spec_string}",
                }

        return None
