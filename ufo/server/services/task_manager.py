import threading
from itertools import count
from typing import Any


class TaskManager:
    """
    TaskManager is responsible for managing task IDs and their results.
    """

    def __init__(self):
        """
        Initialize the TaskManager.
        This class manages task IDs and their results.
        """
        self.task_results = {}
        self._task_id_counter = count(1)
        self.lock = threading.Lock()

    def new_task_id(self) -> str:
        """
        Generate a new unique task ID.
        :return: A new task ID in the format "task_<number>".
        """
        with self.lock:
            return f"task_{next(self._task_id_counter)}"

    def set_result(self, task_id: str, result: Any) -> None:
        """
        Set the result for a given task ID.
        :param task_id: The ID of the task to set the result for.
        :param result: The result to set for the task.
        """
        with self.lock:
            self.task_results[task_id] = result

    def get_result(self, task_id: str) -> Any:
        """
        Get the result for a given task ID.
        :param task_id: The ID of the task to retrieve the result for.
        :return: The result of the task if available, None otherwise.
        """
        with self.lock:
            return self.task_results.get(task_id)

    def remove_result(self, task_id: str) -> None:
        """
        Remove the result for a given task ID.
        :param task_id: The ID of the task to remove the result for.
        """
        with self.lock:
            self.task_results.pop(task_id, None)

    def handle_result(self, task_id: str, result: Any) -> None:
        """
        Handle the result of a completed task.
        :param task_id: The ID of the completed task.
        :param result: The result of the completed task.
        """
        self.set_result(task_id, result)
