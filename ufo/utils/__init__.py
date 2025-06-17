# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import base64
import importlib
import functools
from io import BytesIO
import json
import mimetypes
import os
from typing import Optional, Any, Dict, Tuple
from PIL import Image

from colorama import Fore, Style, init

from pywinauto.win32structures import RECT


# init colorama
init()


def print_with_color(text: str, color: str = "", end: str = "\n") -> None:
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

    print(colored_text, end=end)


def create_folder(folder_path: str) -> None:
    """
    Create a folder if it doesn't exist.

    :param folder_path: The path of the folder to create.
    """
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)


def check_json_format(string: str) -> bool:
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


def json_parser(json_string: str) -> Dict[str, Any]:
    """
    Parse json string to json object.
    :param json_string: The json string to parse.
    :return: The json object.
    """

    # Remove the ```json and ``` at the beginning and end of the string if exists.
    if json_string.startswith("```json"):
        json_string = json_string[7:-3]

    return json.loads(json_string)


def is_json_serializable(obj: Any) -> bool:
    """
    Check if the object is json serializable.
    :param obj: The object to check.
    :return: True if the object is json serializable, False otherwise.
    """
    try:
        json.dumps(obj)
        return True
    except TypeError:
        return False


def revise_line_breaks(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Replace '\\n' with '\n' in the arguments.
    :param args: The arguments.
    :return: The arguments with \\n replaced with \n.
    """
    if not args:
        return {}

    # Replace \\n with \\n
    for key in args.keys():
        if isinstance(args[key], str):
            args[key] = args[key].replace("\\n", "\n")

    return args


def LazyImport(module_name: str) -> Any:
    """
    Import a module as a global variable.
    :param module_name: The name of the module to import.
    :return: The imported module.
    """
    global_name = module_name.split(".")[-1]
    globals()[global_name] = importlib.import_module(module_name, __package__)
    return globals()[global_name]


def find_desktop_path() -> Optional[str]:
    """
    Find the desktop path of the user.
    """
    onedrive_path = os.environ.get("OneDrive")
    if onedrive_path:
        onedrive_desktop = os.path.join(onedrive_path, "Desktop")
        if os.path.exists(onedrive_desktop):
            return onedrive_desktop
    # Fallback to the local user desktop
    local_desktop = os.path.join(os.path.expanduser("~"), "Desktop")
    if os.path.exists(local_desktop):
        return local_desktop
    return None


def append_string_to_file(file_path: str, string: str) -> None:
    """
    Append a string to a file.
    :param file_path: The path of the file.
    :param string: The string to append.
    """

    # If the file doesn't exist, create it.
    if not os.path.exists(file_path):
        with open(file_path, "w", encoding="utf-8") as file:
            pass

    # Append the string to the file.
    with open(file_path, "a", encoding="utf-8") as file:
        file.write(string + "\n")


@functools.lru_cache(maxsize=5)
def get_hugginface_embedding(
    model_name: str = "sentence-transformers/all-mpnet-base-v2",
):
    """
    Get the Hugging Face embeddings.
    :param model_name: The name of the model.
    :return: The Hugging Face embeddings.
    """
    from langchain_huggingface import HuggingFaceEmbeddings

    return HuggingFaceEmbeddings(model_name=model_name)


def coordinate_adjusted(window_rect: RECT, control_rect: RECT) -> Tuple:
    """
    Adjust the coordinates of the control rectangle to the window rectangle.
    :param window_rect: The window rectangle.
    :param control_rect: The control rectangle.
    :return: The adjusted control rectangle (left, top, right, bottom), relative to the window rectangle.
    """
    # (left, top, right, bottom)
    adjusted_rect = (
        control_rect.left - window_rect.left,
        control_rect.top - window_rect.top,
        control_rect.right - window_rect.left,
        control_rect.bottom - window_rect.top,
    )

    return adjusted_rect


def coordinate_adjusted_to_relative(window_rect: RECT, control_rect: RECT) -> Tuple:
    """
    Adjust the coordinates of the control rectangle to the window rectangle.
    :param window_rect: The window rectangle.
    :param control_rect: The control rectangle.
    :return: The adjusted control rectangle (left, top, right, bottom), relative to the window rectangle.
    """
    # (left, top, right, bottom)
    width = window_rect.right - window_rect.left
    height = window_rect.bottom - window_rect.top

    relative_rect = (
        float(control_rect.left - window_rect.left) / width,
        float(control_rect.top - window_rect.top) / height,
        float(control_rect.right - window_rect.left) / width,
        float(control_rect.bottom - window_rect.top) / height,
    )

    return relative_rect

def decode_base64_image(base64_string: str) -> bytes:
    """
    Decode a base64 string to bytes.
    :param base64_string: The base64 string to decode.
    :return: The decoded bytes.
    """
    import base64

    # Remove the prefix if it exists
    if base64_string.startswith("data:image/png;base64,"):
        base64_string = base64_string[len("data:image/png;base64,"):]
    
    return base64.b64decode(base64_string)

_empty_image_string = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="

def encode_image_from_path(
        image_path: str, mime_type: Optional[str] = None
    ) -> str:
        """
        Encode an image file to base64 string.
        :param image_path: The path of the image file.
        :param mime_type: The mime type of the image.
        :return: The base64 string.
        """

        # If image path not exist, return an empty image string
        if not os.path.exists(image_path):

            print_with_color(f"Waring: {image_path} does not exist.", "yellow")
            return _empty_image_string

        file_name = os.path.basename(image_path)
        mime_type = (
            mime_type if mime_type is not None else mimetypes.guess_type(file_name)[0]
        )
        with open(image_path, "rb") as image_file:
            encoded_image = base64.b64encode(image_file.read()).decode("ascii")

        if mime_type is None or not mime_type.startswith("image/"):
            print_with_color(
                "Warning: mime_type is not specified or not an image mime type. Defaulting to png.",
                "yellow",
            )
            mime_type = "image/png"

        image_url = f"data:{mime_type};base64," + encoded_image
        return image_url

_empty_image_string = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="

def encode_image(cls, image: Image.Image, mime_type: Optional[str] = None) -> str:
        """
        Encode an image to base64 string.
        :param image: The image to encode.
        :param mime_type: The mime type of the image.
        :return: The base64 string.
        """

        if image is None:
            return _empty_image_string

        buffered = BytesIO()
        image.save(buffered, format="PNG", optimize=True)
        encoded_image = base64.b64encode(buffered.getvalue()).decode("ascii")

        if mime_type is None:
            mime_type = "image/png"

        image_url = f"data:{mime_type};base64," + encoded_image
        return image_url
    
def load_image(image_path: str) -> Image.Image:
    """
    Load an image from the path.
    :param image_path: The path of the image.
    :return: The image.
    """
    return Image.open(image_path)