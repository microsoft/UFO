# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
import os
import json
from colorama import Fore, Style, init

# init colorama
init()


def print_with_color(text: str, color: str = ""):
    """
    Print text with specified color using ANSI escape codes from Colorama library.

    :param text: The text to print.
    :param color: The color of the text (options: red, green, yellow, blue, magenta, cyan, white, black).
    """
    color_mapping = {
        "red": Fore.RED,
        "green": Fore.GREEN,
        "yellow": Fore.YELLOW,
        "blue": Fore.BLUE,
        "magenta": Fore.MAGENTA,
        "cyan": Fore.CYAN,
        "white": Fore.WHITE,
        "black": Fore.BLACK,
    }

    selected_color = color_mapping.get(color.lower(), "")
    colored_text = selected_color + text + Style.RESET_ALL

    print(colored_text)


def find_files_with_extension(directory, extension):
    """
    Find files with the given extension in the given directory.
    :param directory: The directory to search.
    :param extension: The extension to search for.
    :return: The list of matching files.
    """
    matching_files = []

    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(extension):
                path = os.path.join(root, file)
                path = os.path.realpath(path)
                matching_files.append(path)

    return matching_files


def find_files_with_extension_list(directory, extensions):
    """
    Find files with the given extensions in the given directory.
    :param directory: The directory to search.
    :param extensions: The list of extensions to search for.
    :return: The list of matching files.
    """
    matching_files = []

    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(tuple(extensions)):
                path = os.path.join(root, file)
                path = os.path.realpath(path)
                matching_files.append(path)

    return matching_files


def load_json_file(file_path):
    """
    Load a JSON file.
    :param file_path: The path to the file to load.
    :return: The loaded JSON data.
    """

    with open(file_path, "r") as file:
        data = json.load(file)
    return data


def save_json_file(file_path, data):
    """
    Save a JSON file.
    :param file_path: The path to the file to save.
    """

    with open(file_path, "w") as file:
        json.dump(data, file, indent=4)


def reformat_json_file(file_path, template_path, data):
    """
    Reformat the JSON file to batch format.
    :param file_path: The path to the file to save.
    """
    tmp_data = {}
    if (
        data.get("instantiation_result", {})
        .get("instantiation_evaluation", {})
        .get("result", {})
        .get("judge", None)
    ):
        tmp_data["task"] = data["instantiation_result"]["prefill"]["result"][
            "instantiated_request"
        ]
        tmp_data["object"] = template_path
        tmp_data["close"] = "True"
        with open(file_path, "w") as file:
            json.dump(tmp_data, file, indent=4)
        return True
    else:
        # The instantiation result is not successful. Need to be filtered out.
        return False
