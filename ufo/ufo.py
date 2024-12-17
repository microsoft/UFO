# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import argparse
from datetime import datetime

from ufo.config.config import Config
from ufo.module.client import UFOClientManager
from ufo.module.sessions.session import SessionFactory

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
    "--instruction",
    "-i",
    help="The payload",
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
args.add_argument(
    "--run_arena",
    "-r",
    help="The payload",
    type=bool,
    default=False,
)

parsed_args = args.parse_args()

from typing import Dict, List
import requests
from uuid import uuid4
import json
import os
import argparse

from ufo.module.sessions.service_session import ServiceSession
from ufo.config.config import Config

session_dir = "sessions"

# if os.path.exists("\\\\host.lan\\Data"):
#     session_dir = f"\\\\host.lan\\Data\\server_outputs\\sessions"

if not os.path.exists(session_dir):
    os.makedirs(session_dir)

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

    if (parsed_args.run_arena):
        run_ufo_session(instruction=parsed_args.instruction, agent_settings=parsed_args.agent_settings)
    else:
        sessions = SessionFactory().create_session(
            task=parsed_args.task,
            mode=parsed_args.mode,
            plan=parsed_args.plan,
            request=parsed_args.request,
        )

        clients = UFOClientManager(sessions)
        clients.run_all()

def run_ufo_session(instruction: str, agent_settings: str = "") -> Dict:
    print("Running UFO session")

    try:
        agent_settings_json = json.loads(agent_settings)
        set_config(agent_settings_json)

        session_id = str(uuid4())
        session = ServiceSession(session_id, configs.get("EVA_SESSION", False), id=0)
        session._request = instruction
        session.run()

        # save the session information to log
        session_info = {
            "session_id": session_id,
            "instruction": instruction,
            "status": "success"
        }

        session_file = os.path.join(session_dir, f"{session_id}.json")
        with open(session_file, "w") as f:
            json.dump(session_info, f)

    except Exception as e:
        print(f"Error running UFO session: {e}")

        # save the session information to log
        session_info = {
            "session_id": session_id,
            "instruction": instruction,
            "status": "error",
            "error": str(e),
        }

        session_file = os.path.join(session_dir, f"{session_id}.json")
        with open(session_file, "w") as f:
            json.dump(session_info, f)

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
            configs["HOST_AGENT"]["API_BASE"] = "https://api.openai.com/v1/chat/completions"
            configs["APP_AGENT"]["API_TYPE"] = "openai"
            configs["APP_AGENT"]["API_BASE"] = "https://api.openai.com/v1/chat/completions"
            configs["BACKUP_AGENT"]["API_TYPE"] = "openai"
            configs["BACKUP_AGENT"]["API_BASE"] = "https://api.openai.com/v1/chat/completions"

        configs["HOST_AGENT"]["API_KEY"] = token
        configs["APP_AGENT"]["API_KEY"] = token
        configs["BACKUP_AGENT"]["API_KEY"] = token
        configs["HOST_AGENT"]["API_MODEL"] = "gpt-4-vision-preview"
        configs["APP_AGENT"]["API_MODEL"] = "gpt-4-vision-preview"
        configs["BACKUP_AGENT"]["API_MODEL"] = "gpt-4-vision-preview"

        print("config seeting" + configs["HOST_AGENT"]["API_TYPE"])
        print("config Key" + configs["HOST_AGENT"]["API_KEY"])
        print("config Endpoint   " + configs["HOST_AGENT"]["API_BASE"])

if __name__ == "__main__":
    main()