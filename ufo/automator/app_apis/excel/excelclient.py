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

        sheet = self.com_object.Sheets(sheet_name)

        if end_row == -1:
            end_row = sheet.Rows.Count
        if end_col == -1:
            end_col = sheet.Columns.Count

        try:
            sheet.Range(
                sheet.Cells(start_row, start_col), sheet.Cells(end_row, end_col)
            ).Select()
            return f"Range {start_row}:{start_col} to {end_row}:{end_col} is selected."
        except Exception as e:
            return f"Failed to select the range {start_row}:{start_col} to {end_row}:{end_col}. Error: {e}"

    def reorder_columns(self, sheet_name: str, desired_order: List[str] = None) -> str:
        """
        Reorder only non-empty columns based on desired_order.
        Empty columns remain in their original positions.
        :param sheet_name: Sheet to operate on
        :param desired_order: List of column header names to reorder
        :return: Success or error message
        """
        try:
            ws = self.com_object.Sheets(sheet_name)
            used_range = ws.UsedRange
            start_col = used_range.Column
            total_cols = used_range.Columns.Count
            last_col = start_col + total_cols - 1

            non_empty_columns = []
            empty_columns = []

            for col in range(1, last_col + 1):
                cell_value = ws.Cells(1, col).Value
                if cell_value and str(cell_value).strip():
                    non_empty_columns.append((str(cell_value).strip(), col))
                else:
                    empty_columns.append(col)

            print("📌 Non-empty columns:", [x[0] for x in non_empty_columns])
            print("📌 Empty columns at:", empty_columns)

            name_to_col = {name: col for name, col in non_empty_columns}

            column_data = []
            for name in desired_order:
                if name in name_to_col:
                    col_index = name_to_col[name]
                    data = []
                    row = 1
                    while True:
                        value = ws.Cells(row, col_index).Value
                        if value is None and row > 100:
                            break
                        data.append(value)
                        row += 1
                    column_data.append((name, data))
                else:
                    print(f"⚠️ Column '{name}' not found, skipping.")

            for _, col_index in sorted(non_empty_columns, key=lambda x: -x[1]):
                ws.Columns(col_index).Delete()

            insert_offset = 1
            for name, data in column_data:
                insert_pos = self.get_nth_non_empty_position(insert_offset, empty_columns)
                print(f"✅ Inserting '{name}' at position {insert_pos}")
                for row_index, value in enumerate(data, start=1):
                    ws.Cells(row_index, insert_pos).Value = value
                insert_offset += 1

            return f"Columns reordered successfully into: {desired_order}"

        except Exception as e:
            print(f"❌ Failed to reorder columns. Error: {e}")
            return f"Failed to reorder columns. Error: {e}"

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

    def save_workbook(self, file_path: str = None, file_format: str = "xlsx") -> str:
        """
        Save the current workbook.
        :param file_path: Path where to save the workbook (optional if already saved)
        :param file_format: File format (xlsx, xls, csv, etc.)
        :return: Success message
        """
        try:
            if file_path:
                # Save to specific path
                format_map = {
                    "xlsx": 51,  # Excel Workbook
                    "xlsm": 52,  # Excel Macro-Enabled Workbook
                    "xlsb": 50,  # Excel Binary Workbook
                    "xls": 56,   # Excel 97-2003 Workbook
                    "csv": 6,    # CSV format
                    "txt": 42,   # Text format
                    "pdf": 57,   # PDF format
                    "html": 44   # HTML format
                }
                
                file_format_code = format_map.get(file_format.lower(), 51)
                self.com_object.SaveAs(Filename=file_path, FileFormat=file_format_code)
                return f"Workbook saved successfully to {file_path}"
            else:
                # Save with current name and location
                self.com_object.Save()
                return f"Workbook saved successfully: {self.com_object.Name}"
        except Exception as e:
            return f"Failed to save workbook. Error: {e}"

    def create_workbook(self, template_path: str = None) -> str:
        """
        Create a new Excel workbook.
        :param template_path: Path to template file (optional)
        :return: Success message with workbook name
        """
        try:
            if template_path and os.path.exists(template_path):
                workbook = self.client.Workbooks.Open(template_path)
            else:
                workbook = self.client.Workbooks.Add()
            return f"Workbook created successfully: {workbook.Name}"
        except Exception as e:
            return f"Failed to create workbook. Error: {e}"

    def open_workbook(self, file_path: str, read_only: bool = False, password: str = None) -> str:
        """
        Open an existing Excel workbook.
        :param file_path: Path to the Excel file
        :param read_only: Whether to open in read-only mode
        :param password: Password for protected files
        :return: Success message
        """
        try:
            if not os.path.exists(file_path):
                return f"File not found: {file_path}"
            
            if password:
                workbook = self.client.Workbooks.Open(file_path, ReadOnly=read_only, Password=password)
            else:
                workbook = self.client.Workbooks.Open(file_path, ReadOnly=read_only)
            return f"Workbook opened successfully: {workbook.Name}"
        except Exception as e:
            return f"Failed to open workbook. Error: {e}"

    def close_workbook(self, save_changes: bool = True, workbook_name: str = None) -> str:
        """
        Close the active or specified workbook.
        :param save_changes: Whether to save changes before closing
        :param workbook_name: Name of specific workbook to close (optional)
        :return: Success message
        """
        try:
            if workbook_name:
                workbook = self.client.Workbooks(workbook_name)
            else:
                workbook = self.com_object
            
            workbook.Close(SaveChanges=save_changes)
            return f"Workbook closed successfully"
        except Exception as e:
            return f"Failed to close workbook. Error: {e}"

    def add_worksheet(self, name: str = None, position: int = None) -> str:
        """
        Add a new worksheet to the workbook.
        :param name: Name for the new worksheet
        :param position: Position where to insert (optional)
        :return: Success message with worksheet name
        """
        try:
            if position:
                worksheet = self.com_object.Worksheets.Add(After=self.com_object.Worksheets(position))
            else:
                worksheet = self.com_object.Worksheets.Add()
            
            if name:
                worksheet.Name = name
                
            return f"Worksheet added successfully: {worksheet.Name}"
        except Exception as e:
            return f"Failed to add worksheet. Error: {e}"

    def delete_worksheet(self, sheet_name: str) -> str:
        """
        Delete a worksheet from the workbook.
        :param sheet_name: Name of the worksheet to delete
        :return: Success message
        """
        try:
            # Disable alerts to avoid confirmation dialog
            self.client.DisplayAlerts = False
            self.com_object.Worksheets(sheet_name).Delete()
            self.client.DisplayAlerts = True
            return f"Worksheet '{sheet_name}' deleted successfully"
        except Exception as e:
            self.client.DisplayAlerts = True
            return f"Failed to delete worksheet. Error: {e}"

    def select_worksheet(self, sheet_name: str) -> str:
        """
        Select/activate a specific worksheet.
        :param sheet_name: Name of the worksheet to select
        :return: Success message
        """
        try:
            self.com_object.Worksheets(sheet_name).Activate()
            return f"Worksheet '{sheet_name}' selected successfully"
        except Exception as e:
            return f"Failed to select worksheet. Error: {e}"

    def rename_worksheet(self, old_name: str, new_name: str) -> str:
        """
        Rename a worksheet.
        :param old_name: Current name of the worksheet
        :param new_name: New name for the worksheet
        :return: Success message
        """
        try:
            self.com_object.Worksheets(old_name).Name = new_name
            return f"Worksheet renamed from '{old_name}' to '{new_name}'"
        except Exception as e:
            return f"Failed to rename worksheet. Error: {e}"

    def set_cell_value(self, sheet_name: str, cell_reference: str, value: any, formula: str = None) -> str:
        """
        Set the value of a specific cell.
        :param sheet_name: Name of the worksheet
        :param cell_reference: Cell reference (e.g., 'A1')
        :param value: Value to set
        :param formula: Formula to set (optional)
        :return: Success message
        """
        try:
            sheet = self.com_object.Worksheets(sheet_name)
            if formula:
                sheet.Range(cell_reference).Formula = formula
            else:
                sheet.Range(cell_reference).Value = value
            return f"Cell {cell_reference} set successfully"
        except Exception as e:
            return f"Failed to set cell value. Error: {e}"

    def get_cell_value(self, sheet_name: str, cell_reference: str) -> any:
        """
        Get the value of a specific cell.
        :param sheet_name: Name of the worksheet
        :param cell_reference: Cell reference (e.g., 'A1')
        :return: Cell value
        """
        try:
            sheet = self.com_object.Worksheets(sheet_name)
            return sheet.Range(cell_reference).Value
        except Exception as e:
            return f"Failed to get cell value. Error: {e}"

    def set_range_values(self, sheet_name: str, start_cell: str, end_cell: str, values: list) -> str:
        """
        Set values for a range of cells.
        :param sheet_name: Name of the worksheet
        :param start_cell: Starting cell reference
        :param end_cell: Ending cell reference
        :param values: 2D list of values
        :return: Success message
        """
        try:
            sheet = self.com_object.Worksheets(sheet_name)
            range_obj = sheet.Range(f"{start_cell}:{end_cell}")
            range_obj.Value = values
            return f"Range {start_cell}:{end_cell} set successfully"
        except Exception as e:
            return f"Failed to set range values. Error: {e}"

    def insert_formula(self, sheet_name: str, cell_reference: str, formula: str) -> str:
        """
        Insert a formula into a cell.
        :param sheet_name: Name of the worksheet
        :param cell_reference: Cell reference
        :param formula: Formula to insert
        :return: Success message
        """
        try:
            sheet = self.com_object.Worksheets(sheet_name)
            sheet.Range(cell_reference).Formula = formula
            return f"Formula inserted in {cell_reference}: {formula}"
        except Exception as e:
            return f"Failed to insert formula. Error: {e}"

    def format_cells(self, sheet_name: str, cell_range: str, font_name: str = None, 
                    font_size: int = None, bold: bool = None, italic: bool = None, 
                    font_color: str = None, background_color: str = None, 
                    number_format: str = None) -> str:
        """
        Format cells with various formatting options.
        :param sheet_name: Name of the worksheet
        :param cell_range: Range to format
        :param font_name: Font name
        :param font_size: Font size
        :param bold: Bold formatting
        :param italic: Italic formatting
        :param font_color: Font color (hex)
        :param background_color: Background color (hex)
        :param number_format: Number format
        :return: Success message
        """
        try:
            sheet = self.com_object.Worksheets(sheet_name)
            range_obj = sheet.Range(cell_range)
            
            if font_name:
                range_obj.Font.Name = font_name
            if font_size:
                range_obj.Font.Size = font_size
            if bold is not None:
                range_obj.Font.Bold = bold
            if italic is not None:
                range_obj.Font.Italic = italic
            if font_color:
                range_obj.Font.Color = int(font_color.replace('#', ''), 16)
            if background_color:
                range_obj.Interior.Color = int(background_color.replace('#', ''), 16)
            if number_format:
                range_obj.NumberFormat = number_format
                
            return f"Cells formatted successfully: {cell_range}"
        except Exception as e:
            return f"Failed to format cells. Error: {e}"

    def insert_rows(self, sheet_name: str, row_index: int, count: int = 1) -> str:
        """
        Insert rows at specified position.
        :param sheet_name: Name of the worksheet
        :param row_index: Row index where to insert
        :param count: Number of rows to insert
        :return: Success message
        """
        try:
            sheet = self.com_object.Worksheets(sheet_name)
            for _ in range(count):
                sheet.Rows(row_index).Insert()
            return f"Inserted {count} row(s) at position {row_index}"
        except Exception as e:
            return f"Failed to insert rows. Error: {e}"

    def insert_columns(self, sheet_name: str, column_index: int, count: int = 1) -> str:
        """
        Insert columns at specified position.
        :param sheet_name: Name of the worksheet
        :param column_index: Column index where to insert
        :param count: Number of columns to insert
        :return: Success message
        """
        try:
            sheet = self.com_object.Worksheets(sheet_name)
            for _ in range(count):
                sheet.Columns(column_index).Insert()
            return f"Inserted {count} column(s) at position {column_index}"
        except Exception as e:
            return f"Failed to insert columns. Error: {e}"

    def delete_rows(self, sheet_name: str, row_index: int, count: int = 1) -> str:
        """
        Delete rows at specified position.
        :param sheet_name: Name of the worksheet
        :param row_index: Row index to start deleting
        :param count: Number of rows to delete
        :return: Success message
        """
        try:
            sheet = self.com_object.Worksheets(sheet_name)
            for _ in range(count):
                sheet.Rows(row_index).Delete()
            return f"Deleted {count} row(s) starting at position {row_index}"
        except Exception as e:
            return f"Failed to delete rows. Error: {e}"

    def delete_columns(self, sheet_name: str, column_index: int, count: int = 1) -> str:
        """
        Delete columns at specified position.
        :param sheet_name: Name of the worksheet
        :param column_index: Column index to start deleting
        :param count: Number of columns to delete
        :return: Success message
        """
        try:
            sheet = self.com_object.Worksheets(sheet_name)
            for _ in range(count):
                sheet.Columns(column_index).Delete()
            return f"Deleted {count} column(s) starting at position {column_index}"
        except Exception as e:
            return f"Failed to delete columns. Error: {e}"

    def create_chart(self, sheet_name: str, chart_type: str, data_range: str, 
                    chart_title: str = None, position: dict = None) -> str:
        """
        Create a chart in the worksheet.
        :param sheet_name: Name of the worksheet
        :param chart_type: Type of chart (column, line, pie, etc.)
        :param data_range: Range of data for the chart
        :param chart_title: Title for the chart
        :param position: Position and size of the chart
        :return: Success message
        """
        try:
            sheet = self.com_object.Worksheets(sheet_name)
            
            # Chart type mapping
            chart_types = {
                'column': 51,  # xlColumnClustered
                'line': 4,     # xlLine
                'pie': 5,      # xlPie
                'bar': 57,     # xlBarClustered
                'area': 1,     # xlArea
                'scatter': 74  # xlXYScatter
            }
            
            chart_obj = sheet.Shapes.AddChart2(
                Style=-1,
                Type=chart_types.get(chart_type.lower(), 51)
            ).Chart;
            
            chart_obj.SetSourceData(sheet.Range(data_range))
            
            if chart_title:
                chart_obj.ChartTitle.Text = chart_title
                
            if position:
                chart_shape = chart_obj.Parent
                if 'left' in position:
                    chart_shape.Left = position['left']
                if 'top' in position:
                    chart_shape.Top = position['top']
                if 'width' in position:
                    chart_shape.Width = position['width']
                if 'height' in position:
                    chart_shape.Height = position['height']
            
            return f"Chart created successfully: {chart_type}"
        except Exception as e:
            return f"Failed to create chart. Error: {e}"

    def create_pivot_table(self, sheet_name: str, source_data: str, destination: str, 
                          fields: dict) -> str:
        """
        Create a pivot table.
        :param sheet_name: Name of the worksheet
        :param source_data: Source data range
        :param destination: Destination cell for pivot table
        :param fields: Dictionary of field configurations
        :return: Success message
        """
        try:
            sheet = self.com_object.Worksheets(sheet_name)
            pivot_cache = self.com_object.Parent.PivotCaches().Create(
                SourceType=1,  # xlDatabase
                SourceData=source_data
            )
            
            pivot_table = pivot_cache.CreatePivotTable(
                TableDestination=f"{sheet_name}!{destination}",
                TableName="PivotTable1"
            )
            
            # Configure fields based on the fields dictionary
            # This is a simplified implementation - full implementation would handle all field types
            if 'row_fields' in fields:
                for field in fields['row_fields']:
                    pivot_table.PivotFields(field).Orientation = 1  # xlRowField
                    
            if 'column_fields' in fields:
                for field in fields['column_fields']:
                    pivot_table.PivotFields(field).Orientation = 2  # xlColumnField
                    
            if 'data_fields' in fields:
                for field in fields['data_fields']:
                    pivot_table.PivotFields(field).Orientation = 4  # xlDataField
            
            return "Pivot table created successfully"
        except Exception as e:
            return f"Failed to create pivot table. Error: {e}"

    def sort_range(self, sheet_name: str, data_range: str, sort_column: str, 
                  ascending: bool = True, has_headers: bool = True) -> str:
        """
        Sort a range of data.
        :param sheet_name: Name of the worksheet
        :param data_range: Range to sort
        :param sort_column: Column to sort by
        :param ascending: Sort direction
        :param has_headers: Whether the range has headers
        :return: Success message
        """
        try:
            sheet = self.com_object.Worksheets(sheet_name)
            range_obj = sheet.Range(data_range)
            
            sort_obj = self.com_object.Parent.ActiveWorkbook.Worksheets(sheet_name).Sort
            sort_obj.SortFields.Clear()
            sort_obj.SortFields.Add(
                Key=sheet.Range(sort_column),
                SortOn=0,  # xlSortOnValues
                Order=1 if ascending else 2,  # xlAscending or xlDescending
                DataOption=0  # xlSortNormal
            )
            
            sort_obj.SetRange(range_obj)
            sort_obj.Header = 1 if has_headers else 2  # xlYes or xlNo
            sort_obj.Apply()
            
            return f"Range sorted successfully by column {sort_column}"
        except Exception as e:
            return f"Failed to sort range. Error: {e}"

    def filter_data(self, sheet_name: str, data_range: str, filter_column: str, 
                   criteria: str) -> str:
        """
        Apply filter to data range.
        :param sheet_name: Name of the worksheet
        :param data_range: Range to filter
        :param filter_column: Column to filter by
        :param criteria: Filter criteria
        :return: Success message
        """
        try:
            sheet = self.com_object.Worksheets(sheet_name)
            range_obj = sheet.Range(data_range)
            
            # Apply AutoFilter if not already applied
            if not range_obj.AutoFilter:
                range_obj.AutoFilter()
            
            # Get column index for filtering
            header_row = range_obj.Rows(1)
            column_index = None
            for i, cell in enumerate(header_row.Cells, 1):
                if str(cell.Value).strip() == filter_column:
                    column_index = i
                    break
            
            if column_index:
                range_obj.AutoFilter(Field=column_index, Criteria1=criteria)
                return f"Filter applied to column {filter_column} with criteria: {criteria}"
            else:
                return f"Column '{filter_column}' not found in range"
                
        except Exception as e:
            return f"Failed to apply filter. Error: {e}"

    def freeze_panes(self, sheet_name: str, cell_reference: str) -> str:
        """
        Freeze panes at specified cell.
        :param sheet_name: Name of the worksheet
        :param cell_reference: Cell where to freeze panes
        :return: Success message
        """
        try:
            sheet = self.com_object.Worksheets(sheet_name)
            sheet.Activate()
            sheet.Range(cell_reference).Select()
            self.client.ActiveWindow.FreezePanes = True
            return f"Panes frozen at {cell_reference}"
        except Exception as e:
            return f"Failed to freeze panes. Error: {e}"

    def protect_worksheet(self, sheet_name: str, password: str = None, 
                         allow_formatting_cells: bool = False) -> str:
        """
        Protect a worksheet.
        :param sheet_name: Name of the worksheet
        :param password: Password for protection
        :param allow_formatting_cells: Whether to allow cell formatting
        :return: Success message
        """
        try:
            sheet = self.com_object.Worksheets(sheet_name)
            sheet.Protect(Password=password, AllowFormattingCells=allow_formatting_cells)
            return f"Worksheet '{sheet_name}' protected successfully"
        except Exception as e:
            return f"Failed to protect worksheet. Error: {e}"

    def unprotect_worksheet(self, sheet_name: str, password: str = None) -> str:
        """
        Unprotect a worksheet.
        :param sheet_name: Name of the worksheet
        :param password: Password for unprotection
        :return: Success message
        """
        try:
            sheet = self.com_object.Worksheets(sheet_name)
            sheet.Unprotect(Password=password)
            return f"Worksheet '{sheet_name}' unprotected successfully"
        except Exception as e:
            return f"Failed to unprotect worksheet. Error: {e}"

    def export_worksheet(self, sheet_name: str, file_path: str, file_format: str) -> str:
        """
        Export a specific worksheet to a file.
        :param sheet_name: Name of the worksheet
        :param file_path: Path for the exported file
        :param file_format: Export format (csv, pdf, etc.)
        :return: Success message
        """
        try:
            sheet = self.com_object.Worksheets(sheet_name)
            
            format_map = {
                'csv': 6,    # xlCSV
                'pdf': 57,   # xlTypePDF
                'xps': 58,   # xlTypeXPS
                'html': 44,  # xlHtml
                'txt': 42    # xlTextTab
            }
            
            sheet.ExportAsFixedFormat(
                Type=format_map.get(file_format.lower(), 57),
                Filename=file_path
            )
            
            return f"Worksheet '{sheet_name}' exported to {file_path}"
        except Exception as e:
            return f"Failed to export worksheet. Error: {e}"

    def calculate_workbook(self) -> str:
        """
        Force calculation of all formulas in the workbook.
        :return: Success message
        """
        try:
            self.com_object.Calculate()
            return "Workbook calculations completed"
        except Exception as e:
            return f"Failed to calculate workbook. Error: {e}"

    def get_workbook_info(self) -> dict:
        """
        Get information about the current workbook.
        :return: Dictionary with workbook information
        """
        try:
            info = {
                'name': self.com_object.Name,
                'full_name': self.com_object.FullName,
                'saved': self.com_object.Saved,
                'worksheet_count': self.com_object.Worksheets.Count,
                'active_sheet': self.com_object.ActiveSheet.Name,
                'creation_date': str(self.com_object.BuiltinDocumentProperties("Creation Date").Value),
                'last_save_time': str(self.com_object.BuiltinDocumentProperties("Last Save Time").Value)
            }
            return info
        except Exception as e:
            return f"Failed to get workbook info. Error: {e}"

    def get_worksheet_names(self) -> list:
        """
        Get list of all worksheet names in the workbook.
        :return: List of worksheet names
        """
        try:
            return [sheet.Name for sheet in self.com_object.Worksheets]
        except Exception as e:
            return f"Failed to get worksheet names. Error: {e}"

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
    def get_nth_non_empty_position(target_idx: int, empty_cols: List[int]) -> int:
        """
        Get the Nth available column index in the sheet, skipping empty columns.
        :param target_idx: The target index of the non-empty column.
        :param empty_cols: The list of empty column indexes.
        :return: The Nth non-empty column index.
        """
        col = 1
        non_empty_count = 0
        while True:
            if col not in empty_cols:
                non_empty_count += 1
            if non_empty_count == target_idx:
                return col
            col += 1

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
class ReorderColumnsCommand(WinCOMCommand):
    """
    The command to reorder columns in a sheet.
    """

    def execute(self):
        """
        Execute the command to reorder columns in a sheet.
        :return: The result of reordering columns.
        """
        return self.receiver.reorder_columns(
            sheet_name=self.params.get("sheet_name", 1),
            desired_order=self.params.get("desired_order"),
        )

    @classmethod
    def name(cls) -> str:
        """
        The name of the command.
        """
        return "reorder_columns"


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


