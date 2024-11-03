# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import argparse
import json
import os

import robin_script_translator, translator

args = argparse.ArgumentParser()
args.add_argument(
    "--task",
    "-t",
    help="The name of current task.",
    type=str,
    default="",
)

parsed_args = args.parse_args()


def main():
    """
    Main function to translate the script from UFO actions to Robin actions.
    """

    task_name = parsed_args.task

    if task_name == "":

        logs_folder = "logs"
        # Get the sub-folder in logs_folder that is latest modified

        task_name = max(
            [
                d
                for d in os.listdir(logs_folder)
                if os.path.isdir(os.path.join(logs_folder, d))
            ],
            key=lambda d: os.path.getmtime(os.path.join(logs_folder, d)),
        )

    if task_name:
        print(f"Translating the script for task: {task_name}")
        action_path = f"logs/{task_name}/response.log"

        action_list = []
        with open(action_path, "r") as file:
            for line in file:
                action_dict = json.loads(line)
                if action_dict.get("Agent") == "AppAgent":
                    action_list.append(action_dict)

        mapper = translator.ActionMapping()
        robin_actions = mapper.batch_robin_action_mapper(action_list)

        robin_actions_string = (
            robin_script_translator.RobinActionSequenceGenerator().generate(
                robin_actions
            )
        )

        save_path = f"logs/{task_name}/robin_script_final.txt"
        with open(save_path, "w") as file:
            file.write(robin_actions_string)

        print(f"Robin script is saved to: {save_path}")


if __name__ == "__main__":
    main()
