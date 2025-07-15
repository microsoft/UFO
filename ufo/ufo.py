# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import argparse
from datetime import datetime
from uuid import uuid4

from ufo.config import Config
from ufo.cs.computer import Computer
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
    help="mode of the task. Default is 'normal', it can be set to 'follower' if you want to run the follower agent. Also, it can be set to 'batch_normal' if you want to run the batch normal agent, 'operator' if you want to run the OpenAi Operator agent separately.",
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
    sessions = SessionFactory().create_session(
        task=parsed_args.task,
        mode=parsed_args.mode,
        plan=parsed_args.plan,
        request=parsed_args.request,
    )

    session = sessions[0]  # Assuming the first session is the one we want to run
    computer = Computer("localhost")
    for _ in session.run_coro:
        actions = session.get_actions()
        action_results = {}
        for action in actions:
            # Run each action and collect the results
            result = computer.run_action(action)
            action_results[action.call_id] = result
        session.process_action_results(action_results)


if __name__ == "__main__":
    main()
