# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import base64
import json
import os
from io import BytesIO
from typing import Optional
import importlib

from colorama import Fore, Style, init
from PIL import Image

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
        "black": Fore.BLACK
    }

    selected_color = color_mapping.get(color.lower(), "")
    colored_text = selected_color + text + Style.RESET_ALL

    print(colored_text)



def image_to_base64(image: Image):
    """
    Convert image to base64 string.

    :param image: The image to convert.
    :return: The base64 string.
    """
    buffered = BytesIO()
    image.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode("utf-8")


def encode_image_from_path(image_path: str, mime_type: Optional[str] = None) -> str:
    """
    Encode an image file to base64 string.
    :param image_path: The path of the image file.
    :param mime_type: The mime type of the image.
    :return: The base64 string.
    """
    import mimetypes
    file_name = os.path.basename(image_path)
    mime_type = mime_type if mime_type is not None else mimetypes.guess_type(file_name)[0]
    with open(image_path, "rb") as image_file:
        encoded_image = base64.b64encode(image_file.read()).decode('ascii')
        
    if mime_type is None or not mime_type.startswith("image/"):
        print("Warning: mime_type is not specified or not an image mime type. Defaulting to png.")
        mime_type = "image/png"
        
    image_url = f"data:{mime_type};base64," + encoded_image
    return image_url



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


def yes_or_no():
    """
    Ask for user input until the user enters either Y or N.
    :return: The user input.
    """
    while True:
        user_input = input().upper()

        if user_input == 'Y':
            return True
        elif user_input == 'N':
            return False
        else:
            print("Invalid choice. Please enter either Y or N. Try again.")


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



def generate_function_call(func, args):
    """
    Generate a function call string.
    :param func: The function name.
    :param args: The arguments as a dictionary.
    :return: The function call string.
    """
    # Format the arguments
    args_str = ', '.join(f'{k}={v!r}' for k, v in args.items())

    # Return the function call string
    return f'{func}({args_str})'


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

    