@ExcelWinCOMReceiver.register
class SaveWorkbookCommand(WinCOMCommand):
    """Command to save the current workbook."""
    
    def execute(self):
        return self.receiver.save_workbook(
            file_path=self.params.get("file_path"),
            file_format=self.params.get("file_format", "xlsx")
        )
    
    @classmethod
    def name(cls) -> str:
        return "save_workbook"


@ExcelWinCOMReceiver.register
class CreateWorkbookCommand(WinCOMCommand):
    """Command to create a new workbook."""
    
    def execute(self):
        return self.receiver.create_workbook(
            template_path=self.params.get("template_path")
        )
    
    @classmethod
    def name(cls) -> str:
        return "create_workbook"


@ExcelWinCOMReceiver.register
class OpenWorkbookCommand(WinCOMCommand):
    """Command to open an existing workbook."""
    
    def execute(self):
        return self.receiver.open_workbook(
            file_path=self.params.get("file_path"),
            read_only=self.params.get("read_only", False),
            password=self.params.get("password")
        )
    
    @classmethod
    def name(cls) -> str:
        return "open_workbook"


@ExcelWinCOMReceiver.register
class CloseWorkbookCommand(WinCOMCommand):
    """Command to close a workbook."""
    
    def execute(self):
        return self.receiver.close_workbook(
            save_changes=self.params.get("save_changes", True),
            workbook_name=self.params.get("workbook_name")
        )
    
    @classmethod
    def name(cls) -> str:
        return "close_workbook"


