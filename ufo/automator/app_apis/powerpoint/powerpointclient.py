# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import os
from typing import Dict, Type, List

from ufo.automator.app_apis.basic import WinCOMCommand, WinCOMReceiverBasic
from ufo.automator.basic import CommandBasic


class PowerPointWinCOMReceiver(WinCOMReceiverBasic):
    """
    The base class for Windows COM client.
    """

    _command_registry: Dict[str, Type[CommandBasic]] = {}

    def get_object_from_process_name(self) -> None:
        """
        Get the object from the process name.
        :return: The matched object.
        """

        object_name_list = [
            presentation.Name for presentation in self.client.Presentations
        ]
        matched_object = self.app_match(object_name_list)

        for presentation in self.client.Presentations:
            if presentation.Name == matched_object:
                return presentation

        return None

    def set_background_color(self, color: str, slide_index: List[int] = None) -> str:
        """
        Set the background color of the slide(s).
        :param color: The hex color code to set the background color.
        :param slide_index: The list of slide indexes to set the background color. If None, set the background color for all slides.
        :return: The result of setting the background color.
        """

        if not slide_index:
            slide_index = range(1, self.com_object.Slides.Count + 1)

        try:
            for index in slide_index:
                if index < 1 or index > self.com_object.Slides.Count:
                    continue
                slide = self.com_object.Slides(index)
                slide.FollowMasterBackground = False
                slide.FollowMasterBackground = True
                slide.Background.Fill.BackColor.RGB = int(color, 16)
        except Exception as e:
            return f"Failed to set the background color. Error: {e}"

        return f"Successfully Set the background color to {color} for slide(s) {slide_index}."

    def save_as(
        self, file_dir: str = "", file_name: str = "", file_ext: str = ""
    ) -> None:
        """
        Save the document to PDF.
        :param file_dir: The directory to save the file.
        :param file_name: The name of the file without extension.
        :param file_ext: The extension of the file.
        """

        ppt_ext_to_fileformat = {
            ".pptx": 24,  # PowerPoint Presentation (OpenXML)
            ".ppt": 0,  # PowerPoint 97-2003 Presentation
            ".pdf": 32,  # PDF file
            ".xps": 33,  # XPS file
            ".potx": 25,  # PowerPoint Template (OpenXML)
            ".pot": 5,  # PowerPoint 97-2003 Template
            ".ppsx": 27,  # PowerPoint Show (OpenXML)
            ".pps": 1,  # PowerPoint 97-2003 Show
            ".odp": 35,  # OpenDocument Presentation
            ".jpg": 17,  # JPG images (slides exported as .jpg)
            ".png": 18,  # PNG images
            ".gif": 19,  # GIF images
            ".bmp": 20,  # BMP images
            ".tif": 21,  # TIFF images
            ".rtf": 6,  # Outline RTF
            ".html": 12,  # Single File Web Page
            ".mp4": 39,  # MPEG-4 video (requires PowerPoint 2013+)
            ".wmv": 38,  # Windows Media Video
            ".xml": 10,  # PowerPoint 2003 XML Presentation
        }

        if not file_dir:
            file_dir = os.path.dirname(self.com_object.FullName)
        if not file_name:
            file_name = os.path.splitext(os.path.basename(self.com_object.FullName))[0]
        if not file_ext:
            file_ext = ".pdf"

        file_path = os.path.join(file_dir, file_name + file_ext)

        try:
            self.com_object.SaveAs(
                file_path, FileFormat=ppt_ext_to_fileformat.get(file_ext, 17)
            )
            return f"Document is saved to {file_path}."
        except Exception as e:
            return f"Failed to save the document to {file_path}. Error: {e}"

    @property
    def type_name(self):
        return "COM/POWERPOINT"

    @property
    def xml_format_code(self) -> int:
        return 10


@PowerPointWinCOMReceiver.register
class SetBackgroundColorCommand(WinCOMCommand):
    """
    The command to set the background color of the slide(s).
    """

    def execute(self):
        """
        Execute the command to set the background color of the slide(s).
        :return: The result of setting the background color.
        """
        return self.receiver.set_background_color(
            self.params.get("color"), self.params.get("slide_index")
        )

    @classmethod
    def name(cls) -> str:
        """
        The name of the command.
        """
        return "set_background_color"


@PowerPointWinCOMReceiver.register
class SaveAsCommand(WinCOMCommand):
    """
    The command to save the document to PDF.
    """

    def execute(self):
        """
        Execute the command to save the document to PDF.
        :return: The result of saving the document to PDF.
        """
        return self.receiver.save_as(
            self.params.get("file_dir"),
            self.params.get("file_name"),
            self.params.get("file_ext"),
        )

    @classmethod
    def name(cls) -> str:
        """
        The name of the command.
        """
        return "save_as"
