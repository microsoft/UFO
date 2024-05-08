# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import os
import argparse
from .summarizer.summarizer import DemonstrationSummarizer
from ufo.config.config import Config
from .parser.psr_record_parser import PSRRecordParser
from .utils import create_folder, save_to_json, unzip_and_read_file
from ufo.utils import print_with_color
from typing import Tuple


configs = Config.get_instance().config_data

args = argparse.ArgumentParser()
args.add_argument(
    "--request",
    "-r",
    help="The request that user want to achieve.",
    type=lambda s: s.strip() or None,
    nargs="+",
)
args.add_argument(
    "--behavior-record-path",
    "-p",
    help="The path for user behavior record in zip file.",
    type=lambda f: f if f.endswith(".zip") else None,
)
parsed_args = args.parse_args()


def main():
    """
    Main function.
    1. Read the user demonstration record and parse it.
    2. Summarize the demonstration record.
    3. Let user decide whether to save the demonstration record.
    4. Save the demonstration record if user choose to save.
    """
    try:
        content = unzip_and_read_file(parsed_args.behavior_record_path)
        record = PSRRecordParser(content).parse_to_record()
        record.set_request(parsed_args.request[0])

        summarizer = DemonstrationSummarizer(
            configs["APP_AGENT"]["VISUAL_MODE"],
            configs["DEMONSTRATION_PROMPT"],
            configs["APPAGENT_EXAMPLE_PROMPT"],
            configs["API_PROMPT"],
            configs["RAG_DEMONSTRATION_COMPLETION_N"],
        )

        summaries, total_cost = summarizer.get_summary_list(record)

        is_save, index = __asker(summaries)
        if is_save and index >= 0:
            demonstration_path = configs["DEMONSTRATION_SAVED_PATH"]
            create_folder(demonstration_path)

            save_to_json(
                record.__dict__,
                os.path.join(
                    demonstration_path,
                    "demonstration_log",
                    parsed_args.request[0].replace(" ", "_"),
                )
                + ".json",
            )
            summarizer.create_or_update_yaml(
                [summaries[index]],
                os.path.join(demonstration_path, "demonstration.yaml"),
            )
            summarizer.create_or_update_vector_db(
                [summaries[index]], os.path.join(demonstration_path, "demonstration_db")
            )

        formatted_cost = "${:.2f}".format(total_cost)
        print_with_color(f"Request total cost is {formatted_cost}", "yellow")

    except ValueError as e:
        print_with_color(str(e), "red")


def __asker(summaries) -> Tuple[bool, int]:
    print_with_color(
        """Here are the plans summarized from your demonstration: """, "cyan"
    )
    for index, summary in enumerate(summaries):
        print_with_color(f"Plan [{index + 1}]", "green")
        print_with_color(f"{summary['example']['Plan']}", "yellow")

    print_with_color(
        f"Would you like to save any one of them as future reference by the agent? press ",
        color="cyan",
        end="",
    )
    for index in range(1, len(summaries) + 1):
        print_with_color(f"[{index}]", color="cyan", end=" ")
    print_with_color(
        "to save the corresponding plan, or press any other key to skip.", color="cyan"
    )
    response = input()

    if response.isnumeric() and int(response) in range(1, len(summaries) + 1):
        return True, int(response) - 1
    else:
        return False, -1
