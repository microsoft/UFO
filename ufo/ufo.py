# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import argparse
from datetime import datetime

from ufo.config.config import Config
from ufo.module.client import UFOClientManager
from ufo.module.session import SessionFactory

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

parsed_args = args.parse_args()


def main():
    """
    Main function to run the UFO system.

    To use normal mode, run the following command:
    python -m ufo -t task_name

    To use follower mode that follows a plan file or folder, run the following command:
    python -m ufo -t task_name -m follower -p path_to_plan_file_or_folder
    """
    sessions = SessionFactory().create_session(
        task=parsed_args.task, mode=parsed_args.mode, plan=parsed_args.plan
    )

    clients = UFOClientManager(sessions)
    clients.run_all()


if __name__ == "__main__":
    main()