@ExcelWinCOMReceiver.register
class AddWorksheetCommand(WinCOMCommand):
    """Command to add a new worksheet."""
    
    def execute(self):
        return self.receiver.add_worksheet(
            name=self.params.get("name"),
            position=self.params.get("position")
        )
    
    @classmethod
    def name(cls) -> str:
        return "add_worksheet"


@ExcelWinCOMReceiver.register
class DeleteWorksheetCommand(WinCOMCommand):
    """Command to delete a worksheet."""
    
    def execute(self):
        return self.receiver.delete_worksheet(
            sheet_name=self.params.get("sheet_name")
        )
    
    @classmethod
    def name(cls) -> str:
        return "delete_worksheet"


@ExcelWinCOMReceiver.register
class SelectWorksheetCommand(WinCOMCommand):
    """Command to select a worksheet."""
    
    def execute(self):
        return self.receiver.select_worksheet(
            sheet_name=self.params.get("sheet_name")
        )
    
    @classmethod
    def name(cls) -> str:
        return "select_worksheet"


@ExcelWinCOMReceiver.register
class RenameWorksheetCommand(WinCOMCommand):
    """Command to rename a worksheet."""
    
    def execute(self):
        return self.receiver.rename_worksheet(
            old_name=self.params.get("old_name"),
            new_name=self.params.get("new_name")
        )
    
    @classmethod
    def name(cls) -> str:
        return "rename_worksheet"


