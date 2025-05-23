# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import json
import os
import ast
from typing import Any, Dict, List

from pywinauto.controls.uiawrapper import UIAWrapper
from pywinauto.win32structures import RECT

from ufo.automator.ui_control.grounding.basic import BasicGrounding
from ufo.utils import print_with_color


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
            print_with_color(
                f"Warning: The image path {image_path} does not exist.", "yellow"
            )
            return list_of_grounding_results

        try:
            results = self.service.chat_completion(
                image_path, box_threshold, iou_threshold, use_paddleocr, imgsz, api_name
            )
            grounding_results = results[1].splitlines()

        except Exception as e:
            print_with_color(
                f"Warning: Failed to get grounding results for Omniparser. Error: {e}",
                "yellow",
            )

            return list_of_grounding_results

        for item in grounding_results:
            try:
                item = json.loads(item)
                list_of_grounding_results.append(item)
            except json.JSONDecodeError:
                try:
                    # the item string is a string converted from python's dict
                    item = ast.literal_eval(item[item.index("{"):item.rindex("}") + 1])
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

        if application_window is None:
            application_rect = RECT(0, 0, 0, 0)
        else:
            try:
                application_rect = application_window.rectangle()
            except Exception:
                application_rect = RECT(0, 0, 0, 0)

        for control_info in results:

            if not self._filter_interactivity and control_info.get(
                "interactivity", True
            ):
                continue

            application_left, application_top = (
                application_rect.left,
                application_rect.top,
            )

            control_box = control_info.get("bbox", [0, 0, 0, 0])

            control_left = int(
                application_left + control_box[0] * application_rect.width()
            )
            control_top = int(
                application_top + control_box[1] * application_rect.height()
            )
            control_right = int(
                application_left + control_box[2] * application_rect.width()
            )
            control_bottom = int(
                application_top + control_box[3] * application_rect.height()
            )

            control_elements_info.append(
                {
                    "control_type": control_info.get("type", "Button"),
                    "name": control_info.get("content", ""),
                    "x0": control_left,
                    "y0": control_top,
                    "x1": control_right,
                    "y1": control_bottom,
                }
            )

        return control_elements_info
