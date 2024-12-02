
from typing import Dict, List
import requests
from uuid import uuid4
from ufo.module.sessions.service_session import ServiceSession
from ufo.config.config import Config
import json
import os
import argparse

configs = Config.get_instance().config_data

session_dir = "sessions"

# if os.path.exists("\\\\host.lan\\Data"):
#     session_dir = f"\\\\host.lan\\Data\\server_outputs\\sessions"

if not os.path.exists(session_dir):
    os.makedirs(session_dir)

def run_ufo_session(data: Dict) -> Dict:
    print("Running UFO session")

    try:
        instruction = data.get('instruction', "")
        token = data.get('token', "")

        configs["HOST_AGENT"]["API_TYPE"] = "AOAI"
        configs["APP_AGENT"]["API_TYPE"] = "AOAI"

        configs["HOST_AGENT"]["API_KEY"] = token
        configs["APP_AGENT"]["API_KEY"] = token

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

args = argparse.ArgumentParser()
args.add_argument(
    "--instruction",
    "-i",
    help="The payload",
    type=str,
    default="",
)

parsed_args = args.parse_args()

if __name__ == "__main__":
    run_ufo_session(parsed_args.data)