@ExcelWinCOMReceiver.register
class SetCellValueCommand(WinCOMCommand):
    """Command to set cell value."""
    
    def execute(self):
        return self.receiver.set_cell_value(
            sheet_name=self.params.get("sheet_name"),
            cell_reference=self.params.get("cell_reference"),
            value=self.params.get("value"),
            formula=self.params.get("formula")
        )
    
    @classmethod
    def name(cls) -> str:
        return "set_cell_value"


@ExcelWinCOMReceiver.register
class GetCellValueCommand(WinCOMCommand):
    """Command to get cell value."""
    
    def execute(self):
        return self.receiver.get_cell_value(
            sheet_name=self.params.get("sheet_name"),
            cell_reference=self.params.get("cell_reference")
        )
    
    @classmethod
    def name(cls) -> str:
        return "get_cell_value"


@ExcelWinCOMReceiver.register
class SetRangeValuesCommand(WinCOMCommand):
    """Command to set range values."""
    
    def execute(self):
        return self.receiver.set_range_values(
            sheet_name=self.params.get("sheet_name"),
            start_cell=self.params.get("start_cell"),
            end_cell=self.params.get("end_cell"),
            values=self.params.get("values")
        )
    
    @classmethod
    def name(cls) -> str:
        return "set_range_values"


