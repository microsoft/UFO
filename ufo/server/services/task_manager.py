import threading
from itertools import count


class TaskManager:
    def __init__(self):
        self.task_results = {}
        self._task_id_counter = count(1)
        self.lock = threading.Lock()

    def new_task_id(self):
        with self.lock:
            return f"task_{next(self._task_id_counter)}"

    def set_result(self, task_id, result):
        with self.lock:
            self.task_results[task_id] = result

    def get_result(self, task_id):
        with self.lock:
            return self.task_results.get(task_id)

    def remove_result(self, task_id):
        with self.lock:
            self.task_results.pop(task_id, None)
