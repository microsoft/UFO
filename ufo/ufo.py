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
    help="mode of the task. Default is normal, it can be set to 'follower' if you want to run the follower agent.",
    type=str,
    default="normal",
)
args.add_argument(
    "--plan",
    "-p",
    help="The path of the plan file or folder. It is only required for the follower mode.",
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

configs = Config.get_instance().config_data

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
    """

    if (parsed_args.run_arena):
        run_ufo_session(instruction=parsed_args.instruction)
    else:
        sessions = SessionFactory().create_session(
            task=parsed_args.task, mode=parsed_args.mode, plan=parsed_args.plan
        )

        clients = UFOClientManager(sessions)
        clients.run_all()

def run_ufo_session(instruction: str) -> Dict:
    print("Running UFO session")

    try:
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

if __name__ == "__main__":
    run_ufo_session(instruction=parsed_args.instruction)