@ExcelWinCOMReceiver.register
class InsertFormulaCommand(WinCOMCommand):
    """Command to insert formula."""
    
    def execute(self):
        return self.receiver.insert_formula(
            sheet_name=self.params.get("sheet_name"),
            cell_reference=self.params.get("cell_reference"),
            formula=self.params.get("formula")
        )
    
    @classmethod
    def name(cls) -> str:
        return "insert_formula"


@ExcelWinCOMReceiver.register
class FormatCellsCommand(WinCOMCommand):
    """Command to format cells."""
    
    def execute(self):
        return self.receiver.format_cells(
            sheet_name=self.params.get("sheet_name"),
            cell_range=self.params.get("cell_range"),
            font_name=self.params.get("font_name"),
            font_size=self.params.get("font_size"),
            bold=self.params.get("bold"),
            italic=self.params.get("italic"),
            font_color=self.params.get("font_color"),
            background_color=self.params.get("background_color"),
            number_format=self.params.get("number_format")
        )
    
    @classmethod
    def name(cls) -> str:
        return "format_cells"


@ExcelWinCOMReceiver.register
class InsertRowsCommand(WinCOMCommand):
    """Command to insert rows."""
    
    def execute(self):
        return self.receiver.insert_rows(
            sheet_name=self.params.get("sheet_name"),
            row_index=self.params.get("row_index"),
            count=self.params.get("count", 1)
        )
    
    @classmethod
    def name(cls) -> str:
        return "insert_rows"


