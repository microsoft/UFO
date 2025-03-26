# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import os
from typing import Any, Dict, List, Type, Union

import pandas as pd

from ufo.automator.app_apis.basic import WinCOMCommand, WinCOMReceiverBasic
from ufo.automator.basic import CommandBasic


class ExcelWinCOMReceiver(WinCOMReceiverBasic):
    """
    The base class for Windows COM client.
    """

    _command_registry: Dict[str, Type[CommandBasic]] = {}

    def get_object_from_process_name(self) -> None:
        """
        Get the object from the process name.
        :return: The matched object.
        """
        object_name_list = [doc.Name for doc in self.client.Workbooks]
        matched_object = self.app_match(object_name_list)

        for doc in self.client.Workbooks:
            if doc.Name == matched_object:
                return doc

        return None

    def table2markdown(self, sheet_name: Union[str, int]) -> str:
        """
        Convert the table in the sheet to a markdown table string.
        :param sheet_name: The sheet name (str), or the sheet index (int), starting from 1.
        :return: The markdown table string.
        """

        sheet = self.com_object.Sheets(sheet_name)

        # Fetch the data from the sheet
        data = sheet.UsedRange()

        # Convert the data to a DataFrame
        df = pd.DataFrame(data[1:], columns=data[0])

        # Drop the rows with all NaN values
        df = df.dropna(axis=0, how="all")

        # Convert the values to strings
        df = df.applymap(self.format_value)

        return df.to_markdown(index=False)

    def insert_excel_table(
        self, sheet_name: str, table: List[List[Any]], start_row: int, start_col: int
    ):
        """
        Insert a table into the sheet.
        :param sheet_name: The sheet name.
        :param table: The list of lists of values to be inserted.
        :param start_row: The start row.
        :param start_col: The start column.
        """
        sheet = self.com_object.Sheets(sheet_name)

        if str(start_col).isalpha():
            start_col = self.letters_to_number(start_col)

        for i, row in enumerate(table):
            for j, value in enumerate(row):
                sheet.Cells(start_row + i, start_col + j).Value = value

        return table

    def select_table_range(
        self,
        sheet_name: str,
        start_row: int,
        start_col: int,
        end_row: int,
        end_col: int,
    ):
        """
        Select a range of cells in the sheet.
        :param sheet_name: The sheet name.
        :param start_row: The start row.
        :param start_col: The start column.
        :param end_row: The end row. If ==-1, select to the end of the document with content.
        :param end_col: The end column. If ==-1, select to the end of the document with content.
        """

        sheet_list = [sheet.Name for sheet in self.com_object.Sheets]
        if sheet_name not in sheet_list:
            print(
                f"Sheet {sheet_name} not found in the workbook, using the first sheet."
            )
            sheet_name = 1

        if str(start_col).isalpha():
            start_col = self.letters_to_number(start_col)

        if str(end_col).isalpha():
            end_col = self.letters_to_number(end_col)

        if end_row == -1:
            end_row = sheet.Rows.Count
        if end_col == -1:
            end_col = sheet.Columns.Count

        sheet = self.com_object.Sheets(sheet_name)

        try:
            sheet.Range(
                sheet.Cells(start_row, start_col), sheet.Cells(end_row, end_col)
            ).Select()
            return f"Range {start_row}:{start_col} to {end_row}:{end_col} is selected."
        except Exception as e:
            return f"Failed to select the range {start_row}:{start_col} to {end_row}:{end_col}. Error: {e}"

    def save_as(
        self, file_dir: str = "", file_name: str = "", file_ext: str = ""
    ) -> None:
        """
        Save the document to PDF.
        :param file_dir: The directory to save the file.
        :param file_name: The name of the file without extension.
        :param file_ext: The extension of the file.
        """

        excel_ext_to_fileformat = {
            ".xlsx": 51,  # Excel Workbook (default, no macros)
            ".xlsm": 52,  # Excel Macro-Enabled Workbook
            ".xlsb": 50,  # Excel Binary Workbook
            ".xls": 56,  # Excel 97-2003 Workbook
            ".xltx": 54,  # Excel Template
            ".xltm": 53,  # Excel Macro-Enabled Template
            ".csv": 6,  # CSV (comma delimited)
            ".txt": 42,  # Text (tab delimited)
            ".pdf": 57,  # PDF file (Excel 2007+)
            ".xps": 58,  # XPS file
            ".xml": 46,  # XML Spreadsheet 2003
            ".html": 44,  # HTML file
            ".htm": 44,  # HTML file
            ".prn": 36,  # Formatted text (space delimited)
        }

        if not file_dir:
            file_dir = os.path.dirname(self.com_object.FullName)
        if not file_name:
            file_name = os.path.splitext(os.path.basename(self.com_object.FullName))[0]
        if not file_ext:
            file_ext = ".csv"

        file_path = os.path.join(file_dir, file_name + file_ext)

        try:
            self.com_object.SaveAs2(
                file_path, FileFormat=excel_ext_to_fileformat.get(file_ext, 6)
            )
            return f"Document is saved to {file_path}."
        except Exception as e:
            return f"Failed to save the document to {file_path}. Error: {e}"

    @staticmethod
    def letters_to_number(letters: str) -> int:
        """
        Convert the column letters to the column number.
        :param letters: The column letters.
        :return: The column number.
        """
        number = 0
        for i, letter in enumerate(letters[::-1]):
            number += (ord(letter.upper()) - ord("A") + 1) * (26**i)
        return number

    @staticmethod
    def format_value(value: Any) -> str:
        """
        Convert the value to a formatted string.
        :param value: The value to be converted.
        :return: The converted string.
        """
        if isinstance(value, (int, float)):
            return "{:.0f}".format(value)
        return value

    @property
    def type_name(self):
        return "COM/EXCEL"

    @property
    def xml_format_code(self) -> int:
        return 46


