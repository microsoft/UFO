#!/usr/bin/env python3
"""
Simplified DAG visualization test without full dependencies.
"""

import sys
import os
from datetime import datetime
from typing import Dict, Any, Optional

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, project_root)

# Import real enums from Galaxy framework
from galaxy.constellation.enums import (
    TaskStatus,
    ConstellationState,
    DependencyType,
)


class TaskStar:
    def __init__(self, task_id: str, description: str):
        self.task_id = task_id
        self.description = description
        self.name = task_id  # Add name attribute for compatibility
        self.status = TaskStatus.PENDING
        self.priority = 1  # Add priority attribute for compatibility

    def mark_completed(self):
        self.status = TaskStatus.COMPLETED

    def mark_failed(self):
        self.status = TaskStatus.FAILED

    def to_dict(self):
        return {
            "task_id": self.task_id,
            "description": self.description,
            "status": self.status,
        }


class TaskStarLine:
    def __init__(
        self, source_task_id: str, target_task_id: str, dependency_id: str = None
    ):
        self.source_task_id = source_task_id
        self.target_task_id = target_task_id
        self.from_task_id = source_task_id  # Add for compatibility
        self.to_task_id = target_task_id  # Add for compatibility
        self.dependency_type = DependencyType.SUCCESS_ONLY  # Add for compatibility
        self.is_satisfied = True  # Add for compatibility
        self.dependency_id = (
            dependency_id or f"dep_{source_task_id}_to_{target_task_id}"
        )

    def to_dict(self):
        return {
            "dependency_id": self.dependency_id,
            "source_task_id": self.source_task_id,
            "target_task_id": self.target_task_id,
        }