@ExcelWinCOMReceiver.register
class InsertColumnsCommand(WinCOMCommand):
    """Command to insert columns."""
    
    def execute(self):
        return self.receiver.insert_columns(
            sheet_name=self.params.get("sheet_name"),
            column_index=self.params.get("column_index"),
            count=self.params.get("count", 1)
        )
    
    @classmethod
    def name(cls) -> str:
        return "insert_columns"


@ExcelWinCOMReceiver.register
class DeleteRowsCommand(WinCOMCommand):
    """Command to delete rows."""
    
    def execute(self):
        return self.receiver.delete_rows(
            sheet_name=self.params.get("sheet_name"),
            row_index=self.params.get("row_index"),
            count=self.params.get("count", 1)
        )
    
    @classmethod
    def name(cls) -> str:
        return "delete_rows"


@ExcelWinCOMReceiver.register
class DeleteColumnsCommand(WinCOMCommand):
    """Command to delete columns."""
    
    def execute(self):
        return self.receiver.delete_columns(
            sheet_name=self.params.get("sheet_name"),
            column_index=self.params.get("column_index"),
            count=self.params.get("count", 1)
        )
    
    @classmethod
    def name(cls) -> str:
        return "delete_columns"


@ExcelWinCOMReceiver.register
class CreateChartCommand(WinCOMCommand):
    """Command to create a chart."""
    
    def execute(self):
        return self.receiver.create_chart(
            sheet_name=self.params.get("sheet_name"),
            chart_type=self.params.get("chart_type"),
            data_range=self.params.get("data_range"),
            chart_title=self.params.get("chart_title"),
            position=self.params.get("position")
        )
    
    @classmethod
    def name(cls) -> str:
        return "create_chart"


