# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import importlib
import json
import os

from colorama import Fore, Style, init

# init colorama
init()

def print_with_color(text: str, color: str = "", end: str = "\n"):
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
        "black": Fore.BLACK
    }

    selected_color = color_mapping.get(color.lower(), "")
    colored_text = selected_color + text + Style.RESET_ALL

    print(colored_text, end=end)



def create_folder(folder_path: str):
    """
    Create a folder if it doesn't exist.

    :param folder_path: The path of the folder to create.
    """
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)



def number_to_letter(n:int):
    """
    Convert number to letter.
    :param n: The number to convert.
    :return: The letter converted from the number.
    """
    if n < 0:
        return "Invalid input"
    
    result = ""
    while n >= 0:
        remainder = n % 26
        result = chr(65 + remainder) + result  # 65 is the ASCII code for 'A'
        n = n // 26 - 1
        if n < 0:
            break
    
    return result


def check_json_format(string:str):
    """
    Check if the string can be correctly parse by json.
    :param string: The string to check.
    :return: True if the string can be correctly parse by json, False otherwise.
    """
    import json
    try:
        json.loads(string)
    except ValueError:
        return False
    return True


def json_parser(json_string:str):
    """
    Parse json string to json object.
    :param json_string: The json string to parse.
    :return: The json object.
    """

    # Remove the ```json and ``` at the beginning and end of the string if exists.
    if json_string.startswith("```json"):
        json_string = json_string[7:-3]

    return json.loads(json_string)


def is_json_serializable(obj):
    try:
        json.dumps(obj)
        return True
    except TypeError:
        return False


def revise_line_breaks(args: dict):
    """
    Replace '\\n' with '\n' in the arguments.
    :param args: The arguments.
    :return: The arguments with \\n replaced with \n.
    """
    # Replace \\n with \\n
    for key in args.keys():
        if isinstance(args[key], str):
            args[key] = args[key].replace('\\n', '\n')

    return args


def LazyImport(module_name:str):
    """
    Import a module as a global variable.
    :param module_name: The name of the module to import.
    :return: The imported module.
    """
    global_name = module_name.split(".")[-1]
    globals()[global_name] = importlib.import_module(module_name, __package__)
    return globals()[global_name]

    




