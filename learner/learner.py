# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import argparse

from learner import indexer

args = argparse.ArgumentParser()
args.add_argument(
    "--app", help="The name of application to learn.", type=str, default="./"
)
args.add_argument(
    "--docs", help="The help application of the app.", type=str, default="./"
)
args.add_argument(
    "--format", help="The format of the help doc.", type=str, default="json"
)
args.add_argument(
    "--incremental", action="store_true", help="Enable incremental update."
)
args.add_argument(
    "--save_path",
    help="The format of the help doc.",
    type=str,
    default="./vectordb/docs/",
)


parsed_args = args.parse_args()


def main():
    """
    Main function.
    """

    indexer.DocumentsIndexer().create_indexer(
        parsed_args.app,
        parsed_args.docs,
        parsed_args.format,
        parsed_args.incremental,
        parsed_args.save_path,
    )


if __name__ == "__main__":
    main()
