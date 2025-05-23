# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import base64
import functools
import mimetypes
import os
from abc import ABC, abstractmethod
from io import BytesIO
from typing import Dict, List, Optional, Tuple

from PIL import Image, ImageDraw, ImageFont, ImageGrab
from pywinauto.controls.uiawrapper import UIAWrapper
from pywinauto.win32structures import RECT

from ufo import utils
from ufo.config.config import Config

configs = Config.get_instance().config_data

if configs is not None:
    DEFAULT_PNG_COMPRESS_LEVEL = int(configs.get("DEFAULT_PNG_COMPRESS_LEVEL", 0))
else:
    DEFAULT_PNG_COMPRESS_LEVEL = 6


class Photographer(ABC):
    """
    Abstract class for the photographer.
    """

    @abstractmethod
    def capture(self):
        pass

    @staticmethod
    def rescale_image(image: Image.Image, scaler: List[int]) -> Image.Image:
        """
        Rescale an image.
        :param image: The image to rescale.
        :param scale: The scale factor.
        :return: The rescaled image.
        """

        raw_width, raw_height = image.size
        scale_ratio = min(scaler[0] / raw_width, scaler[1] / raw_height)
        new_width = int(raw_width * scale_ratio)
        new_height = int(raw_height * scale_ratio)

        resized_image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)

        new_image = Image.new("RGB", scaler, (0, 0, 0))
        new_image.paste(
            resized_image,
            (0, 0),
        )

        return new_image


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

    def capture(self, save_path: str = None, scalar: List[int] = None):
        """
        Capture a screenshot.
        :param save_path: The path to save the screenshot.
        :return: The screenshot."""
        # Capture single window screenshot
        screenshot = self.control.capture_as_image()
        if scalar is not None:
            screenshot = self.rescale_image(screenshot, scalar)

        if save_path is not None and screenshot is not None:
            screenshot.save(save_path, compress_level=DEFAULT_PNG_COMPRESS_LEVEL)
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

    def capture(self, save_path: str = None, scalar: List[int] = None):
        """
        Capture a screenshot.
        :param save_path: The path to save the screenshot.
        :return: The screenshot.
        """
        screenshot = ImageGrab.grab(all_screens=self.all_screens)
        if scalar is not None:
            screenshot = self.rescale_image(screenshot, scalar)
        if save_path is not None and screenshot is not None:
            screenshot.save(save_path, compress_level=DEFAULT_PNG_COMPRESS_LEVEL)
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

    @staticmethod
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

    def capture(self, save_path: str, background_screenshot_path: Optional[str] = None):
        """
        Capture a screenshot with rectangles.
        :param save_path: The path to save the screenshot.
        :param background_screenshot_path: The path of the background screenshot, optional. If provided, the rectangle will be drawn on the background screenshot instead of the control screenshot.
        :return: The screenshot with rectangles.
        """

        if background_screenshot_path is not None and os.path.exists(
            background_screenshot_path
        ):
            screenshot = Image.open(background_screenshot_path)
        else:
            screenshot = self.photographer.capture()

        window_rect = self.photographer.control.rectangle()

        for control in self.sub_control_list:
            if control:
                control_rect = control.rectangle()
                adjusted_rect = self.coordinate_adjusted(window_rect, control_rect)
                screenshot = self.draw_rectangles(
                    screenshot, coordinate=adjusted_rect, color=self.color
                )
        if save_path is not None and screenshot is not None:
            screenshot.save(save_path, compress_level=DEFAULT_PNG_COMPRESS_LEVEL)
        return screenshot

    def capture_from_adjusted_coords(
        self,
        control_adjusted_coords: List[Dict[str, Dict[str, float]]],
        save_path: str,
        background_screenshot_path: Optional[str] = None,
    ):
        """
        Capture a screenshot with rectangles when the adjusted coordinates are provided.
        :param control_adjusted_coords: The adjusted coordinates of the control rectangles.
        :param save_path: The path to save the screenshot.
        :param background_screenshot_path: The path of the background screenshot, optional. If provided, the rectangle will be drawn on the background screenshot instead of the control screenshot.
        :return: The screenshot with rectangles.
        """
        if background_screenshot_path is not None and os.path.exists(
            background_screenshot_path
        ):
            screenshot = Image.open(background_screenshot_path)
        else:
            screenshot = self.photographer.capture()

        for control_adjusted_coord in control_adjusted_coords:
            if control_adjusted_coord:
                control_rect = (
                    control_adjusted_coord["left"],
                    control_adjusted_coord["top"],
                    control_adjusted_coord["right"],
                    control_adjusted_coord["bottom"],
                )
                screenshot = self.draw_rectangles(
                    screenshot, coordinate=control_rect, color=self.color
                )
        if save_path is not None and screenshot is not None:
            screenshot.save(save_path, compress_level=DEFAULT_PNG_COMPRESS_LEVEL)
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
        button_img = AnnotationDecorator._get_button_img(
            label_text,
            botton_margin=botton_margin,
            border_width=border_width,
            font_size=font_size,
            font_color=font_color,
            border_color=border_color,
            button_color=button_color,
        )
        # put button on source image
        image.paste(button_img, (coordinate[0], coordinate[1]))
        return image

    @staticmethod
    @functools.lru_cache(maxsize=2048, typed=False)
    def _get_button_img(
        label_text: str,
        botton_margin: int = 5,
        border_width: int = 2,
        font_size: int = 25,
        font_color: str = "#000000",
        border_color: str = "#FF0000",
        button_color: str = "#FFF68F",
    ):
        font = AnnotationDecorator._get_font("arial.ttf", font_size)
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
        return button_img

    @staticmethod
    @functools.lru_cache(maxsize=64, typed=False)
    def _get_font(name: str, size: int):
        return ImageFont.truetype(name, size)

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

        color_dict = configs.get("ANNOTATION_COLORS", {})

        for label_text, control in annotation_dict.items():
            control_rect = control.rectangle()
            adjusted_rect = self.coordinate_adjusted(window_rect, control_rect)
            adjusted_coordinate = (adjusted_rect[0], adjusted_rect[1])
            screenshot_annotated = self.draw_rectangles_controls(
                screenshot_annotated,
                adjusted_coordinate,
                label_text,
                font_size=configs.get("ANNOTATION_FONT_SIZE", 25),
                button_color=(
                    color_dict.get(
                        control.element_info.control_type, self.color_default
                    )
                    if self.color_diff
                    else self.color_default
                ),
            )

        if save_path is not None and screenshot_annotated is not None:
            screenshot_annotated.save(
                save_path, compress_level=DEFAULT_PNG_COMPRESS_LEVEL
            )

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
    """
    The facade class for the photographer.
    """

    _instance = None
    _empty_image_string = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="

    def __new__(cls):
        """
        Singleton pattern.
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.screenshot_factory = PhotographerFactory()
        return cls._instance

    def __init__(self):
        pass

    def capture_app_window_screenshot(
        self, control: UIAWrapper, save_path=None, scalar: List[int] = None
    ):
        """
        Capture the control screenshot.
        :param control: The control item to capture.
        :param save_path: The path to save the screenshot.
        :pram scalar: The scale factor.
        :return: The screenshot.
        """
        screenshot = self.screenshot_factory.create_screenshot("app_window", control)
        return screenshot.capture(save_path, scalar)

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
        background_screenshot_path: Optional[str] = None,
        save_path: Optional[str] = None,
    ) -> Image.Image:
        """
        Capture the control screenshot with a rectangle.
        :param control: The control item to capture.
        :param coordinate: The coordinate of the rectangle.
        :param color: The color of the rectangle.
        :param width: The width of the rectangle.
        :param sub_control_list: The list of the controls to draw rectangles on.
        :param background_screenshot_path: The path of the background screenshot, optional. If provided, the rectangle will be drawn on the background screenshot instead of the control screenshot.
        :param save_path: The path to save the screenshot.
        :return: The screenshot.
        """
        screenshot = self.screenshot_factory.create_screenshot("app_window", control)
        screenshot = RectangleDecorator(screenshot, color, width, sub_control_list)
        return screenshot.capture(save_path, background_screenshot_path)

    def capture_app_window_screenshot_with_rectangle_from_adjusted_coords(
        self,
        control: UIAWrapper,
        color: str = "red",
        width=3,
        control_adjusted_coords: List[Dict[str, Dict[str, float]]] = [],
        background_screenshot_path: Optional[str] = None,
        save_path: Optional[str] = None,
    ) -> Image.Image:
        """
        Capture the control screenshot with a rectangle.
        :param control: The control item to capture.
        :param coordinate: The coordinate of the rectangle.
        :param color: The color of the rectangle.
        :param width: The width of the rectangle.
        :param sub_control_list: The list of the controls to draw rectangles on.
        :param background_screenshot_path: The path of the background screenshot, optional. If provided, the rectangle will be drawn on the background screenshot instead of the control screenshot.
        :param save_path: The path to save the screenshot.
        :return: The screenshot.
        """
        screenshot = self.screenshot_factory.create_screenshot("app_window", control)
        screenshot = RectangleDecorator(screenshot, color, width, [])

        return screenshot.capture_from_adjusted_coords(
            control_adjusted_coords=control_adjusted_coords,
            save_path=save_path,
            background_screenshot_path=background_screenshot_path,
        )

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

    def capture_app_window_screenshot_with_point_from_path(
        self,
        point_list: List[Tuple[int]],
        background_screenshot_path: Optional[str] = None,
        save_path: Optional[str] = None,
        color: str = "red",
        point_radius: int = 5,
    ) -> Image.Image:
        """
        Capture the control screenshot with a rectangle.
        :param point_list: The list of the points to draw on the screenshot.
        :param background_screenshot_path: The path of the background screenshot, optional. If provided, the rectangle will be drawn on the background screenshot instead of the control screenshot.
        :param save_path: The path to save the screenshot.
        :return: The screenshot.
        """
        if not os.path.exists(background_screenshot_path):
            return None

        screenshot = Image.open(background_screenshot_path)
        draw = ImageDraw.Draw(screenshot)
        for point in point_list:
            draw.ellipse(
                (
                    point[0] - point_radius,
                    point[1] - point_radius,
                    point[0] + point_radius,
                    point[1] + point_radius,
                ),
                fill=color,
            )

        if save_path is not None and screenshot is not None:
            screenshot.save(save_path, compress_level=DEFAULT_PNG_COMPRESS_LEVEL)
        return screenshot

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
        if not os.path.exists(image1_path):
            utils.print_with_color(f"Waring: {image1_path} does not exist.", "yellow")

            return Image.new("RGB", (0, 0))

        if not os.path.exists(image2_path):
            utils.print_with_color(f"Waring: {image2_path} does not exist.", "yellow")

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

    @staticmethod
    def load_image(image_path: str) -> Image.Image:
        """
        Load an image from the path.
        :param image_path: The path of the image.
        :return: The image.
        """
        return Image.open(image_path)

    @staticmethod
    def image_to_base64(image: Image.Image) -> str:
        """
        Convert image to base64 string.

        :param image: The image to convert.
        :return: The base64 string.
        """
        buffered = BytesIO()
        image.save(buffered, format="PNG", optimize=True)

        return base64.b64encode(buffered.getvalue()).decode("utf-8")

    @staticmethod
    def control_iou(control1: UIAWrapper, control2: UIAWrapper) -> float:
        """
        Calculate the IOU overlap between two controls.
        :param control1: The first control.
        :param control2: The second control.
        :return: The IOU overlap.
        """
        rect1 = control1.rectangle()
        rect2 = control2.rectangle()

        left = max(rect1.left, rect2.left)
        top = max(rect1.top, rect2.top)
        right = min(rect1.right, rect2.right)
        bottom = min(rect1.bottom, rect2.bottom)

        intersection_area = max(0, right - left) * max(0, bottom - top)
        area1 = (rect1.right - rect1.left) * (rect1.bottom - rect1.top)
        area2 = (rect2.right - rect2.left) * (rect2.bottom - rect2.top)

        iou = intersection_area / (area1 + area2 - intersection_area)

        return iou

    @staticmethod
    def merge_control_list(
        main_control_list: List[Dict[str, UIAWrapper]],
        additional_control_list: List[Dict[str, UIAWrapper]],
        iou_overlap_threshold: float = 0.1,
    ) -> List[Dict[str, UIAWrapper]]:
        """
        Merge two control lists by removing the overlapping controls in the additional control list.
        :param main_control_list: The main control list. All controls in this list will be kept.
        :param additional_control_list: The additional control list. The overlapping controls in this list will be removed.
        :param iou_overlap_threshold: The threshold of the IOU overlap to consider two controls as overlapping.
        :return: The merged control list.
        """
        merged_control_list = main_control_list.copy()

        for additional_control in additional_control_list:
            is_overlapping = False
            for main_control in main_control_list:
                if (
                    PhotographerFacade.control_iou(additional_control, main_control)
                    > iou_overlap_threshold
                ):
                    is_overlapping = True
                    break

            if not is_overlapping:
                merged_control_list.append(additional_control)

        return merged_control_list

    @classmethod
    def encode_image(cls, image: Image.Image, mime_type: Optional[str] = None) -> str:
        """
        Encode an image to base64 string.
        :param image: The image to encode.
        :param mime_type: The mime type of the image.
        :return: The base64 string.
        """

        if image is None:
            return cls._empty_image_string

        buffered = BytesIO()
        image.save(buffered, format="PNG", optimize=True)
        encoded_image = base64.b64encode(buffered.getvalue()).decode("ascii")

        if mime_type is None:
            mime_type = "image/png"

        image_url = f"data:{mime_type};base64," + encoded_image
        return image_url

    @classmethod
    def encode_image_from_path(
        cls, image_path: str, mime_type: Optional[str] = None
    ) -> str:
        """
        Encode an image file to base64 string.
        :param image_path: The path of the image file.
        :param mime_type: The mime type of the image.
        :return: The base64 string.
        """

        # If image path not exist, return an empty image string
        if not os.path.exists(image_path):

            utils.print_with_color(f"Waring: {image_path} does not exist.", "yellow")
            return cls._empty_image_string

        file_name = os.path.basename(image_path)
        mime_type = (
            mime_type if mime_type is not None else mimetypes.guess_type(file_name)[0]
        )
        with open(image_path, "rb") as image_file:
            encoded_image = base64.b64encode(image_file.read()).decode("ascii")

        if mime_type is None or not mime_type.startswith("image/"):
            utils.print_with_color(
                "Warning: mime_type is not specified or not an image mime type. Defaulting to png.",
                "yellow",
            )
            mime_type = "image/png"

        image_url = f"data:{mime_type};base64," + encoded_image
        return image_url
