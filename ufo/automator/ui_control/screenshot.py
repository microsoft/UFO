# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import base64
import mimetypes
import os
from abc import ABC, abstractmethod
from io import BytesIO
from typing import Dict, List, Optional

from PIL import Image, ImageDraw, ImageFont, ImageGrab
from pywinauto.controls.uiawrapper import UIAWrapper
from pywinauto.win32structures import RECT

from ufo.config.config import Config

configs = Config.get_instance().config_data


class Photographer(ABC):
    """
    Abstract class for the photographer.
    """

    @abstractmethod
    def capture(self):
        pass


class ControlPhotographer(Photographer):
    """
    Class to capture the control screenshot.
    """

    def __init__(self, control: UIAWrapper):
        """
        Initialize the ControlPhotographer.
        :param control: The control item to capture.
        """
        self.control = control

    def capture(self, save_path: str = None):
        """
        Capture a screenshot.
        :param save_path: The path to save the screenshot.
        :return: The screenshot."""
        # Capture single window screenshot
        screenshot = self.control.capture_as_image()
        if save_path is not None:
            screenshot.save(save_path)
        return screenshot


class DesktopPhotographer(Photographer):
    """
    Class to capture the desktop screenshot.
    """

    def __init__(self, all_screens=True) -> None:
        """
        Initialize the DesktopPhotographer.
        :param all_screens: Whether to capture all screens.
        """
        self.all_screens = all_screens

    def capture(self, save_path: str = None):
        """
        Capture a screenshot.
        :param save_path: The path to save the screenshot.
        :return: The screenshot.
        """
        screenshot = ImageGrab.grab(all_screens=self.all_screens)
        if save_path is not None:
            screenshot.save(save_path)
        return screenshot


class PhotographerDecorator(Photographer):
    """
    Class to decorate the photographer.
    """

    def __init__(self, photographer: Photographer) -> None:
        """
        Initialize the PhotographerDecorator.
        :param photographer: The photographer.
        """
        self.photographer = photographer

    def capture(self, save_path=None):
        """
        Capture a screenshot.
        :param save_path: The path to save the screenshot.
        :return: The screenshot.
        """
        return self.photographer.capture(save_path)

    @staticmethod
    def coordinate_adjusted(window_rect: RECT, control_rect: RECT):
        """
        Adjust the coordinates of the control rectangle to the window rectangle.
        :param window_rect: The window rectangle.
        :param control_rect: The control rectangle.
        :return: The adjusted control rectangle.
        """
        # (left, top, right, bottom)
        adjusted_rect = (
            control_rect.left - window_rect.left,
            control_rect.top - window_rect.top,
            control_rect.right - window_rect.left,
            control_rect.bottom - window_rect.top,
        )

        return adjusted_rect


class RectangleDecorator(PhotographerDecorator):
    """
    Class to draw rectangles on the screenshot.
    """

    def __init__(
        self,
        photographer: Photographer,
        color: str,
        width: float,
        sub_control_list: List[UIAWrapper],
    ) -> None:
        """
        Initialize the RectangleDecorator.
        :param photographer: The photographer.
        :param coordinate: The coordinate of the rectangle.
        :param color: The color of the rectangle.
        :param width: The width of the rectangle.
        :param sub_control_list: The list of the controls to draw rectangles on.
        """
        super().__init__(photographer)
        self.color = color
        self.width = width
        self.sub_control_list = sub_control_list

    @staticmethod
    def draw_rectangles(
        image: Image.Image, coordinate: tuple, color: str = "red", width: int = 3
    ):
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

    def capture(self, save_path: str):
        """
        Capture a screenshot with rectangles.
        :param save_path: The path to save the screenshot.
        :return: The screenshot with rectangles.
        """
        screenshot = self.photographer.capture()
        window_rect = self.photographer.control.rectangle()

        for control in self.sub_control_list:
            if control:
                control_rect = control.rectangle()
                adjusted_rect = self.coordinate_adjusted(window_rect, control_rect)
                screenshot = self.draw_rectangles(
                    screenshot, coordinate=adjusted_rect, color=self.color
                )
        if save_path is not None:
            screenshot.save(save_path)
        return screenshot


