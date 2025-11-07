# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import json
import logging
import os
import ast
import platform
from typing import Any, Dict, List, TYPE_CHECKING

# Conditional imports for Windows-specific packages
if TYPE_CHECKING or platform.system() == "Windows":
    from pywinauto.controls.uiawrapper import UIAWrapper
    from pywinauto.win32structures import RECT
else:
    UIAWrapper = Any
    RECT = Any

from ufo.agents.processors.schemas.target import TargetInfo, TargetKind
from ufo.automator.ui_control.grounding.basic import BasicGrounding

logger = logging.getLogger(__name__)


class OmniparserGrounding(BasicGrounding):
    """
    The OmniparserGrounding class is a subclass of BasicGrounding, which is used to represent the Omniparser grounding model.
    """

    _filter_interactivity = True

    def predict(
        self,
        image_path: str,
        box_threshold: float = 0.05,
        iou_threshold: float = 0.1,
        use_paddleocr: bool = True,
        imgsz: int = 640,
        api_name: str = "/process",
    ) -> List[Dict[str, Any]]:
        """
        Predict the grounding for the given image.
        :param image_path: The path to the image.
        :param box_threshold: The threshold for the bounding box.
        :param iou_threshold: The threshold for the intersection over union.
        :param use_paddleocr: Whether to use paddleocr.
        :param imgsz: The image size.
        :param api_name: The name of the API.
        :return: The predicted grounding results string.
        """

        list_of_grounding_results = []

        if not os.path.exists(image_path):
            logger.warning(f"The image path {image_path} does not exist.")
            return list_of_grounding_results

        try:
            results = self.service.chat_completion(
                image_path, box_threshold, iou_threshold, use_paddleocr, imgsz, api_name
            )
            grounding_results = results[1].splitlines()

        except Exception as e:
            logger.warning(
                f"Failed to get grounding results for Omniparser. Error: {e}"
            )

            return list_of_grounding_results

        for item in grounding_results:
            try:
                item = json.loads(item)
                list_of_grounding_results.append(item)
            except json.JSONDecodeError:
                try:
                    # the item string is a string converted from python's dict
                    item = ast.literal_eval(
                        item[item.index("{") : item.rindex("}") + 1]
                    )
                    list_of_grounding_results.append(item)
                except Exception:
                    pass

        return list_of_grounding_results

    def parse_results(
        self, results: List[Dict[str, Any]], application_window: UIAWrapper = None
    ) -> List[Dict[str, Any]]:
        """
        Parse the grounding results string into a list of control elements infomation dictionaries.
        :param results: The list of grounding results dictionaries from the grounding model.
        :param application_window: The application window to get the absolute coordinates.
        :return: The list of control elements information dictionaries, the dictionary should contain the following keys:
        {
            "control_type": The control type of the element,
            "name": The name of the element,
            "x0": The absolute left coordinate of the bounding box in integer,
            "y0": The absolute top coordinate of the bounding box in integer,
            "x1": The absolute right coordinate of the bounding box in integer,
            "y1": The absolute bottom coordinate of the bounding box in integer,
        }
        """
        control_elements_info = []

        # Get application rectangle coordinates from UIAWrapper
        app_left, app_top, app_width, app_height = self._get_application_rect_from_uia(
            application_window
        )

        for control_info in results:
            control_element = self._calculate_absolute_coordinates(
                control_info, app_left, app_top, app_width, app_height
            )
            if control_element is not None:
                control_elements_info.append(control_element)

        return control_elements_info

        return control_elements_info

    def _get_application_rect_from_uia(
        self, application_window: UIAWrapper = None
    ) -> tuple:
        """
        Extract application rectangle coordinates from UIAWrapper.
        :param application_window: The application window UIAWrapper
        :return: Tuple of (left, top, width, height)
        """
        if application_window is None:
            return (0, 0, 0, 0)

        try:
            rect = application_window.rectangle()
            return (rect.left, rect.top, rect.width(), rect.height())
        except Exception:
            return (0, 0, 0, 0)

    def _get_application_rect_from_target_info(
        self, application_window_info: TargetInfo = None
    ) -> tuple:
        """
        Extract application rectangle coordinates from TargetInfo.
        :param application_window_info: The application window TargetInfo
        :return: Tuple of (left, top, width, height)
        """
        if application_window_info is None or not application_window_info.rect:
            return (0, 0, 0, 0)

        rect = application_window_info.rect
        if len(rect) >= 4:
            # TargetInfo.rect is [left, top, right, bottom]
            left, top, right, bottom = rect[0], rect[1], rect[2], rect[3]
            width = right - left
            height = bottom - top
            return (left, top, width, height)
        else:
            return (0, 0, 0, 0)

    def _calculate_absolute_coordinates(
        self,
        control_info: Dict[str, Any],
        app_left: int,
        app_top: int,
        app_width: int,
        app_height: int,
    ) -> Dict[str, Any]:
        """
        Calculate absolute coordinates for a control based on relative bbox and application window.
        :param control_info: Control information dictionary with bbox
        :param app_left: Application window left coordinate
        :param app_top: Application window top coordinate
        :param app_width: Application window width
        :param app_height: Application window height
        :return: Dictionary with control information including absolute coordinates
        """
        # Skip if interactivity filter is enabled and control is not interactive
        if self._filter_interactivity and not control_info.get("interactivity", True):
            return None

        control_box = control_info.get("bbox", [0, 0, 0, 0])

        control_left = int(app_left + control_box[0] * app_width)
        control_top = int(app_top + control_box[1] * app_height)
        control_right = int(app_left + control_box[2] * app_width)
        control_bottom = int(app_top + control_box[3] * app_height)

        return {
            "control_type": control_info.get("type", "Button"),
            "name": control_info.get("content", ""),
            "x0": control_left,
            "y0": control_top,
            "x1": control_right,
            "y1": control_bottom,
        }

    def screen_parsing(
        self,
        screenshot_path: str,
        application_window_info: TargetInfo = None,
    ) -> List[TargetInfo]:
        """
        Parse the grounding results using TargetInfo for application window information.
        :param application_window_info: The application window TargetInfo.
        :return: The list of control elements information dictionaries.
        """
        results = self.predict(screenshot_path)

        control_elements_info = []

        # Get application rectangle coordinates from TargetInfo
        app_left, app_top, app_width, app_height = (
            self._get_application_rect_from_target_info(application_window_info)
        )

        for control_info in results:
            control_element = self._calculate_absolute_coordinates(
                control_info, app_left, app_top, app_width, app_height
            )
            if control_element is not None:
                control_elements_info.append(
                    TargetInfo(
                        kind=TargetKind.CONTROL,
                        type=control_element.get("control_type", "Button"),
                        name=control_element.get("name", ""),
                        rect=(
                            control_element.get("x0", 0),
                            control_element.get("y0", 0),
                            control_element.get("x1", 0),
                            control_element.get("y1", 0),
                        ),
                    )
                )

        return control_elements_info
