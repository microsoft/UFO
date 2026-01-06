# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import argparse
from datetime import datetime

from ufo.logging.setup import setup_logger

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
args.add_argument(
    "--log-level",
    help="Set logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL). Use OFF to disable logs.",
    type=str,
    default="WARNING",
)


parsed_args = args.parse_args()

# Initialize logger
setup_logger(parsed_args.log_level)


async def main():
    """
    Main function to run the UFO system.

    To use normal mode, run the following command:
    python -m ufo -t task_name

    To use follower mode that follows a plan file or folder, run the following command:
    python -m ufo -t task_name -m follower -p path_to_plan_file_or_folder

    To use batch mode that follows a plan file or folder, run the following command:
    python -m ufo -t task_name -m batch_normal -p path_to_plan_file_or_folder
    """
    from ufo.module.session_pool import SessionFactory, SessionPool

    sessions = SessionFactory().create_session(
        task=parsed_args.task,
        mode=parsed_args.mode,
        plan=parsed_args.plan,
        request=parsed_args.request,
    )

    clients = SessionPool(sessions)
    await clients.run_all()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