@ExcelWinCOMReceiver.register
class CreatePivotTableCommand(WinCOMCommand):
    """Command to create a pivot table."""
    
    def execute(self):
        return self.receiver.create_pivot_table(
            sheet_name=self.params.get("sheet_name"),
            source_data=self.params.get("source_data"),
            destination=self.params.get("destination"),
            fields=self.params.get("fields")
        )
    
    @classmethod
    def name(cls) -> str:
        return "create_pivot_table"


@ExcelWinCOMReceiver.register
class SortRangeCommand(WinCOMCommand):
    """Command to sort a range."""
    
    def execute(self):
        return self.receiver.sort_range(
            sheet_name=self.params.get("sheet_name"),
            data_range=self.params.get("data_range"),
            sort_column=self.params.get("sort_column"),
            ascending=self.params.get("ascending", True),
            has_headers=self.params.get("has_headers", True)
        )
    
    @classmethod
    def name(cls) -> str:
        return "sort_range"


@ExcelWinCOMReceiver.register
class FilterDataCommand(WinCOMCommand):
    """Command to filter data."""
    
    def execute(self):
        return self.receiver.filter_data(
            sheet_name=self.params.get("sheet_name"),
            data_range=self.params.get("data_range"),
            filter_column=self.params.get("filter_column"),
            criteria=self.params.get("criteria")
        )
    
    @classmethod
    def name(cls) -> str:
        return "filter_data"


