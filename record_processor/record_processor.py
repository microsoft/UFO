# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import argparse
from .parser.psr_record_parser import PSRRecordParser
from .utils import save_to_json, unzip_and_read_file
from ufo.utils import print_with_color
import os

args = argparse.ArgumentParser()
args.add_argument("--request", "-r", help="The request that user want to achieve.",
                  type=lambda s: s.strip() or None, nargs='+')
args.add_argument("--behavior-record-path", "-p", help="The path for user behavior record in zip file.",
                  type=lambda f: f if f.endswith(".zip") else None)
parsed_args = args.parse_args()


def main():
    """
    Main function.
    """

    # Temporarily hardcode the output file path, will move to a config file later
    output_file = '{prefix}\\vectordb\\records\\log\\{file_name}.json'.format(
        prefix=os.getcwd(),
        file_name=parsed_args.request[0].replace(' ', '_')
    )
    try:
        content = unzip_and_read_file(parsed_args.behavior_record_path)
        record = PSRRecordParser(content).parse_to_record()
        record.set_request(parsed_args.request[0])
        save_to_json(record.__dict__, output_file)
        print_with_color(
            f"Record process successfully. The record is saved to {output_file}.", "green")
    except ValueError as e:
        print_with_color(str(e), "red")