class AnnotationDecorator(PhotographerDecorator):
    """
    Class to annotate the controls on the screenshot.
    """

    def __init__(
        self,
        screenshot: Image.Image,
        sub_control_list: List[UIAWrapper],
        annotation_type: str = "number",
        color_diff: bool = True,
        color_default: str = "#FFF68F",
    ) -> None:
        """
        Initialize the AnnotationDecorator.
        :param screenshot: The screenshot.
        :param sub_control_list: The list of the controls to annotate.
        :param annotation_type: The type of the annotation.
        :param color_diff: Whether to use different colors for different control types.
        :param color_default: The default color of the annotation.
        """
        super().__init__(screenshot)
        self.sub_control_list = sub_control_list
        self.annotation_type = annotation_type
        self.color_diff = color_diff
        self.color_default = color_default

    @staticmethod
    def draw_rectangles_controls(
        image: Image.Image,
        coordinate: tuple,
        label_text: str,
        botton_margin: int = 5,
        border_width: int = 2,
        font_size: int = 25,
        font_color: str = "#000000",
        border_color: str = "#FF0000",
        button_color: str = "#FFF68F",
    ) -> Image.Image:
        """
        Draw a rectangle around the control and label it.
        :param image: The image to draw on.
        :param coordinate: The coordinate of the control.
        :param label_text: The text label of the control.
        :param botton_margin: The margin of the button.
        :param border_width: The width of the border.
        :param font_size: The size of the font.
        :param font_color: The color of the font.
        :param border_color: The color of the border.
        :param button_color: The color of the button.
        return: The image with the control rectangle and label.
        """
        _ = ImageDraw.Draw(image)
        font = ImageFont.truetype("arial.ttf", font_size)
        text_size = font.getbbox(label_text)

        # set button size + margins
        button_size = (text_size[2] + botton_margin, text_size[3] + botton_margin)
        # create image with correct size and black background
        button_img = Image.new("RGBA", button_size, button_color)
        button_draw = ImageDraw.Draw(button_img)
        button_draw.text(
            (botton_margin / 2, botton_margin / 2),
            label_text,
            font=font,
            fill=font_color,
        )

        # draw red rectangle around button
        ImageDraw.Draw(button_img).rectangle(
            [(0, 0), (button_size[0] - 1, button_size[1] - 1)],
            outline=border_color,
            width=border_width,
        )

        # put button on source image
        image.paste(button_img, (coordinate[0], coordinate[1]))
        return image

    @staticmethod
    def number_to_letter(n: int):
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

    def get_annotation_dict(self) -> Dict[str, UIAWrapper]:
        """
        Get the dictionary of the annotations.
        :return: The dictionary of the annotations.
        """
        annotation_dict = {}
        for i, control in enumerate(self.sub_control_list):
            if self.annotation_type == "number":
                label_text = str(i + 1)
            elif self.annotation_type == "letter":
                label_text = self.number_to_letter(i)
            annotation_dict[label_text] = control
        return annotation_dict

    def get_cropped_icons_dict(
        self, annotation_dict: Dict[str, UIAWrapper]
    ) -> Dict[str, Image.Image]:
        """
        Get the dictionary of the cropped icons.
        :return: The dictionary of the cropped icons.
        """
        cropped_icons_dict = {}
        image = self.photographer.capture()
        window_rect = self.photographer.control.rectangle()

        for label_text, control in annotation_dict.items():
            control_rect = control.rectangle()
            cropped_icons_dict[label_text] = image.crop(
                self.coordinate_adjusted(window_rect, control_rect)
            )

        return cropped_icons_dict

    def capture_with_annotation_dict(
        self, annotation_dict: Dict[str, UIAWrapper], save_path: Optional[str] = None
    ):

        window_rect = self.photographer.control.rectangle()
        screenshot_annotated = self.photographer.capture()

        color_dict = configs["ANNOTATION_COLORS"]

        for label_text, control in annotation_dict.items():
            control_rect = control.rectangle()
            adjusted_rect = self.coordinate_adjusted(window_rect, control_rect)
            adjusted_coordinate = (adjusted_rect[0], adjusted_rect[1])
            screenshot_annotated = self.draw_rectangles_controls(
                screenshot_annotated,
                adjusted_coordinate,
                label_text,
                button_color=(
                    color_dict.get(
                        control.element_info.control_type, self.color_default
                    )
                    if self.color_diff
                    else self.color_default
                ),
            )

        if save_path is not None:
            screenshot_annotated.save(save_path)

        return screenshot_annotated

    def capture(self, save_path: Optional[str] = None):
        """
        Capture a screenshot with annotations.
        :param save_path: The path to save the screenshot.
        :return: The screenshot with annotations.
        """

        annotation_dict = self.get_annotation_dict()
        self.capture_with_annotation_dict(annotation_dict, save_path)


class PhotographerFactory:
    @staticmethod
    def create_screenshot(screenshot_type: str, *args, **kwargs):
        """
        Create a screenshot.
        :param screenshot_type: The type of the screenshot.
        :return: The screenshot photographer.
        """
        if screenshot_type == "app_window":
            return ControlPhotographer(*args, **kwargs)
        elif screenshot_type == "desktop_window":
            return DesktopPhotographer(*args, **kwargs)
        else:
            raise ValueError("Invalid screenshot type")


