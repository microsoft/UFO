# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import json
from typing import Any, Dict, List

from ufo.automator.ui_control.grounding.basic import BasicGrounding
from pywinauto.win32structures import RECT


class OmniparserGrounding(BasicGrounding):
    """
    The OmniparserGrounding class is a subclass of BasicGrounding, which is used to represent the Omniparser grounding model.
    """

    _filter_interactivity = True

    def predict(self, image_path: str) -> str:
        """
        Predict the grounding for the given image.
        :param image_path: The path to the image.
        :return: The predicted grounding results string.
        """
        pass

    def parse_results(self, results: str) -> List[Dict[str, Any]]:
        """
        Parse the grounding results string into a list of control elements infomation dictionaries.
        :param results: The grounding results string from the grounding model.
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

        try:
            control_info_list = json.loads(results)
        except json.JSONDecodeError:
            return []

        control_elements_info = []

        for control_info in control_info_list:

            if self._filter_interactivity and control_info.get("interactivity", True):
                continue

            application_rect: RECT = self.application_window.rectangle()

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
