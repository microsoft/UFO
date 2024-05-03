# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import argparse
from datetime import datetime

from .config.config import Config
from .module.session import SessionFactory
from .module.client import UFOClientManager

configs = Config.get_instance().config_data


args = argparse.ArgumentParser()
args.add_argument("--task", "-t", help="The name of current task.",
                  type=str, default=datetime.now().strftime("%Y-%m-%d-%H-%M-%S"))
args.add_argument("--mode", "-m", help="mode of the task. Default is normal, it can be set to 'follower' if you want to run the follower agent.",
                  type=str, default="normal")
args.add_argument("--plan", "-p", help="The path of the plan file or folder. It is only required for the follower mode.",
                  type=str, default="")

parsed_args = args.parse_args()



def main():
    """
    Main function.
    """
    sessions = SessionFactory().create_session(task=parsed_args.task, mode=parsed_args.mode, plan=parsed_args.plan)

    clients = UFOClientManager(sessions)
    clients.run_all()

  


if __name__ == "__main__":
    main()