class PhotographerFacade:
    def __init__(self):
        self.screenshot_factory = PhotographerFactory()

    def capture_app_window_screenshot(self, control: UIAWrapper, save_path=None):
        """
        Capture the control screenshot.
        :param control: The control item to capture.
        :return: The screenshot.
        """
        screenshot = self.screenshot_factory.create_screenshot("app_window", control)
        return screenshot.capture(save_path)

    def capture_desktop_screen_screenshot(self, all_screens=True, save_path=None):
        """
        Capture the desktop screenshot.
        :param all_screens: Whether to capture all screens.
        :return: The screenshot.
        """
        screenshot = self.screenshot_factory.create_screenshot(
            "desktop_window", all_screens
        )
        return screenshot.capture(save_path)

    def capture_app_window_screenshot_with_rectangle(
        self,
        control: UIAWrapper,
        color: str = "red",
        width=3,
        sub_control_list: List[UIAWrapper] = None,
        save_path: Optional[str] = None,
    ) -> Image.Image:
        """
        Capture the control screenshot with a rectangle.
        :param control: The control item to capture.
        :param coordinate: The coordinate of the rectangle.
        :param color: The color of the rectangle.
        :param width: The width of the rectangle.
        :param sub_control_list: The list of the controls to draw rectangles on.
        :return: The screenshot.
        """
        screenshot = self.screenshot_factory.create_screenshot("app_window", control)
        screenshot = RectangleDecorator(screenshot, color, width, sub_control_list)
        return screenshot.capture(save_path)

    def capture_app_window_screenshot_with_annotation_dict(
        self,
        control: UIAWrapper,
        annotation_control_dict: Dict[str, UIAWrapper],
        annotation_type: str = "number",
        color_diff: bool = True,
        color_default: str = "#FFF68F",
        save_path: Optional[str] = None,
    ) -> Image.Image:
        """
        Capture the control screenshot with annotations.
        :param control: The control item to capture.
        :param annotation_control_dict: The dictionary of the controls with annotation labels as keys.
        :param annotation_type: The type of the annotation.
        :param color_diff: Whether to use different colors for different control types.
        :param color_default: The default color of the annotation.
        :return: The screenshot.
        """
        screenshot = self.screenshot_factory.create_screenshot("app_window", control)
        sub_control_list = list(annotation_control_dict.values())
        screenshot = AnnotationDecorator(
            screenshot, sub_control_list, annotation_type, color_diff, color_default
        )
        return screenshot.capture_with_annotation_dict(
            annotation_control_dict, save_path
        )

    def capture_app_window_screenshot_with_annotation(
        self,
        control: UIAWrapper,
        sub_control_list: List[UIAWrapper],
        annotation_type: str = "number",
        color_diff: bool = True,
        color_default: str = "#FFF68F",
        save_path: Optional[str] = None,
    ) -> Image.Image:
        """
        Capture the control screenshot with annotations.
        :param control: The control item to capture.
        :param sub_control_list: The list of the controls to annotate.
        :param annotation_type: The type of the annotation.
        :param color_diff: Whether to use different colors for different control types.
        :param color_default: The default color of the annotation.
        :param filtered_control_info: The list of the filtered control info.
        :return: The screenshot.
        """
        screenshot = self.screenshot_factory.create_screenshot("app_window", control)
        screenshot = AnnotationDecorator(
            screenshot, sub_control_list, annotation_type, color_diff, color_default
        )
        return screenshot.capture(save_path)

    def get_annotation_dict(
        self,
        control: UIAWrapper,
        sub_control_list: List[UIAWrapper],
        annotation_type: str = "number",
    ) -> Dict[str, UIAWrapper]:
        """
        Get the dictionary of the annotations.
        :param control: The control item to capture.
        :param sub_control_list: The list of the controls to annotate.
        :param annotation_type: The type of the annotation.
        :return: The dictionary of the annotations.
        """

        screenshot = self.screenshot_factory.create_screenshot("app_window", control)
        screenshot = AnnotationDecorator(screenshot, sub_control_list, annotation_type)
        return screenshot.get_annotation_dict()

    def get_cropped_icons_dict(
        self, control: UIAWrapper, annotation_dict: Dict[str, UIAWrapper]
    ) -> Dict[str, Image.Image]:
        """
        Get the dictionary of the cropped icons.
        :param control: The control item to capture.
        :param sub_control_list: The list of the controls to annotate.
        :param annotation_type: The type of the annotation.
        :return: The dictionary of the cropped icons.
        """

        screenshot = self.screenshot_factory.create_screenshot("app_window", control)
        screenshot = AnnotationDecorator(screenshot, sub_control_list=[])
        return screenshot.get_cropped_icons_dict(annotation_dict)

    @staticmethod
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
        result.save(output_path)

        return result

    @staticmethod
    def image_to_base64(image: Image.Image) -> str:
        """
        Convert image to base64 string.

        :param image: The image to convert.
        :return: The base64 string.
        """
        buffered = BytesIO()
        image.save(buffered, format="PNG")
        return base64.b64encode(buffered.getvalue()).decode("utf-8")

    @staticmethod
    def encode_image_from_path(image_path: str, mime_type: Optional[str] = None) -> str:
        """
        Encode an image file to base64 string.
        :param image_path: The path of the image file.
        :param mime_type: The mime type of the image.
        :return: The base64 string.
        """

        file_name = os.path.basename(image_path)
        mime_type = (
            mime_type if mime_type is not None else mimetypes.guess_type(file_name)[0]
        )
        with open(image_path, "rb") as image_file:
            encoded_image = base64.b64encode(image_file.read()).decode("ascii")

        if mime_type is None or not mime_type.startswith("image/"):
            print(
                "Warning: mime_type is not specified or not an image mime type. Defaulting to png."
            )
            mime_type = "image/png"

        image_url = f"data:{mime_type};base64," + encoded_image
        return image_url
