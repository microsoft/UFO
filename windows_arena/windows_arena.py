# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import argparse
from datetime import datetime

from ufo.config.config import Config
from ufo.module.client import UFOClientManager
from ufo.module.sessions.session import SessionFactory
import json

configs = Config.get_instance().config_data

args = argparse.ArgumentParser()
args.add_argument(
    "--task",
    "-t",
    help="The name of current task.",
    type=str,
    default=datetime.now().strftime("%Y-%m-%d-%H-%M-%S"),
)
args.add_argument(
    "--mode",
    "-m",
    help="mode of the task. Default is normal, it can be set to 'follower' if you want to run the follower agent. Also, it can be set to 'batch_normal' if you want to run the batch normal agent.",
    type=str,
    default="normal",
)
args.add_argument(
    "--plan",
    "-p",
    help="The path of the plan file or folder. It is only required for the follower mode and batch_normal mode.",
    type=str,
    default="",
)
args.add_argument(
    "--request",
    "-r",
    help="The description of the request, optional. If not provided, UFO will ask the user to input the request.",
    type=str,
    default="",
)
args.add_argument(
    "--agent_settings",
    "-a",
    help="The agent settings.",
    type=str,
    default="",
)

parsed_args = args.parse_args()

def main():
    """
    Main function to run the UFO system.

    To use normal mode, run the following command:
    python -m ufo -t task_name

    To use follower mode that follows a plan file or folder, run the following command:
    python -m ufo -t task_name -m follower -p path_to_plan_file_or_folder

    To use batch mode that follows a plan file or folder, run the following command:
    python -m ufo -t task_name -m batch_normal -p path_to_plan_file_or_folder
    """

    # Set config if agent setting exist.
    if parsed_args.agent_settings is not None and parsed_args.agent_settings != "":
        try:
            agent_settings_json = json.loads(parsed_args.agent_settings)
        except json.JSONDecodeError:
            agent_settings_json = {}
        
        set_config(agent_settings_json)
    
    task_name = agent_settings_json.get("task_name")
    if task_name is not None and task_name != "":
        parsed_args.task = task_name

    sessions = SessionFactory().create_session(
        task=parsed_args.task,
        mode=parsed_args.mode,
        plan=parsed_args.plan,
        request=parsed_args.request,
    )

    clients = UFOClientManager(sessions)
    clients.run_all()

def set_config(agent_settings_json: dict = {}):
    if agent_settings_json is not None and len(agent_settings_json) > 0:
        llm_type = agent_settings_json.get("llm_type")
        llm_endpoint = agent_settings_json.get("llm_endpoint")
        llm_auth = agent_settings_json.get("llm_auth", {})
        auth_type = llm_auth.get("type")
        token = llm_auth.get("token")
        
        if llm_type == "azure" and auth_type == "Identity":
            configs["HOST_AGENT"]["API_TYPE"] = "azure_ad"
            configs["APP_AGENT"]["API_TYPE"] = "azure_ad"
            configs["HOST_AGENT"]["API_BASE"] = llm_endpoint
            configs["APP_AGENT"]["API_BASE"] = llm_endpoint
            configs["BACKUP_AGENT"]["API_BASE"] = llm_endpoint
            configs["BACKUP_AGENT"]["API_BASE"] = llm_endpoint

        elif llm_type == "azure" and auth_type == "api-key":
            configs["HOST_AGENT"]["API_TYPE"] = "aoai"
            configs["HOST_AGENT"]["API_BASE"] = llm_endpoint
            configs["APP_AGENT"]["API_TYPE"] = "aoai"
            configs["APP_AGENT"]["API_BASE"] = llm_endpoint
            configs["BACKUP_AGENT"]["API_TYPE"] = "aoai"
            configs["BACKUP_AGENT"]["API_BASE"] = llm_endpoint
        elif llm_type == "oai":
            configs["HOST_AGENT"]["API_TYPE"] = "openai"
            configs["HOST_AGENT"]["API_BASE"] = "https://api.openai.com/v1"
            configs["APP_AGENT"]["API_TYPE"] = "openai"
            configs["APP_AGENT"]["API_BASE"] = "https://api.openai.com/v1"
            configs["BACKUP_AGENT"]["API_TYPE"] = "openai"
            configs["BACKUP_AGENT"]["API_BASE"] = "https://api.openai.com/v1"

        configs["HOST_AGENT"]["API_KEY"] = token
        configs["APP_AGENT"]["API_KEY"] = token
        configs["BACKUP_AGENT"]["API_KEY"] = token
        configs["HOST_AGENT"]["API_MODEL"] = "gpt-4o"
        configs["APP_AGENT"]["API_MODEL"] = "gpt-4o"
        configs["BACKUP_AGENT"]["API_MODEL"] = "gpt-4o"
        configs["SAVE_EXPERIENCE"] = "always_not"
        configs["MAX_ROUND"] = 1

if __name__ == "__main__":
    main()