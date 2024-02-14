# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from typing import List

from PIL import Image, ImageDraw, ImageFont, ImageGrab
from pywinauto.application import Application
from pywinauto.win32structures import RECT

from ..config.config import load_config
from ..utils import number_to_letter

configs = load_config()

def capture_screenshot(window_title:str, save_path:str, is_save:bool=True):
    """
    Capture a screenshot of the window.
    :param window_title: The title of the window.
    :param save_path: The path to save the screenshot.
    :param is_save: Whether to save the screenshot.
    :return: The screenshot.
    """
    app = Application(backend="uia").connect(title_re=window_title)
    window = app.top_window()
    screenshot = window.capture_as_image()
    if is_save:
        screenshot.save(save_path)
    return screenshot


def capture_screenshot_multiscreen(save_path:str):
    """
    Capture a screenshot of the multi-screen.
    """
    screenshot = ImageGrab.grab(all_screens=True)
    screenshot.save(save_path)
    return screenshot


def draw_rectangles(image, coordinate:tuple, color="red", width=3):
    """
    Draw a rectangle on the image.
    :param image: The image to draw on.
    :param coordinate: The coordinate of the rectangle.
    :param color: The color of the rectangle.
    :param width: The width of the rectangle.
    :return: The image with the rectangle.
    """
    draw = ImageDraw.Draw(image)
    draw.rectangle(coordinate, outline=color, width=width)
    return image

    

def capture_screenshot_controls(top_window, control_list: List, save_path:str, color="red", is_save:bool=True):
    """
    Capture a screenshot with rectangles around the controls.
    :param top_window: The top window.
    :param control_list: The list of the controls to annotate.
    :param save_path: The path to save the screenshot.
    :param color: The color of the rectangle.
    :param is_save: Whether to save the screenshot.
    :return: The screenshot with rectangles around the controls.
    """
    screenshot = top_window.capture_as_image()
    window_rect = top_window.rectangle()
    
    for control in control_list:
        control_rect = control.rectangle()
        adjusted_rect = coordinate_adjusted(window_rect, control_rect)
        screenshot = draw_rectangles(screenshot, adjusted_rect, color=color)
    if is_save:
        screenshot.save(save_path)
    return screenshot



def coordinate_adjusted(window_rect:RECT, control_rect:RECT):
    """
    Adjust the coordinates of the control rectangle to the window rectangle.
    :param window_rect: The window rectangle.
    :param control_rect: The control rectangle.
    :return: The adjusted control rectangle.
    """
    # (left, top, right, bottom)
    adjusted_rect = (control_rect.left - window_rect.left, control_rect.top - window_rect.top, 
                         control_rect.right - window_rect.left, control_rect.bottom - window_rect.top)
    
    return adjusted_rect


def draw_rectangles_controls(image, coordinate:tuple, label_text:str, botton_margin:int=5, border_width:int=2, font_size:int=25, 
                             font_color:str="#000000", border_color:str="#FF0000", button_color:str="#FFF68F"):
    """
    Draw a rectangle around the control and label it.
    :param image: The image to draw on.
    :param save_path: The path to save the screenshot.
    :param coordinate: The coordinate of the control.
    :param label_text: The text label of the control.
    :param botton_margin: The margin of the button.
    :param border_width: The width of the border.
    :param font_size: The size of the font.
    :param font_color: The color of the font.
    :param border_color: The color of the border.
    :param button_color: The color of the button.
    return: The image with the rectangle and label.
    """
    _ = ImageDraw.Draw(image)
    font = ImageFont.truetype("arial.ttf", font_size) 
    text_size = font.getbbox(label_text)
    
    # set button size + margins
    button_size = (text_size[2]+botton_margin, text_size[3]+botton_margin)
    # create image with correct size and black background
    button_img = Image.new('RGBA', button_size, button_color)
    button_draw = ImageDraw.Draw(button_img)
    button_draw.text((botton_margin/2, botton_margin/2), label_text, font=font, fill=font_color)

    # draw red rectangle around button
    ImageDraw.Draw(button_img).rectangle(
        [(0, 0), (button_size[0] - 1, button_size[1] - 1)],
        outline=border_color, width=border_width
    )
    
    # put button on source image
    image.paste(button_img, (coordinate[0], coordinate[1]))
    return image



def control_annotations(window:str, screenshot_save_path:str, annotated_screenshot_save_path:str, control_list:List, anntation_type:str="number", 
                        color_diff:bool=True, color_default:str="#FFF68F", is_save:bool=True):

    """
    Annotate the controls of the window.
    :param window_title: The title of the window.
    :param screenshot_save_path: The path to save the screenshot.
    :param annotated_screenshot_save_path: The path to save the annotated screenshot.
    :param control_list: The list of the controls to annotate.
    :param anntation_type: The type of the annotation, must be number or letter.
    :param color_diff: Whether to use color difference to annotate different control type.
    :param color_default: The default color of the annotation.
    :param is_save: Whether to save the screenshot and annotated screenshot.
    :return: The dictionary of the annotations and the annotated screenshot.
    """

    annotation_dict = {}
    window_rect = window.rectangle()
    screenshot = window.capture_as_image()
    screenshot_annotated = screenshot.copy()

    assert anntation_type in ["number", "letter"], "The annotation type must be number or letter."

    color_dict = configs["ANNOTATION_COLORS"]

    for i, control in enumerate(control_list):
        control_rect = control.rectangle()
        adjusted_rect = coordinate_adjusted(window_rect, control_rect)
        adjusted_coordinate = (adjusted_rect[0], adjusted_rect[1])

        if anntation_type == "number":
            label_text = str(i+1)
            screenshot_annotated = draw_rectangles_controls(screenshot_annotated, adjusted_coordinate, label_text, button_color=color_dict.get(control.element_info.control_type, color_default) if color_diff else color_default)
        elif anntation_type == "letter":
            label_text = number_to_letter(i)
            screenshot_annotated = draw_rectangles_controls(screenshot_annotated, adjusted_coordinate, label_text, button_color=color_dict.get(control.element_info.control_type, color_default) if color_diff else color_default)
        annotation_dict[label_text] = control

    if is_save:
        screenshot.save(screenshot_save_path)
        screenshot_annotated.save(annotated_screenshot_save_path)
    return annotation_dict, screenshot, screenshot_annotated



def concat_images_left_right(image1_path, image2_path, output_path):
    """
    Concatenate two images horizontally.
    :param image1_path: The path of the first image.
    :param image2_path: The path of the second image.
    :param output_path: The path to save the concatenated image.
    :return: The concatenated image.
    """
    # Open the images
    image1 = Image.open(image1_path)
    image2 = Image.open(image2_path)

    # Ensure both images have the same height
    min_height = min(image1.height, image2.height)
    image1 = image1.crop((0, 0, image1.width, min_height))
    image2 = image2.crop((0, 0, image2.width, min_height))

    # Concatenate images horizontally
    result = Image.new('RGB', (image1.width + image2.width, min_height))
    result.paste(image1, (0, 0))
    result.paste(image2, (image1.width, 0))

    # Save the result
    result.save(output_path)
    
    return result
