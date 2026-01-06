# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
TaskConstellation - DAG management system for Constellation V2.

This module provides comprehensive task DAG management with LLM integration,
dynamic modification, and advanced dependency handling capabilities.
"""


import uuid
from collections import defaultdict, deque
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

from galaxy.constellation.enums import ConstellationState
from galaxy.visualization.dag_visualizer import DAGVisualizer

from ..core.interfaces import IConstellation

# Use the constellation-specific TaskStatus instead of contracts
from .enums import ConstellationState, TaskStatus
from .task_star import TaskStar
from .task_star_line import TaskStarLine

if TYPE_CHECKING:
    from galaxy.agents.schema import TaskConstellationSchema


class TaskConstellation(IConstellation):
    """
    Manages a DAG of tasks (TaskConstellation) with comprehensive orchestration capabilities.

    Provides:
    - DAG validation and cycle detection
    - Dynamic task and dependency management
    - LLM-based creation and modification
    - Execution state tracking
    - Export/import capabilities

    Implements IDAGManager interface for consistent DAG operations.
    """

    def __init__(
        self,
        constellation_id: Optional[str] = None,
        name: Optional[str] = None,
    ) -> None:
        """
        Initialize a TaskConstellation.

        :param constellation_id: Unique identifier (auto-generated if None)
        :param name: Human-readable name for the constellation
        """
        self._constellation_id: str = (
            constellation_id
            or f"constellation_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:8]}"
        )
        self._name: str = name or self._constellation_id
        self._state: ConstellationState = ConstellationState.CREATED

        # Core data structures
        self._tasks: Dict[str, TaskStar] = {}
        self._dependencies: Dict[str, TaskStarLine] = {}

        # Tracking
        self._created_at: datetime = datetime.now(timezone.utc)
        self._updated_at: datetime = self._created_at
        self._execution_start_time: Optional[datetime] = None
        self._execution_end_time: Optional[datetime] = None

        # Metadata
        self._metadata: Dict[str, Any] = {}

    @property
    def constellation_id(self) -> str:
        """Get the constellation ID."""
        return self._constellation_id

    @property
    def name(self) -> str:
        """Get the constellation name."""
        return self._name

    @name.setter
    def name(self, value: str) -> None:
        """Set the constellation name."""
        self._name = value
        self._updated_at = datetime.now(timezone.utc)

    @property
    def state(self) -> ConstellationState:
        """Get the constellation state."""
        return self._state

    @property
    def tasks(self) -> Dict[str, TaskStar]:
        """Get a copy of all tasks."""
        return self._tasks.copy()

    @property
    def dependencies(self) -> Dict[str, TaskStarLine]:
        """Get a copy of all dependencies."""
        return self._dependencies.copy()

    @property
    def task_count(self) -> int:
        """Get the number of tasks."""
        return len(self._tasks)

    @property
    def dependency_count(self) -> int:
        """Get the number of dependencies."""
        return len(self._dependencies)

    @property
    def created_at(self) -> datetime:
        """Get the creation timestamp."""
        return self._created_at

    @property
    def updated_at(self) -> datetime:
        """Get the last update timestamp."""
        return self._updated_at

    @property
    def execution_start_time(self) -> Optional[datetime]:
        """Get the execution start timestamp."""
        return self._execution_start_time

    @property
    def execution_end_time(self) -> Optional[datetime]:
        """Get the execution end timestamp."""
        return self._execution_end_time

    @property
    def execution_duration(self) -> Optional[float]:
        """Get the execution duration in seconds."""
        if self._execution_start_time and self._execution_end_time:
            return (
                self._execution_end_time - self._execution_start_time
            ).total_seconds()
        return None

    @property
    def metadata(self) -> Dict[str, Any]:
        """Get a copy of the metadata."""
        return self._metadata.copy()

    def update_metadata(self, metadata: Dict[str, Any]) -> None:
        """Update the constellation metadata."""
        self._metadata.update(metadata)
        self._updated_at = datetime.now(timezone.utc)

    def add_task(self, task: TaskStar) -> None:
        """
        Add a task to the constellation.

        :param task: TaskStar instance to add
        :raises ValueError: If task with same ID already exists
        """
        if task.task_id in self._tasks:
            raise ValueError(f"Task with ID {task.task_id} already exists")

        self._tasks[task.task_id] = task
        self._updated_at = datetime.now(timezone.utc)

        # Update constellation state as task composition changed
        self.update_state()

    def remove_task(self, task_id: str) -> None:
        """
        Remove a task from the constellation.

        :param task_id: ID of the task to remove
        :raises ValueError: If task doesn't exist or is running
        """
        if task_id not in self._tasks:
            raise ValueError(f"Task {task_id} not found")

        task = self._tasks[task_id]
        if task.status == TaskStatus.RUNNING:
            raise ValueError(f"Cannot remove running task {task_id}")

        # Remove all dependencies involving this task
        dependencies_to_remove = []
        for dep_id, dep in self._dependencies.items():
            if dep.from_task_id == task_id or dep.to_task_id == task_id:
                dependencies_to_remove.append(dep_id)

        for dep_id in dependencies_to_remove:
            self.remove_dependency(dep_id)

        del self._tasks[task_id]
        self._updated_at = datetime.now(timezone.utc)

        # Update constellation state as task composition changed
        self.update_state()

    def get_task(self, task_id: str) -> Optional[TaskStar]:
        """
        Get a task by ID.

        :param task_id: ID of the task
        :return: TaskStar instance or None if not found
        """
        return self._tasks.get(task_id)

    def add_dependency(self, dependency: TaskStarLine) -> None:
        """
        Add a dependency to the constellation.

        :param dependency: TaskStarLine instance to add
        :raises ValueError: If dependency would create a cycle or tasks don't exist
        """
        # Validate tasks exist
        if dependency.from_task_id not in self._tasks:
            raise ValueError(f"Source task {dependency.from_task_id} not found")
        if dependency.to_task_id not in self._tasks:
            raise ValueError(f"Target task {dependency.to_task_id} not found")

        # Check for cycle
        if self._would_create_cycle(dependency.from_task_id, dependency.to_task_id):
            raise ValueError(
                f"Adding dependency {dependency.from_task_id} -> {dependency.to_task_id} would create a cycle"
            )

        # Add the dependency
        self._dependencies[dependency.line_id] = dependency

        # Update task references
        from_task = self._tasks[dependency.from_task_id]
        to_task = self._tasks[dependency.to_task_id]

        from_task.add_dependent(dependency.to_task_id)
        to_task.add_dependency(dependency.from_task_id)

        self._updated_at = datetime.now(timezone.utc)

        # Update constellation state as dependencies changed
        self.update_state()

    def remove_dependency(self, dependency_id: str) -> None:
        """
        Remove a dependency from the constellation.

        :param dependency_id: ID of the dependency to remove
        """
        if dependency_id not in self._dependencies:
            return

        dependency = self._dependencies[dependency_id]

        # Update task references
        if dependency.from_task_id in self._tasks:
            from_task = self._tasks[dependency.from_task_id]
            from_task.remove_dependent(dependency.to_task_id)

        if dependency.to_task_id in self._tasks:
            to_task = self._tasks[dependency.to_task_id]
            to_task.remove_dependency(dependency.from_task_id)

        del self._dependencies[dependency_id]
        self._updated_at = datetime.now(timezone.utc)

        # Update constellation state as dependencies changed
        self.update_state()

    def get_dependency(self, dependency_id: str) -> Optional[TaskStarLine]:
        """
        Get a dependency by ID.

        :param dependency_id: ID of the dependency
        :return: TaskStarLine instance or None if not found
        """
        return self._dependencies.get(dependency_id)

    def get_ready_tasks(self) -> List[TaskStar]:
        """
        Get all tasks that are ready to execute.

        :return: List of TaskStar instances ready for execution
        """
        ready_tasks = []
        for task in self._tasks.values():
            if task.is_ready_to_execute:
                # Double-check dependencies are satisfied
                if self._are_dependencies_satisfied(task.task_id):
                    ready_tasks.append(task)

        # Sort by priority (higher priority first)
        ready_tasks.sort(key=lambda t: t.priority.value, reverse=True)
        return ready_tasks

    def get_running_tasks(self) -> List[TaskStar]:
        """Get all currently running tasks."""
        return [
            task for task in self._tasks.values() if task.status == TaskStatus.RUNNING
        ]

    def get_completed_tasks(self) -> List[TaskStar]:
        """Get all completed tasks."""
        return [
            task for task in self._tasks.values() if task.status == TaskStatus.COMPLETED
        ]

    def get_failed_tasks(self) -> List[TaskStar]:
        """Get all failed tasks."""
        return [
            task for task in self._tasks.values() if task.status == TaskStatus.FAILED
        ]

    def get_pending_tasks(self) -> List[TaskStar]:
        """Get all pending tasks."""
        return [
            task for task in self._tasks.values() if task.status == TaskStatus.PENDING
        ]

    def get_all_tasks(self) -> List[TaskStar]:
        """Get all tasks in the constellation."""
        return list(self._tasks.values())

    def get_all_dependencies(self) -> List[TaskStarLine]:
        """Get all dependencies in the constellation."""
        return list(self._dependencies.values())

    def get_task_dependencies(self, task_id: str) -> List[TaskStarLine]:
        """Get dependencies for a specific task."""
        return [dep for dep in self._dependencies.values() if dep.to_task_id == task_id]

    def get_modifiable_tasks(self) -> List[TaskStar]:
        """
        Get all tasks that can be modified (PENDING or WAITING_DEPENDENCY status).

        :return: List of tasks that are safe to modify
        """
        modifiable_statuses = {TaskStatus.PENDING, TaskStatus.WAITING_DEPENDENCY}
        return [
            task for task in self._tasks.values() if task.status in modifiable_statuses
        ]

    def get_modifiable_dependencies(self) -> List[TaskStarLine]:
        """
        Get all dependencies that can be modified.
        A dependency can be modified if its target task (to_task_id) has not started.

        :return: List of dependencies that are safe to modify
        """
        modifiable_deps = []
        modifiable_statuses = {TaskStatus.PENDING, TaskStatus.WAITING_DEPENDENCY}

        for dep in self._dependencies.values():
            target_task = self._tasks.get(dep.to_task_id)
            if target_task and target_task.status in modifiable_statuses:
                modifiable_deps.append(dep)

        return modifiable_deps

    def is_task_modifiable(self, task_id: str) -> bool:
        """
        Check if a specific task can be modified.

        :param task_id: ID of the task to check
        :return: True if task is modifiable, False otherwise
        """
        task = self._tasks.get(task_id)
        if not task:
            return False
        return task.status in {TaskStatus.PENDING, TaskStatus.WAITING_DEPENDENCY}

    def is_dependency_modifiable(self, dependency_id: str) -> bool:
        """
        Check if a specific dependency can be modified.

        :param dependency_id: ID of the dependency to check
        :return: True if dependency is modifiable, False otherwise
        """
        dep = self._dependencies.get(dependency_id)
        if not dep:
            return False
        target_task = self._tasks.get(dep.to_task_id)
        if not target_task:
            return False
        return target_task.status in {TaskStatus.PENDING, TaskStatus.WAITING_DEPENDENCY}

    def is_complete(self) -> bool:
        """Check if the entire constellation has completed execution."""
        return all(task.is_terminal for task in self._tasks.values())

    def update_state(self) -> None:
        """Update the constellation state based on task states."""
        if not self._tasks:
            self._state = ConstellationState.CREATED
            return

        all_terminal = all(task.is_terminal for task in self._tasks.values())
        has_running = any(
            task.status == TaskStatus.RUNNING for task in self._tasks.values()
        )
        has_failed = any(
            task.status == TaskStatus.FAILED for task in self._tasks.values()
        )
        has_completed = any(
            task.status == TaskStatus.COMPLETED for task in self._tasks.values()
        )

        if all_terminal:
            if has_failed and has_completed:
                self._state = ConstellationState.PARTIALLY_FAILED
            elif has_failed:
                self._state = ConstellationState.FAILED
            else:
                self._state = ConstellationState.COMPLETED
        elif has_running or has_completed:
            self._state = ConstellationState.EXECUTING
        else:
            self._state = ConstellationState.READY

    def start_task(self, task_id: str) -> None:
        """
        Start execution of a task.

        :param task_id: ID of the task to start
        :raises ValueError: If task not found or not ready to start
        """
        if task_id not in self._tasks:
            raise ValueError(f"Task {task_id} not found")

        task = self._tasks[task_id]
        task.start_execution()

        # Update constellation state as task status changed
        self.update_state()

    def mark_task_completed(
        self, task_id: str, success: bool, result: Any = None, error: Exception = None
    ) -> List[TaskStar]:
        """
        Mark a task as completed and update dependent tasks.

        :param task_id: ID of the completed task
        :param success: Whether the task completed successfully
        :param result: Task result (if successful)
        :param error: Error information (if failed)
        :return: List of newly ready tasks after dependency updates
        """
        if task_id not in self._tasks:
            raise ValueError(f"Task {task_id} not found")

        task = self._tasks[task_id]

        # If task is not running, start it first
        if task.status == TaskStatus.PENDING:
            task.start_execution()

        # Mark the task as completed
        if success:
            task.complete_with_success(result)
        else:
            task.complete_with_failure(error)

        # Update dependent tasks
        newly_ready = []
        for dependency in self._dependencies.values():
            if dependency.from_task_id == task_id:
                # This completed task is a prerequisite for the dependent task
                dependent_task = self._tasks.get(dependency.to_task_id)
                if dependent_task and dependent_task.status == TaskStatus.PENDING:
                    # Evaluate the dependency condition
                    if dependency.evaluate_condition(result if success else error):
                        dependent_task.remove_dependency(task_id)

                        # Check if dependent task is now ready
                        if self._are_dependencies_satisfied(dependent_task.task_id):
                            newly_ready.append(dependent_task)

        self.update_state()
        self._updated_at = datetime.now(timezone.utc)

        return newly_ready

    def validate_dag(self) -> Tuple[bool, List[str]]:
        """
        Validate the DAG structure.

        :return: Tuple of (is_valid, list_of_errors)
        """
        errors = []

        # Check for cycles
        if self.has_cycle():
            errors.append("DAG contains cycles")

        # Check for invalid dependencies
        for dependency in self._dependencies.values():
            if dependency.from_task_id not in self._tasks:
                errors.append(
                    f"Dependency references non-existent source task {dependency.from_task_id}"
                )
            if dependency.to_task_id not in self._tasks:
                errors.append(
                    f"Dependency references non-existent target task {dependency.to_task_id}"
                )

        return len(errors) == 0, errors

    def get_topological_order(self) -> List[str]:
        """
        Get a topological ordering of the DAG.

        :return: List of task IDs in topological order
        :raises ValueError: If DAG contains cycles
        """
        # Build adjacency list from dependencies
        in_degree = defaultdict(int)
        adjacency = defaultdict(list)

        # Initialize all tasks with 0 in-degree
        for task_id in self._tasks:
            in_degree[task_id] = 0

        # Build the graph from dependencies
        for dependency in self._dependencies.values():
            from_task = dependency.from_task_id
            to_task = dependency.to_task_id

            adjacency[from_task].append(to_task)
            in_degree[to_task] += 1

        # Kahn's algorithm
        queue = deque([task_id for task_id, degree in in_degree.items() if degree == 0])
        result = []

        while queue:
            current = queue.popleft()
            result.append(current)

            for neighbor in adjacency[current]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        if len(result) != len(self._tasks):
            raise ValueError("DAG contains cycles")

        return result

    def get_longest_path(self) -> Tuple[int, List[str]]:
        """
        Calculate the longest path in the DAG (critical path).

        :return: Tuple of (path_length, list_of_task_ids_in_longest_path)
        """
        if not self._tasks:
            return (0, [])

        # Build adjacency list
        adjacency = defaultdict(list)
        in_degree = defaultdict(int)

        for task_id in self._tasks:
            in_degree[task_id] = 0

        for dependency in self._dependencies.values():
            adjacency[dependency.from_task_id].append(dependency.to_task_id)
            in_degree[dependency.to_task_id] += 1

        # Find all root nodes (nodes with no incoming edges)
        queue = deque([task_id for task_id, degree in in_degree.items() if degree == 0])

        # Track longest path to each node
        longest_distance = {task_id: 0 for task_id in self._tasks}
        parent = {task_id: None for task_id in self._tasks}

        # Process nodes in topological order
        while queue:
            current = queue.popleft()
            current_distance = longest_distance[current]

            for neighbor in adjacency[current]:
                # Update longest distance if we found a longer path
                if longest_distance[neighbor] < current_distance + 1:
                    longest_distance[neighbor] = current_distance + 1
                    parent[neighbor] = current

                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        # Find the node with maximum distance (end of longest path)
        max_distance = 0
        end_node = None
        for task_id, distance in longest_distance.items():
            if distance > max_distance:
                max_distance = distance
                end_node = task_id

        # Reconstruct the longest path
        path = []
        if end_node:
            current = end_node
            while current is not None:
                path.append(current)
                current = parent[current]
            path.reverse()

        return (max_distance + 1, path)

    def get_max_width(self) -> int:
        """
        Calculate the maximum width of the DAG (maximum number of nodes at any level).

        :return: Maximum width of the DAG
        """
        if not self._tasks:
            return 0

        # Build adjacency list and calculate in-degrees
        adjacency = defaultdict(list)
        in_degree = defaultdict(int)

        for task_id in self._tasks:
            in_degree[task_id] = 0

        for dependency in self._dependencies.values():
            adjacency[dependency.from_task_id].append(dependency.to_task_id)
            in_degree[dependency.to_task_id] += 1

        # BFS level-order traversal to find width at each level
        queue = deque([task_id for task_id, degree in in_degree.items() if degree == 0])
        max_width = len(queue)

        level_in_degree = in_degree.copy()

        while queue:
            level_size = len(queue)
            max_width = max(max_width, level_size)

            # Process all nodes at current level
            for _ in range(level_size):
                current = queue.popleft()

                for neighbor in adjacency[current]:
                    level_in_degree[neighbor] -= 1
                    if level_in_degree[neighbor] == 0:
                        queue.append(neighbor)

        return max_width

    def get_critical_path_length_with_time(self) -> Tuple[float, List[str]]:
        """
        Calculate the critical path length using actual execution times.
        Only valid when all tasks are completed or failed.

        :return: Tuple of (critical_path_duration_seconds, list_of_task_ids_in_critical_path)
        """
        if not self._tasks:
            return (0.0, [])

        # Build adjacency list
        adjacency = defaultdict(list)
        in_degree = defaultdict(int)

        for task_id in self._tasks:
            in_degree[task_id] = 0

        for dependency in self._dependencies.values():
            adjacency[dependency.from_task_id].append(dependency.to_task_id)
            in_degree[dependency.to_task_id] += 1

        # Find all root nodes
        queue = deque([task_id for task_id, degree in in_degree.items() if degree == 0])

        # Track longest time path to each node
        longest_time = {task_id: 0.0 for task_id in self._tasks}
        parent = {task_id: None for task_id in self._tasks}

        # Initialize root nodes with their execution durations
        for task_id in queue:
            task = self._tasks[task_id]
            duration = task.execution_duration or 0.0
            longest_time[task_id] = duration

        # Process nodes in topological order
        processing_queue = deque(queue)
        while processing_queue:
            current = processing_queue.popleft()
            current_time = longest_time[current]

            for neighbor in adjacency[current]:
                neighbor_task = self._tasks[neighbor]
                neighbor_duration = neighbor_task.execution_duration or 0.0

                # Update longest time if we found a longer path
                new_time = current_time + neighbor_duration
                if longest_time[neighbor] < new_time:
                    longest_time[neighbor] = new_time
                    parent[neighbor] = current

                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    processing_queue.append(neighbor)

        # Find the node with maximum time (end of critical path)
        max_time = 0.0
        end_node = None
        for task_id, time in longest_time.items():
            if time > max_time:
                max_time = time
                end_node = task_id

        # Reconstruct the critical path
        path = []
        if end_node:
            current = end_node
            while current is not None:
                path.append(current)
                current = parent[current]
            path.reverse()

        return (max_time, path)

    def get_total_work(self) -> float:
        """
        Calculate total work (sum of all task execution durations).

        :return: Total work in seconds
        """
        total = 0.0
        for task in self._tasks.values():
            duration = task.execution_duration
            if duration is not None:
                total += duration
        return total

    def get_parallelism_metrics(self) -> Dict[str, Any]:
        """
        Calculate parallelism metrics including:
        - L: Critical Path Length (longest serial dependency chain)
        - W: Total Work (sum of all task execution times)
        - P: Parallelism Ratio (W / L)

        Two calculation modes:
        1. When tasks are incomplete: Use node counts and path lengths
        2. When all tasks are complete/failed: Use actual execution times

        :return: Dictionary with parallelism metrics
        """
        if not self._tasks:
            return {
                "critical_path_length": 0,
                "total_work": 0,
                "parallelism_ratio": 0.0,
                "calculation_mode": "empty",
                "critical_path_tasks": [],
            }

        # Check if all tasks are in terminal state (completed or failed)
        all_terminal = all(task.is_terminal for task in self._tasks.values())

        if all_terminal:
            # Use actual execution times
            critical_path_time, critical_path_tasks = (
                self.get_critical_path_length_with_time()
            )
            total_work = self.get_total_work()

            # Calculate parallelism ratio
            parallelism_ratio = (
                total_work / critical_path_time if critical_path_time > 0 else 0.0
            )

            return {
                "critical_path_length": critical_path_time,
                "total_work": total_work,
                "parallelism_ratio": parallelism_ratio,
                "calculation_mode": "actual_time",
                "critical_path_tasks": critical_path_tasks,
            }
        else:
            # Use node counts (each task counts as 1 unit)
            longest_path_length, longest_path_tasks = self.get_longest_path()
            total_nodes = len(self._tasks)

            # Calculate parallelism ratio using node counts
            parallelism_ratio = (
                total_nodes / longest_path_length if longest_path_length > 0 else 0.0
            )

            return {
                "critical_path_length": longest_path_length,
                "total_work": total_nodes,
                "parallelism_ratio": parallelism_ratio,
                "calculation_mode": "node_count",
                "critical_path_tasks": longest_path_tasks,
            }

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about the constellation.

        :return: Dictionary with statistics
        """
        status_counts = defaultdict(int)
        for task in self._tasks.values():
            status_counts[task.status.value] += 1

        # Calculate longest path and max width
        longest_path_length, longest_path_tasks = self.get_longest_path()
        max_width = self.get_max_width()

        # Calculate parallelism metrics (L, W, P)
        parallelism_metrics = self.get_parallelism_metrics()

        return {
            "constellation_id": self._constellation_id,
            "name": self._name,
            "state": self._state.value,
            "total_tasks": len(self._tasks),
            "total_dependencies": len(self._dependencies),
            "task_status_counts": dict(status_counts),
            "longest_path_length": longest_path_length,
            "longest_path_tasks": longest_path_tasks,
            "max_width": max_width,
            "critical_path_length": parallelism_metrics["critical_path_length"],
            "total_work": parallelism_metrics["total_work"],
            "parallelism_ratio": parallelism_metrics["parallelism_ratio"],
            "parallelism_calculation_mode": parallelism_metrics["calculation_mode"],
            "critical_path_tasks": parallelism_metrics["critical_path_tasks"],
            "execution_duration": self.execution_duration,
            "created_at": self._created_at.isoformat(),
            "updated_at": self._updated_at.isoformat(),
            "execution_start_time": (
                self._execution_start_time.isoformat()
                if self._execution_start_time
                else None
            ),
            "execution_end_time": (
                self._execution_end_time.isoformat()
                if self._execution_end_time
                else None
            ),
        }

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the TaskConstellation to a dictionary representation.

        :return: Dictionary representation of the TaskConstellation
        """
        # Convert tasks using their to_dict methods
        tasks_dict = {}
        for task_id, task in self._tasks.items():
            tasks_dict[task_id] = task.to_dict()

        # Convert dependencies using their to_dict methods
        dependencies_dict = {}
        for dep_id, dependency in self._dependencies.items():
            dependencies_dict[dep_id] = dependency.to_dict()

        return {
            "constellation_id": self._constellation_id,
            "name": self._name,
            "state": self._state.value,
            "tasks": tasks_dict,
            "dependencies": dependencies_dict,
            "metadata": self._metadata,
            "created_at": self._created_at.isoformat(),
            "updated_at": self._updated_at.isoformat(),
            "execution_start_time": (
                self._execution_start_time.isoformat()
                if self._execution_start_time
                else None
            ),
            "execution_end_time": (
                self._execution_end_time.isoformat()
                if self._execution_end_time
                else None
            ),
            "execution_duration": self.execution_duration,
        }

    @staticmethod
    def _parse_constellation_state(state_value: Any) -> ConstellationState:
        """
        Parse constellation state value (string or ConstellationState) into ConstellationState enum.

        :param state_value: State value to parse
        :return: ConstellationState enum instance
        """
        if isinstance(state_value, ConstellationState):
            return state_value
        elif isinstance(state_value, str):
            # Map string names to ConstellationState
            state_map = {
                "CREATED": ConstellationState.CREATED,
                "READY": ConstellationState.READY,
                "EXECUTING": ConstellationState.EXECUTING,
                "COMPLETED": ConstellationState.COMPLETED,
                "FAILED": ConstellationState.FAILED,
                "PARTIALLY_FAILED": ConstellationState.PARTIALLY_FAILED,
            }
            return state_map.get(state_value.upper(), ConstellationState.CREATED)
        else:
            return ConstellationState.CREATED

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TaskConstellation":
        """
        Create a TaskConstellation from a dictionary representation.

        :param data: Dictionary representation
        :return: TaskConstellation instance
        """
        # Create constellation with basic properties
        constellation = cls(
            constellation_id=data.get("constellation_id"), name=data.get("name")
        )

        # Restore state and metadata
        constellation._state = cls._parse_constellation_state(
            data.get("state", ConstellationState.CREATED.value)
        )
        constellation._metadata = data.get("metadata", {})

        # Restore timestamps
        if data.get("created_at"):
            constellation._created_at = datetime.fromisoformat(data["created_at"])
        if data.get("updated_at"):
            constellation._updated_at = datetime.fromisoformat(data["updated_at"])
        if data.get("execution_start_time"):
            constellation._execution_start_time = datetime.fromisoformat(
                data["execution_start_time"]
            )
        if data.get("execution_end_time"):
            constellation._execution_end_time = datetime.fromisoformat(
                data["execution_end_time"]
            )

        # Restore tasks using TaskStar.from_dict
        for task_id, task_data in data.get("tasks", {}).items():
            task = TaskStar.from_dict(task_data)
            constellation._tasks[task_id] = task

        # Restore dependencies using TaskStarLine.from_dict
        for dep_id, dep_data in data.get("dependencies", {}).items():
            dependency = TaskStarLine.from_dict(dep_data)
            constellation._dependencies[dep_id] = dependency

        return constellation

    def to_json(self, save_path: Optional[str] = None) -> str:
        """
        Convert the TaskConstellation to a JSON string representation.

        :param save_path: Optional file path to save the JSON to disk
        :return: JSON string representation of the TaskConstellation
        :raises IOError: If file writing fails when save_path is provided
        """
        import json

        # Get dictionary representation
        constellation_dict = self.to_dict()

        # Handle potentially non-serializable attributes
        serializable_dict = self._ensure_json_serializable(constellation_dict)

        # Convert to JSON string with proper formatting
        json_str = json.dumps(serializable_dict, indent=2, ensure_ascii=False)

        # Save to file if path provided
        if save_path:
            try:
                with open(save_path, "w", encoding="utf-8") as f:
                    f.write(json_str)
            except FileNotFoundError as e:
                raise IOError(
                    f"Directory not found for save path {save_path}: {e}"
                ) from e
            except PermissionError as e:
                raise IOError(f"Permission denied writing to {save_path}: {e}") from e
            except OSError as e:
                raise IOError(
                    f"OS error saving TaskConstellation to {save_path}: {e}"
                ) from e
            except Exception as e:
                raise IOError(
                    f"Unexpected error saving TaskConstellation to {save_path}: {e}"
                ) from e

        return json_str

    def _ensure_json_serializable(self, data: Any) -> Any:
        """
        Recursively ensure all values are JSON serializable.

        :param data: Data to make serializable (can be dict, list, or primitive)
        :return: JSON serializable data
        """
        import json
        from enum import Enum
        from datetime import datetime

        # Handle None
        if data is None:
            return None

        # Handle primitives that are already JSON serializable
        if isinstance(data, (str, int, float, bool)):
            return data

        # Handle datetime
        if isinstance(data, datetime):
            return data.isoformat()

        # Handle Enum
        if isinstance(data, Enum):
            return data.value

        # Handle dictionaries recursively
        if isinstance(data, dict):
            serializable_dict = {}
            for key, value in data.items():
                try:
                    # Try to serialize the value to test it
                    json.dumps(value)
                    serializable_dict[key] = value
                except (TypeError, ValueError):
                    # Recursively handle non-serializable values
                    serializable_dict[key] = self._ensure_json_serializable(value)
            return serializable_dict

        # Handle lists recursively
        if isinstance(data, (list, tuple)):
            return [self._ensure_json_serializable(item) for item in data]

        # Handle sets
        if isinstance(data, set):
            return [self._ensure_json_serializable(item) for item in data]

        # Handle objects with __dict__
        if hasattr(data, "__dict__"):
            try:
                obj_dict = vars(data)
                return self._ensure_json_serializable(obj_dict)
            except:
                return str(data)

        # Handle callables
        if callable(data):
            return f"<callable: {getattr(data, '__name__', 'unknown')}>"

        # Fallback to string representation
        return str(data)

    @classmethod
    def from_json(
        cls, json_data: Optional[str] = None, file_path: Optional[str] = None
    ) -> "TaskConstellation":
        """
        Create a TaskConstellation from a JSON string or JSON file.

        :param json_data: JSON string representation of the TaskConstellation
        :param file_path: Path to JSON file containing TaskConstellation data
        :return: TaskConstellation instance
        :raises ValueError: If neither json_data nor file_path is provided, or both are provided
        :raises FileNotFoundError: If file_path is provided but file doesn't exist
        :raises json.JSONDecodeError: If JSON parsing fails
        :raises IOError: If file reading fails
        """
        import json

        if json_data is None and file_path is None:
            raise ValueError("Either json_data or file_path must be provided")

        if json_data is not None and file_path is not None:
            raise ValueError("Only one of json_data or file_path should be provided")

        # Load JSON data
        if file_path:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except FileNotFoundError:
                raise FileNotFoundError(f"JSON file not found: {file_path}")
            except Exception as e:
                raise IOError(f"Failed to read JSON file {file_path}: {e}")
        else:
            try:
                data = json.loads(json_data)
            except json.JSONDecodeError as e:
                raise json.JSONDecodeError(
                    f"Invalid JSON format: {e}", json_data, e.pos
                )

        # Validate that data is a dictionary
        if not isinstance(data, dict):
            raise ValueError("JSON data must represent a dictionary/object")

        # Create TaskConstellation instance from dictionary
        return cls.from_dict(data)

    @classmethod
    def from_basemodel(cls, schema: "TaskConstellationSchema") -> "TaskConstellation":
        """
        Create a TaskConstellation from a Pydantic BaseModel schema.

        :param schema: TaskConstellationSchema instance
        :return: TaskConstellation instance
        """
        from galaxy.agents.schema import TaskConstellationSchema

        if not isinstance(schema, TaskConstellationSchema):
            raise ValueError("Expected TaskConstellationSchema instance")

        # Convert schema to dict and use existing from_dict method
        data = schema.model_dump()
        return cls.from_dict(data)

    def to_basemodel(self) -> "TaskConstellationSchema":
        """
        Convert the TaskConstellation to a Pydantic BaseModel schema.

        :return: TaskConstellationSchema instance
        """
        from galaxy.agents.schema import TaskConstellationSchema

        # Get dictionary representation and create schema
        data = self.to_dict()
        return TaskConstellationSchema(**data)

    def _are_dependencies_satisfied(self, task_id: str) -> bool:
        """Check if all dependencies for a task are satisfied."""
        task = self._tasks.get(task_id)
        if not task:
            return False

        for dependency in self._dependencies.values():
            if dependency.to_task_id == task_id:
                prerequisite_task = self._tasks.get(dependency.from_task_id)
                if not prerequisite_task or not prerequisite_task.is_terminal:
                    return False

                # Check if dependency condition is satisfied
                if not dependency.is_satisfied:
                    # Try to evaluate the condition
                    result = (
                        prerequisite_task.result
                        if prerequisite_task.status == TaskStatus.COMPLETED
                        else prerequisite_task.error
                    )
                    if not dependency.evaluate_condition(result):
                        return False

        return True

    def _would_create_cycle(self, from_task_id: str, to_task_id: str) -> bool:
        """Check if adding a dependency would create a cycle."""
        # Use DFS to check if there's already a path from to_task_id to from_task_id
        visited = set()

        def has_path(current: str, target: str) -> bool:
            if current == target:
                return True
            if current in visited:
                return False

            visited.add(current)

            # Check all dependencies where current is the source
            for dependency in self._dependencies.values():
                if dependency.from_task_id == current:
                    if has_path(dependency.to_task_id, target):
                        return True

            return False

        return has_path(to_task_id, from_task_id)

    def has_cycle(self) -> bool:
        """Check if the DAG has any cycles."""
        try:
            self.get_topological_order()
            return False
        except ValueError:
            return True

    def start_execution(self) -> None:
        """Mark the constellation as started."""

        self._state = ConstellationState.EXECUTING
        self._execution_start_time = datetime.now(timezone.utc)
        self._updated_at = self._execution_start_time

    def complete_execution(self) -> None:
        """Mark the constellation as completed."""
        self._execution_end_time = datetime.now(timezone.utc)
        self._updated_at = self._execution_end_time
        self.update_state()

    def display_dag(self, mode: str = "overview") -> None:
        """
        Manually display the DAG visualization.

        :param mode: Visualization mode ('overview', 'topology', 'details', 'execution')
        """
        try:
            visualizer = DAGVisualizer()

            if mode == "overview":
                visualizer.display_constellation_overview(self)
            elif mode == "topology":
                visualizer.display_dag_topology(self)
            elif mode == "details":
                visualizer.display_task_details(self)
            elif mode == "execution":
                visualizer.display_execution_flow(self)
            else:
                visualizer.display_constellation_overview(self)
        except Exception as e:
            print(f"Visualization error: {e}")

    def __str__(self) -> str:
        """String representation of the TaskConstellation."""
        return f"TaskConstellation(id={self._constellation_id}, tasks={len(self._tasks)}, state={self._state.value})"

    def __repr__(self) -> str:
        """Detailed representation of the TaskConstellation."""
        return (
            f"TaskConstellation(constellation_id={self._constellation_id!r}, "
            f"name={self._name!r}, "
            f"tasks={len(self._tasks)}, "
            f"dependencies={len(self._dependencies)}, "
            f"state={self._state.value!r})"
        )
