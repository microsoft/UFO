# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import os
from typing import Dict, Type

from ufo.automator.app_apis.basic import WinCOMCommand, WinCOMReceiverBasic
from ufo.automator.basic import CommandBasic


class WordWinCOMReceiver(WinCOMReceiverBasic):
    """
    The base class for Windows COM client.
    """

    _command_registry: Dict[str, Type[CommandBasic]] = {}

    def get_object_from_process_name(self) -> None:
        """
        Get the object from the process name.
        :return: The matched object.
        """
        object_name_list = [doc.Name for doc in self.client.Documents]
        matched_object = self.app_match(object_name_list)

        for doc in self.client.Documents:
            if doc.Name == matched_object:
                return doc

        return None

    def insert_table(self, rows: int, columns: int) -> object:
        """
        Insert a table at the end of the document.
        :param rows: The number of rows.
        :param columns: The number of columns.
        :return: The inserted table.
        """

        # Get the range at the end of the document
        end_range = self.com_object.Range()
        end_range.Collapse(0)  # Collapse the range to the end

        # Insert a paragraph break (optional)
        end_range.InsertParagraphAfter()
        table = self.com_object.Tables.Add(end_range, rows, columns)
        table.Borders.Enable = True

        return table

    def select_text(self, text: str) -> None:
        """
        Select the text in the document.
        :param text: The text to be selected.
        """
        finder = self.com_object.Range().Find
        finder.Text = text

        if finder.Execute():
            finder.Parent.Select()
            return f"Text {text} is selected."
        else:
            return f"Text {text} is not found."

    def select_paragraph(
        self, start_index: int, end_index: int, non_empty: bool = True
    ) -> None:
        """
        Select a paragraph in the document.
        :param start_index: The start index of the paragraph.
        :param end_index: The end index of the paragraph, if ==-1, select to the end of the document.
        :param non_empty: Whether to select the non-empty paragraphs only.
        """
        paragraphs = self.com_object.Paragraphs

        start_index = max(1, start_index)

        if non_empty:
            paragraphs = [p for p in paragraphs if p.Range.Text.strip()]

        para_start = paragraphs[start_index - 1].Range.Start
        if end_index == -1:
            para_end = self.com_object.Range().End
        else:
            para_end = paragraphs[end_index - 1].Range.End

        self.com_object.Range(para_start, para_end).Select()

    def select_table(self, number: int) -> None:
        """
        Select a table in the document.
        :param number: The number of the table.
        """
        tables = self.com_object.Tables
        if not number or number < 1 or number > tables.Count:
            return f"Table number {number} is out of range."

        tables(number).Select()
        return f"Table {number} is selected."

    def set_font(self, font_name: str = None, font_size: int = None) -> None:
        """
        Set the font of the selected text in the active Word document.

        :param font_name: The name of the font (e.g., "Arial", "Times New Roman", "宋体").
                        If None, the font name will not be changed.
        :param font_size: The font size (e.g., 12).
                        If None, the font size will not be changed.
        """
        selection = self.com_object.Selection

        if selection.Type == 0:  # wdNoSelection

            return "No text is selected to set the font."

        font = selection.Range.Font

        message = ""

        if font_name:
            font.Name = font_name
            message += f"Font is set to {font_name}."

        if font_size:
            font.Size = font_size
            message += f" Font size is set to {font_size}."

        return message

    def save_to_pdf(self, file_path: str = None) -> None:
        """
        Save the document to PDF.
        :param file_path: The path of the PDF file. If None, save to the same path as the Word document.
        """

        if not file_path:
            filename = self.com_object.FullName
            file_path = os.path.splitext(filename)[0] + ".pdf"

        try:
            self.com_object.SaveAs2(file_path, FileFormat=17)
            return f"Document is saved to {file_path}."
        except Exception as e:
            return f"Failed to save the document to {file_path}. Error: {e}"

    @property
    def type_name(self):
        return "COM/WORD"

    @property
    def xml_format_code(self) -> int:
        return 11


@WordWinCOMReceiver.register
class InsertTableCommand(WinCOMCommand):
    """
    The command to insert a table.
    """

    def execute(self):
        """
        Execute the command to insert a table.
        :return: The inserted table.
        """
        return self.receiver.insert_table(
            self.params.get("rows"), self.params.get("columns")
        )

    @classmethod
    def name(cls) -> str:
        """
        The name of the command.
        """
        return "insert_table"


@WordWinCOMReceiver.register
class SelectTextCommand(WinCOMCommand):
    """
    The command to select text.
    """

    def execute(self):
        """
        Execute the command to select text.
        :return: The selected text.
        """
        return self.receiver.select_text(self.params.get("text"))

    @classmethod
    def name(cls) -> str:
        """
        The name of the command.
        """
        return "select_text"


@WordWinCOMReceiver.register
class SelectTableCommand(WinCOMCommand):
    """
    The command to select a table.
    """

    def execute(self):
        """
        Execute the command to select a table in the document.
        :return: The selected table.
        """
        return self.receiver.select_table(self.params.get("number"))

    @classmethod
    def name(cls) -> str:
        """
        The name of the command.
        """
        return "select_table"


@WordWinCOMReceiver.register
class SelectParagraphCommand(WinCOMCommand):
    """
    The command to select a paragraph.
    """

    def execute(self):
        """
        Execute the command to select a paragraph in the document.
        :return: The selected paragraph.
        """
        return self.receiver.select_paragraph(
            self.params.get("start_index"),
            self.params.get("end_index"),
            self.params.get("non_empty"),
        )

    @classmethod
    def name(cls) -> str:
        """
        The name of the command.
        """
        return "select_paragraph"


@WordWinCOMReceiver.register
class SaveToPDFCommand(WinCOMCommand):
    """
    The command to save the document to PDF.
    """

    def execute(self):
        """
        Execute the command to save the document to PDF.
        :return: The saved PDF file path.
        """
        return self.receiver.save_to_pdf(self.params.get("file_path", None))

    @classmethod
    def name(cls) -> str:
        """
        The name of the command.
        """
        return "save_to_pdf"


@WordWinCOMReceiver.register
class SetFontCommand(WinCOMCommand):
    """
    The command to set the font of the selected text.
    """

    def execute(self):
        """
        Execute the command to set the font of the selected text.
        :return: The message of the font setting.
        """
        return self.receiver.set_font(
            self.params.get("font_name"), self.params.get("font_size")
        )

    @classmethod
    def name(cls) -> str:
        """
        The name of the command.
        """
        return "set_font"
