import os
from typing import Dict, List, Optional, Tuple
import functools
from PIL import Image, ImageDraw, ImageFont, ImageGrab

from ufo.contracts.contracts import AppWindowControlInfo, ControlInfo, WindowInfo


from ufo.config import Config
from ufo.utils import print_with_color

configs = Config.get_instance().config_data

if configs is not None:
    DEFAULT_PNG_COMPRESS_LEVEL = int(configs.get("DEFAULT_PNG_COMPRESS_LEVEL", 0))
else:
    DEFAULT_PNG_COMPRESS_LEVEL = 6


def annotate_app_window_image(
    image: Image.Image,
    app_window_info: WindowInfo,
    controls: list[ControlInfo],
    colors: List[Tuple[int, int, int]] = [(255, 0, 0)],
) -> Image.Image:
    """
    Annotate an image with rectangles and labels.
    :param image: The image to annotate.
    :param app_window_control_info: The AppWindowControlInfo object containing information about the window.
    :param colors: A list of colors for the rectangles.
    :return: The annotated image.
    """
    if not image or not controls:
        return image

    # Create a copy of the image to avoid modifying the original
    annotated_image = image.copy()

    # Draw rectangles and labels for each control
    for i, control in enumerate(controls):
        if not control.rectangle:
            continue

        # Get control rectangle coordinates
        rect = control.rectangle

        # Calculate the coordinates for the rectangle on the image
        rect_coords = (rect.x, rect.y, rect.x + rect.width, rect.y + rect.height)

        # Adjust coordinates to make them relative to the image
        rect_coords = (
            rect_coords[0] - app_window_info.rectangle.x,
            rect_coords[1] - app_window_info.rectangle.y,
            rect_coords[2] - app_window_info.rectangle.x,
            rect_coords[3] - app_window_info.rectangle.y,
        )

        # Get the color for this control (cycle through colors if needed)
        color_idx = i % len(colors) if colors else 0
        color = colors[color_idx] if colors else (255, 0, 0)

        # Draw rectangle around the control
        draw = ImageDraw.Draw(annotated_image)
        draw.rectangle(rect_coords, outline=color, width=3)

        # Create a label for the control
        label_text = str(i + 1)

        # Create and paste a button with the label
        button_img = get_button_img(
            label_text,
            botton_margin=5,
            border_width=2,
            font_size=25,
            font_color="#000000",
            border_color="#FF0000",
            button_color="#FFF68F",
        )

        # Paste the button onto the image at the top-left corner of the control
        annotated_image.paste(button_img, (rect_coords[0], rect_coords[1]), button_img)

    return annotated_image


@functools.lru_cache(maxsize=2048, typed=False)
def get_button_img(
    label_text: str,
    botton_margin: int = 5,
    border_width: int = 2,
    font_size: int = 25,
    font_color: str = "#000000",
    border_color: str = "#FF0000",
    button_color: str = "#FFF68F",
):
    """
    Create a button image with text.
    :param label_text: The text to display on the button.
    :param botton_margin: The margin of the button.
    :param border_width: The width of the border.
    :param font_size: The size of the font.
    :param font_color: The color of the font.
    :param border_color: The color of the border.
    :param button_color: The color of the button.
    :return: The button image.
    """
    font = get_font("arial.ttf", font_size)
    text_size = font.getbbox(label_text)

    # Set button size + margins
    button_size = (text_size[2] + botton_margin, text_size[3] + botton_margin)
    # Create image with correct size and background color
    button_img = Image.new("RGBA", button_size, button_color)
    button_draw = ImageDraw.Draw(button_img)
    button_draw.text(
        (botton_margin / 2, botton_margin / 2),
        label_text,
        font=font,
        fill=font_color,
    )

    # Draw rectangle around button
    ImageDraw.Draw(button_img).rectangle(
        [(0, 0), (button_size[0] - 1, button_size[1] - 1)],
        outline=border_color,
        width=border_width,
    )
    return button_img


@functools.lru_cache(maxsize=64, typed=False)
def get_font(name: str, size: int):
    """
    Get a font with the specified name and size.
    :param name: The name of the font.
    :param size: The size of the font.
    :return: The font.
    """
    try:
        return ImageFont.truetype(name, size)
    except:
        # Fallback to default font if the specified font is not available
        return ImageFont.load_default()


def concat_screenshots(
    image1_path: str, image2_path: str, output_path: str
) -> Image.Image:
    """
    Concatenate two images horizontally.
    :param image1_path: The path of the first image.
    :param image2_path: The path of the second image.
    :param output_path: The path to save the concatenated image.
    :return: The concatenated image.
    """
    # Open the images
    if not os.path.exists(image1_path):
        print_with_color(f"Waring: {image1_path} does not exist.", "yellow")

        return Image.new("RGB", (0, 0))

    if not os.path.exists(image2_path):
        print_with_color(f"Waring: {image2_path} does not exist.", "yellow")

        return Image.new("RGB", (0, 0))

    image1 = Image.open(image1_path)
    image2 = Image.open(image2_path)

    # Ensure both images have the same height
    min_height = min(image1.height, image2.height)
    image1 = image1.crop((0, 0, image1.width, min_height))
    image2 = image2.crop((0, 0, image2.width, min_height))

    # Concatenate images horizontally
    result = Image.new("RGB", (image1.width + image2.width, min_height))
    result.paste(image1, (0, 0))
    result.paste(image2, (image1.width, 0))

    # Save the result
    result.save(output_path, compress_level=DEFAULT_PNG_COMPRESS_LEVEL)

    return result
