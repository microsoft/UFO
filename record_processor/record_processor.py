# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import os
import argparse
from record_processor.summarizer.summarizer import DemonstrationSummarizer
from ufo.config.config import load_config
from .parser.psr_record_parser import PSRRecordParser
from .utils import create_folder, save_to_json, unzip_and_read_file
from ufo.utils import print_with_color

configs = load_config()

args = argparse.ArgumentParser()
args.add_argument("--request", "-r", help="The request that user want to achieve.",
                  type=lambda s: s.strip() or None, nargs='+')
args.add_argument("--behavior-record-path", "-p", help="The path for user behavior record in zip file.",
                  type=lambda f: f if f.endswith(".zip") else None)
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
            configs["ACTION_AGENT"]["VISUAL_MODE"], configs["DEMONSTRATION_PROMPT"], configs["ACTION_SELECTION_EXAMPLE_PROMPT"], configs["API_PROMPT"])

        summaries, total_cost = summarizer.get_summary_list([record])
        if asker(summaries):
            demonstration_path = configs["DEMONSTRATION_SAVED_PATH"]
            create_folder(demonstration_path)

            save_to_json(record.__dict__, os.path.join(demonstration_path, "demonstration_log", parsed_args.request[0].replace(' ', '_')) + ".json")
            summarizer.create_or_update_yaml(summaries, os.path.join(demonstration_path, "demonstration.yaml"))
            summarizer.create_or_update_vector_db(summaries, os.path.join(demonstration_path, "demonstration_db"))

        formatted_cost = '${:.2f}'.format(total_cost)
        print_with_color(f"Request total cost is {formatted_cost}", "yellow")

    except ValueError as e:
        print_with_color(str(e), "red")


def asker(summaries) -> bool:
    plan = summaries[0]["example"]["Plan"]
    print_with_color("""Here's the plan summarized from your demonstration: """, "cyan")
    print_with_color(plan, "green")
    print_with_color("""Would you like to save the plan future reference by the agent?
[Y] for yes, any other key for no.""", "cyan")

    response = input()

    if response.upper() == "Y":
        return True
    else:
        return False