@ExcelWinCOMReceiver.register
class GetSheetContentCommand(WinCOMCommand):
    """
    The command to insert a table.
    """

    def execute(self):
        """
        Execute the command to insert a table.
        :return: The inserted table.
        """
        return self.receiver.table2markdown(self.params.get("sheet_name"))

    @classmethod
    def name(cls) -> str:
        """
        The name of the command.
        """
        return "table2markdown"


@ExcelWinCOMReceiver.register
class InsertExcelTableCommand(WinCOMCommand):
    """
    The command to insert a table.
    """

    def execute(self):
        """
        Execute the command to insert a table.
        :return: The inserted table.
        """
        return self.receiver.insert_excel_table(
            sheet_name=self.params.get("sheet_name", 1),
            table=self.params.get("table"),
            start_row=self.params.get("start_row", 1),
            start_col=self.params.get("start_col", 1),
        )

    @classmethod
    def name(cls) -> str:
        """
        The name of the command.
        """
        return "insert_excel_table"


@ExcelWinCOMReceiver.register
class SelectTableRangeCommand(WinCOMCommand):
    """
    The command to select a table.
    """

    def execute(self):
        """
        Execute the command to select a table.
        :return: The selected table.
        """
        return self.receiver.select_table_range(
            sheet_name=self.params.get("sheet_name", 1),
            start_row=self.params.get("start_row", 1),
            start_col=self.params.get("start_col", 1),
            end_row=self.params.get("end_row", 1),
            end_col=self.params.get("end_col", 1),
        )

    @classmethod
    def name(cls) -> str:
        """
        The name of the command.
        """
        return "select_table_range"


@ExcelWinCOMReceiver.register
class SaveAsCommand(WinCOMCommand):
    """
    The command to save the document to a specific format.
    """

    def execute(self):
        """
        Execute the command to save the document to a specific format.
        :return: The result of saving the document.
        """
        return self.receiver.save_as(
            file_dir=self.params.get("file_dir"),
            file_name=self.params.get("file_name"),
            file_ext=self.params.get("file_ext"),
        )

    @classmethod
    def name(cls) -> str:
        """
        The name of the command.
        """
        return "save_as"