@ExcelWinCOMReceiver.register
class FreezePanesCommand(WinCOMCommand):
    """Command to freeze panes."""
    
    def execute(self):
        return self.receiver.freeze_panes(
            sheet_name=self.params.get("sheet_name"),
            cell_reference=self.params.get("cell_reference")
        )
    
    @classmethod
    def name(cls) -> str:
        return "freeze_panes"


@ExcelWinCOMReceiver.register
class ProtectWorksheetCommand(WinCOMCommand):
    """Command to protect worksheet."""
    
    def execute(self):
        return self.receiver.protect_worksheet(
            sheet_name=self.params.get("sheet_name"),
            password=self.params.get("password"),
            allow_formatting_cells=self.params.get("allow_formatting_cells", False)
        )
    
    @classmethod
    def name(cls) -> str:
        return "protect_worksheet"


@ExcelWinCOMReceiver.register
class UnprotectWorksheetCommand(WinCOMCommand):
    """Command to unprotect worksheet."""
    
    def execute(self):
        return self.receiver.unprotect_worksheet(
            sheet_name=self.params.get("sheet_name"),
            password=self.params.get("password")
        )
    
    @classmethod
    def name(cls) -> str:
        return "unprotect_worksheet"


@ExcelWinCOMReceiver.register
class ExportWorksheetCommand(WinCOMCommand):
    """Command to export worksheet."""
    
    def execute(self):
        return self.receiver.export_worksheet(
            sheet_name=self.params.get("sheet_name"),
            file_path=self.params.get("file_path"),
            file_format=self.params.get("file_format")
        )
    
    @classmethod
    def name(cls) -> str:
        return "export_worksheet"


@ExcelWinCOMReceiver.register
class CalculateWorkbookCommand(WinCOMCommand):
    """Command to calculate workbook."""
    
    def execute(self):
        return self.receiver.calculate_workbook()
    
    @classmethod
    def name(cls) -> str:
        return "calculate_workbook"


@ExcelWinCOMReceiver.register
class GetWorkbookInfoCommand(WinCOMCommand):
    """Command to get workbook info."""
    
    def execute(self):
        return self.receiver.get_workbook_info()
    
    @classmethod
    def name(cls) -> str:
        return "get_workbook_info"


@ExcelWinCOMReceiver.register
class GetWorksheetNamesCommand(WinCOMCommand):
    """Command to get worksheet names."""
    
    def execute(self):
        return self.receiver.get_worksheet_names()
    
    @classmethod
    def name(cls) -> str:
        return "get_worksheet_names"
