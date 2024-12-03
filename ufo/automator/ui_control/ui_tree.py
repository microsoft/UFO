# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from typing import Any, Dict
from ufo.automator.ui_control.screenshot import PhotographerDecorator
from pywinauto.controls.uiawrapper import UIAWrapper
import json
import traceback


class UITree:
    """
    A class to represent the UI tree.
    """

    def __init__(self, root: UIAWrapper):
        """
        Initialize the UI tree with the root element.
        :param root: The root element of the UI tree.
        """
        self.root = root

        try:
            self._ui_tree = self._get_ui_tree(self.root)
        except Exception as e:
            self._ui_tree = {"error": traceback.format_exc()}

    def _get_ui_tree(self, root: UIAWrapper) -> Dict[str, Any]:
        """
        Get the UI tree.
        :param root: The root element of the UI tree.
        """

        adjusted_rect = PhotographerDecorator.coordinate_adjusted(
            self.root.element_info.rectangle, root.element_info.rectangle
        )

        relative_rect = PhotographerDecorator.coordinate_adjusted_to_relative(
            self.root.element_info.rectangle, root.element_info.rectangle
        )

        ui_tree = {
            "name": root.element_info.name,
            "control_type": root.element_info.control_type,
            "rectangle": {
                "left": root.element_info.rectangle.left,
                "top": root.element_info.rectangle.top,
                "right": root.element_info.rectangle.right,
                "bottom": root.element_info.rectangle.bottom,
            },
            "adjusted_rectangle": {
                "left": adjusted_rect[0],
                "top": adjusted_rect[1],
                "right": adjusted_rect[2],
                "bottom": adjusted_rect[3],
            },
            "relative_rectangle": {
                "left": relative_rect[0],
                "top": relative_rect[1],
                "right": relative_rect[2],
                "bottom": relative_rect[3],
            },
            "children": [],
        }

        for child in root.children():
            try:
                ui_tree["children"].append(self._get_ui_tree(child))
            except Exception as e:
                ui_tree["error"] = traceback.format_exc()

        return ui_tree

    @property
    def ui_tree(self):
        """
        The UI tree.
        """
        return self._ui_tree

    def save_ui_tree_to_json(self, file_path: str):
        """
        Save the UI tree to a JSON file.
        :param file_path: The file path to save the UI tree.
        """
        with open(file_path, "w") as file:
            json.dump(self.ui_tree, file, indent=4)
