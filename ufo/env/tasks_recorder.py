"""The class to record tasks and states."""
import os
import json
from ..config.config import load_config
import datetime

configs = load_config()

tasks_dir = configs['TASKS_HUB']

class TaskRecorder:
    def __init__(self,app_name):
        self.app_name = app_name
        if not os.path.exists(tasks_dir):
            os.makedirs(tasks_dir,exist_ok=True)
        self.app_task_dir = os.path.join(tasks_dir,self.app_name)
        if not os.path.exists(self.app_task_dir):
            os.makedirs(self.app_task_dir,exist_ok=True)
    def record_task(self,history_actions,history_states,init_state,task_description):
        """
        Record the task to the json file.
        :param path: The json file path to save the task.
        """

        # set the name with time and task description
        task_name = f"{datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}-{task_description[:10]}" 
        task_path = os.path.join(self.app_task_dir,task_name)
        task_json = {
            "init_state":init_state,
            "history_actions":history_actions,
            "history_states":history_states,
            "task_description":task_description
        }
        open(task_path,"w").write(json.dumps(task_json))
    
            