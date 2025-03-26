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

    def reorder_columns(self, sheet_name: str, desired_order: List[str]):
        """
        Reorder the columns in the sheet.
        :param sheet_name: The sheet name.
        :param desired_order: The list of column names in the new order.
        """

        sheet_list = [sheet.Name for sheet in self.com_object.Sheets]
        if sheet_name not in sheet_list:
            print(
                f"Sheet {sheet_name} not found in the workbook, using the first sheet."
            )
            sheet_name = 1

        sheet = self.com_object.Sheets(sheet_name)

        used_range = sheet.UsedRange
        num_cols = used_range.Columns.Count

        # Build a map from header name to current column number
        header_map = {}
        for col in range(1, num_cols + 1):
            header = str(sheet.Cells(1, col).Value).strip()
            if header:
                header_map[header] = col

        print("📌 Current columns:", list(header_map.keys()))

        # Reorder the columns
        insert_pos = 1

        try:
            for col_name in desired_order:
                print(f"🔀 Moving column '{col_name}' to position {insert_pos}.")
                if col_name not in header_map:
                    print(f"⚠️ Column '{col_name}' not found, skipping.")
                    continue

                current_col = header_map[col_name]

                # Copy the column and insert at target position
                sheet.Columns(current_col).Copy()
                sheet.Columns(insert_pos).Insert()

                # Delete the original column (adjust index if needed)
                if current_col >= insert_pos:
                    sheet.Columns(current_col + 1).Delete()
                else:
                    sheet.Columns(current_col).Delete()

                # Update header_map: all columns after this shift left
                header_map = {
                    h: (c if c < current_col else c - 1)
                    for h, c in header_map.items()
                    if h != col_name
                }

                insert_pos += 1
        except Exception as e:
            return f"Failed to reorder at column '{col_name}'. Error: {e}"

        return f"Columns reordered to: {desired_order}."

    def get_range_values(
        self,
        sheet_name: str,
        start_row: int,
        start_col: int,
        end_row: int = -1,
        end_col: int = -1,
    ):
        """
        Get values from Excel sheet starting at (start_row, start_col) to (end_row, end_col).
        If end_row or end_col is -1, it automatically extends to the last used row or column.

        :param sheet_name: The name of the sheet.
        :param start_row: Starting row index (1-based)
        :param start_col: Starting column index (1-based)
        :param end_row: Ending row index, -1 means go to the last used row
        :param end_col: Ending column index, -1 means go to the last used column
        :return: List of lists (2D) containing the values
        """

        sheet_list = [sheet.Name for sheet in self.com_object.Sheets]
        if sheet_name not in sheet_list:
            print(
                f"Sheet {sheet_name} not found in the workbook, using the first sheet."
            )
            sheet_name = 1

        sheet = self.com_object.Sheets(sheet_name)

        used_range = sheet.UsedRange
        last_row = used_range.Row + used_range.Rows.Count - 1
        last_col = used_range.Column + used_range.Columns.Count - 1

        if end_row == -1:
            end_row = last_row
        if end_col == -1:
            end_col = last_col

        cell_range = sheet.Range(
            sheet.Cells(start_row, start_col), sheet.Cells(end_row, end_col)
        )

        try:
            values = cell_range.Value

        except Exception as e:
            return f"Failed to get values from range {start_row}:{start_col} to {end_row}:{end_col}. Error: {e}"

        # If it's a single cell, return [[value]]
        if not isinstance(values, tuple):
            return [[values]]

        # If it's a single row or column, make sure it’s 2D list
        if isinstance(values[0], (str, int, float, type(None))):
            return [list(values)]

        return [list(row) for row in values]

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
            self.com_object.SaveAs(
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
class GetRangeValuesCommand(WinCOMCommand):
    """
    The command to get values from a range.
    """

    def execute(self):
        """
        Execute the command to get values from a range.
        :return: The values from the range.
        """
        return self.receiver.get_range_values(
            sheet_name=self.params.get("sheet_name", 1),
            start_row=self.params.get("start_row", 1),
            start_col=self.params.get("start_col", 1),
            end_row=self.params.get("end_row", -1),
            end_col=self.params.get("end_col", -1),
        )

    @classmethod
    def name(cls) -> str:
        """
        The name of the command.
        """
        return "get_range_values"


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
