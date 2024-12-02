# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import json
import os
import psutil
import time
import win32com.client
from typing import List, Optional

from ufo.config.config import Config

configs = Config.get_instance().config_data


class PlanReader:
    """
    The reader for a plan file.
    """

    def __init__(self, plan_file: str):
        """
        Initialize a plan reader.
        :param plan_file: The path of the plan file.
        """

        self.plan_file = plan_file
        with open(plan_file, "r") as f:
            self.plan = json.load(f)
        self.close = self.plan.get("close", False)
        self.remaining_steps = self.get_steps()

    def get_task(self) -> str:
        """
        Get the task name.
        :return: The task name.
        """

        return self.plan.get("new_problem", "")

    def get_steps(self) -> List[str]:
        """
        Get the steps in the plan.
        :return: The steps in the plan.
        """

        return self.plan.get("steps", [])

    def get_operation_object(self) -> str:
        """
        Get the operation object in the step.
        :return: The operation object.
        """

        return self.plan.get("object", None)

    def get_initial_request(self) -> str:
        """
        Get the initial request in the plan.
        :return: The initial request.
        """

        task = self.get_task()
        object_name = self.get_operation_object()

        request = f"{task} in {object_name}"

        return request

    def get_host_agent_request(self) -> str:
        """
        Get the request for the host agent.
        :return: The request for the host agent.
        """

        object_name = self.get_operation_object()

        request = (
            f"Open and select the application of {object_name}, and output the FINISH status immediately. "
            "You must output the selected application with their control text and label even if it is already open."
        )

        return request

    def get_file_path(self):

        file_path = os.path.dirname(os.path.abspath(self.plan_file)).replace(
            "tasks", "files"
        )
        file = os.path.basename(
            self.plan.get(
                "object",
            )
        )

        return os.path.join(file_path, file)

    def get_app_name(self, object_name: str) -> str:
        """
        Get the application name based on the object name.
        :param object_name: The name of the object.
        :return: The application name.
        """
        application_mapping = {
            ".docx": "WINWORD.EXE",
            ".xlsx": "EXCEL.EXE",
            ".pptx": "POWERPNT.EXE",
            # "outlook": "olk.exe",
            # "onenote": "ONENOTE.EXE",
        }
        self.app_name = application_mapping.get(object_name)
        return self.app_name

    def get_app_com(self, object_name: str) -> str:
        application_mapping = {
            ".docx": "Word.Application",
            ".xlsx": "Excel.Application",
            ".pptx": "PowerPoint.Application",
        }
        self.app_name = application_mapping.get(object_name)
        return self.app_name

    def get_host_request(self) -> str:
        """
        Get the request for the host agent.
        :return: The request for the host agent.
        """

        task = self.get_task()
        object_name = self.get_operation_object()
        if object_name:
            suffix = os.path.splitext(object_name)[1]
            app_name = self.get_app_name(suffix)
            file = self.get_file_path()
            if self.close:
                for process in psutil.process_iter(["name"]):
                    if process.info["name"] == app_name:
                        os.system(f"taskkill /f /im {app_name}")
                        time.sleep(1)
            code_snippet = f"import os\nos.system('start {app_name} \"{file}\"')"
            code_snippet = code_snippet.replace("\\", "\\\\")  # escape backslashes
            try:
                exec(code_snippet, globals())
                time.sleep(3)  # wait for the app to boot
                word_app = win32com.client.Dispatch(suffix)
                word_app.WindowState = 1  # wdWindowStateMaximize

            except Exception as e:
                print(f"An error occurred: {e}", "red")
            request = task

        else:
            if self.close:
                app_names = ["WINWORD.EXE", "EXCEL.EXE", "POWERPNT.EXE"]
                for process in psutil.process_iter(["name"]):
                    if process.info["name"] in app_names:
                        os.system(f"taskkill /f /im {process.info['name']}")
                        time.sleep(1)
            request = f"Open the application of {task}. You must output the selected application with their control text and label even if it is already open."

        return request

    def next_step(self) -> Optional[str]:
        """
        Get the next step in the plan.
        :return: The next step.
        """

        if self.remaining_steps:
            step = self.remaining_steps.pop(0)
            return step

        return None

    def task_finished(self) -> bool:
        """
        Check if the task is finished.
        :return: True if the task is finished, False otherwise.
        """

        return not self.remaining_steps