# Simple TaskConstellation for testing
class SimpleTaskConstellation:
    def __init__(
        self,
        constellation_id: str = None,
        name: str = None,
        enable_visualization: bool = True,
    ):
        self.constellation_id = (
            constellation_id
            or f"test_constellation_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )
        self.name = name or self.constellation_id
        self.state = ConstellationState.CREATED

        self._tasks: Dict[str, TaskStar] = {}
        self._dependencies: Dict[str, TaskStarLine] = {}

        self._created_at = datetime.now()
        self._updated_at = self._created_at
        self._execution_start_time: Optional[datetime] = None
        self._execution_end_time: Optional[datetime] = None

        self._enable_visualization = enable_visualization
        self._visualizer = None

        if enable_visualization:
            try:
                from galaxy.visualization.dag_visualizer import DAGVisualizer

                self._visualizer = DAGVisualizer()
                print("✅ DAG visualizer loaded successfully")
            except ImportError as e:
                print(f"❌ Could not import DAGVisualizer: {e}")
                self._enable_visualization = False

    @property
    def tasks(self):
        return self._tasks.copy()

    @property
    def dependencies(self):
        return self._dependencies.copy()

    @property
    def task_count(self):
        return len(self._tasks)

    @property
    def dependency_count(self):
        return len(self._dependencies)

    @property
    def created_at(self):
        return self._created_at

    @property
    def updated_at(self):
        return self._updated_at

    @property
    def execution_start_time(self):
        return self._execution_start_time

    @property
    def execution_end_time(self):
        return self._execution_end_time

    @property
    def execution_duration(self):
        if self._execution_start_time and self._execution_end_time:
            return (
                self._execution_end_time - self._execution_start_time
            ).total_seconds()
        return None

    def _visualize_dag(self, action: str = "update"):
        """Visualize the DAG if visualization is enabled."""
        if self._enable_visualization and self._visualizer:
            try:
                print(f"\n🎨 Visualizing DAG after {action}:")
                self._visualizer.display_constellation_overview(self)
                return True
            except Exception as e:
                print(f"❌ Visualization error: {e}")
                return False
        return False

    def add_task(self, task: TaskStar) -> bool:
        if task.task_id in self._tasks:
            raise ValueError(f"Task with ID '{task.task_id}' already exists")

        self._tasks[task.task_id] = task
        self._updated_at = datetime.now()

        print(f"➕ Added task: {task.task_id} - {task.description}")
        self._visualize_dag("add_task")
        return True

    def add_dependency(self, dependency: TaskStarLine) -> bool:
        if dependency.source_task_id not in self._tasks:
            raise ValueError(
                f"Source task '{dependency.source_task_id}' does not exist"
            )
        if dependency.target_task_id not in self._tasks:
            raise ValueError(
                f"Target task '{dependency.target_task_id}' does not exist"
            )

        self._dependencies[dependency.dependency_id] = dependency
        self._updated_at = datetime.now()

        print(
            f"🔗 Added dependency: {dependency.source_task_id} → {dependency.target_task_id}"
        )
        self._visualize_dag("add_dependency")
        return True

    def mark_task_completed(self, task_id: str, success: bool = True) -> bool:
        if task_id not in self._tasks:
            raise ValueError(f"Task with ID '{task_id}' does not exist")

        task = self._tasks[task_id]
        if success:
            task.mark_completed()
            print(f"✅ Task completed: {task_id}")
        else:
            task.mark_failed()
            print(f"❌ Task failed: {task_id}")

        self._updated_at = datetime.now()
        self._visualize_dag("task_completed")
        return True

    def start_execution(self):
        self.state = ConstellationState.EXECUTING
        self._execution_start_time = datetime.now()
        print(f"🚀 Starting execution of constellation: {self.name}")
        self._visualize_dag("start_execution")

    def complete_execution(self, success: bool = True):
        self.state = ConstellationState.COMPLETED
        self._execution_end_time = datetime.now()

        status = "successfully" if success else "with failures"
        print(f"🏁 Completed execution {status}")
        self._visualize_dag("complete_execution")

    def get_all_tasks(self):
        """Return all tasks in the constellation."""
        return list(self._tasks.values())

    def get_all_dependencies(self):
        """Return all dependencies in the constellation."""
        return list(self._dependencies.values())

    def get_statistics(self):
        """Return constellation statistics."""
        total_tasks = len(self._tasks)
        completed_tasks = sum(
            1 for task in self._tasks.values() if task.status == TaskStatus.COMPLETED
        )
        failed_tasks = sum(
            1 for task in self._tasks.values() if task.status == TaskStatus.FAILED
        )
        pending_tasks = sum(
            1 for task in self._tasks.values() if task.status == TaskStatus.PENDING
        )
        running_tasks = sum(
            1 for task in self._tasks.values() if task.status == TaskStatus.RUNNING
        )
        ready_tasks = len(self.get_ready_tasks())

        # Calculate success rate
        success_rate = None
        if completed_tasks + failed_tasks > 0:
            success_rate = completed_tasks / (completed_tasks + failed_tasks)

        return {
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "failed_tasks": failed_tasks,
            "pending_tasks": pending_tasks,
            "running_tasks": running_tasks,
            "ready_tasks": ready_tasks,
            "total_dependencies": len(self._dependencies),
            "constellation_state": self.state,
            "execution_start_time": self._execution_start_time,
            "execution_end_time": self._execution_end_time,
            "success_rate": success_rate,
        }

    def get_ready_tasks(self):
        """Return tasks that are ready to execute (no pending dependencies)."""
        ready_tasks = []
        for task in self._tasks.values():
            if task.status == TaskStatus.PENDING:
                # Check if all dependencies are satisfied
                task_dependencies = [
                    dep
                    for dep in self._dependencies.values()
                    if dep.target_task_id == task.task_id
                ]

                if not task_dependencies:  # No dependencies - ready to run
                    ready_tasks.append(task)
                else:
                    # Check if all dependency tasks are completed
                    all_deps_completed = all(
                        self._tasks[dep.source_task_id].status == TaskStatus.COMPLETED
                        for dep in task_dependencies
                    )
                    if all_deps_completed:
                        ready_tasks.append(task)

        return ready_tasks

    def get_task_dependencies(self, task_id: str):
        """Get dependencies for a specific task."""
        return [dep for dep in self._dependencies.values() if dep.to_task_id == task_id]

    def get_task(self, task_id: str):
        """Get a task by ID."""
        return self._tasks.get(task_id)


def test_dag_visualization():
    """Test the DAG visualization functionality."""
    print("🧪 Testing DAG Visualization")
    print("=" * 50)

    # Create constellation
    constellation = SimpleTaskConstellation(
        name="Data Processing Pipeline", enable_visualization=True
    )

    if not constellation._visualizer:
        print("❌ Visualization not available, skipping test")
        return

    # Create tasks
    tasks = [
        TaskStar("extract", "Extract data from source"),
        TaskStar("validate", "Validate extracted data"),
        TaskStar("transform", "Transform data format"),
        TaskStar("load_staging", "Load to staging area"),
        TaskStar("quality_check", "Run quality checks"),
        TaskStar("load_prod", "Load to production"),
    ]

    # Add tasks to constellation
    print("\n📋 Adding tasks...")
    for task in tasks:
        constellation.add_task(task)

    # Add dependencies to create a pipeline
    print("\n🔗 Adding dependencies...")
    dependencies = [
        TaskStarLine("extract", "validate"),
        TaskStarLine("validate", "transform"),
        TaskStarLine("transform", "load_staging"),
        TaskStarLine("load_staging", "quality_check"),
        TaskStarLine("quality_check", "load_prod"),
    ]

    for dep in dependencies:
        constellation.add_dependency(dep)

    # Start execution
    print("\n🚀 Starting execution...")
    constellation.start_execution()

    # Simulate task completion
    print("\n⚙️ Simulating task execution...")
    for task_id in [
        "extract",
        "validate",
        "transform",
        "load_staging",
        "quality_check",
    ]:
        constellation.mark_task_completed(task_id, success=True)

    # Complete the pipeline
    constellation.mark_task_completed("load_prod", success=True)
    constellation.complete_execution(success=True)

    print("\n✅ DAG visualization test completed!")


if __name__ == "__main__":
    test_dag_visualization()
