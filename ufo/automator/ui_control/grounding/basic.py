# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from abc import ABC, abstractmethod
from typing import Any, Dict, List

from pywinauto.controls.uiawrapper import UIAWrapper
from pywinauto.uia_element_info import UIAElementInfo
from pywinauto.win32structures import RECT

from ufo.llm.base import BaseService


class VirtualUIAElementInfo(UIAElementInfo):
    """
    A virtual UIA element that can be used for testing purposes.
    This class is a subclass of UIAElementInfo, which is used to represent UIA elements in pywinauto.
    """

    def __init__(
        self, control_type: str, name: str, x0: int, y0: int, x1: int, y1: int
    ):
        """Create a virtual UIA element.
        :param control_type: The control type of the element.
        :param name: The name of the element.
        :param x0: The left coordinate of the bounding box.
        :param y0: The top coordinate of the bounding box.
        :param x1: The right coordinate of the bounding box.
        :param y1: The bottom coordinate of the bounding box.
        """
        super().__init__()
        self._control_type = control_type
        self._name = name
        self._automation_id = "VirtualControl"
        self._class_name = "CustomVirtualButton"
        self._parent = None  # No parent, since it's virtual
        self._handle = 0  # No actual window handle

        # Define the rectangle
        self._rect = RECT(x0, y0, x1, y1)

    @property
    def control_type(self):
        """Override the control_type property to return a UIA control type."""
        return "Button"

    @property
    def name(self):
        return self._name

    @property
    def automation_id(self):
        return self._automation_id

    @property
    def class_name(self):
        return self._class_name

    @property
    def rectangle(self):
        """Override the rectangle property to return the bounding box."""
        return self._rect

    @property
    def rectangle(self):
        """Override the rectangle property to return the bounding box."""
        return self._rect


class BasicGrounding(ABC):

    def __init__(self, service: BaseService):
        """
        Create a new BasicGrounding model.
        :param service: The grounding model service.
        """
        self.service = service

    @abstractmethod
    def predict(self, image_path: str) -> str:
        """
        Predict the grounding for the given image.
        :param image_path: The path to the image.
        :return: The predicted grounding results string.
        """
        pass

    @abstractmethod
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
        pass

    def uia_wrapping(self, control_info: Dict[str, Any]) -> UIAWrapper:
        """
        Create a UIAWrapper object from the given control info.
        :param control_info: The control info dictionary.
        :return: The UIAWrapper object.
        """

        elementinfo = VirtualUIAElementInfo(
            control_type=control_info.get("control_type", "Button"),
            name=control_info.get("name", ""),
            x0=control_info.get("x0", 0),
            y0=control_info.get("y0", 0),
            x1=control_info.get("x1", 0),
            y1=control_info.get("y1", 0),
        )

        virtual_control = UIAWrapper(elementinfo)

        return virtual_control

    def convert_to_virtual_uia_elements(
        self, image_path: str, application_window: UIAWrapper = None, *args, **kwargs
    ) -> List[UIAWrapper]:
        """
        Convert the grounding to a UIAWrapper object.
        :param image_path: The path to the image.
        :return: The control elements dictionary.
        """

        control_list = []

        grounding_results = self.predict(image_path, *args, **kwargs)
        control_elements_info = self.parse_results(
            grounding_results, application_window
        )

        for control_info in control_elements_info:
            control_list.append(self.uia_wrapping(control_info))

        return control_list
