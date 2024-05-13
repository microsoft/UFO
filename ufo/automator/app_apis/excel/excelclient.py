# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from typing import Any, Dict, Type

import pandas as pd

from ufo.automator.app_apis.basic import WinCOMCommand, WinCOMReceiverBasic
from ufo.automator.basic import CommandBasic
from ufo.prompter.agent_prompter import APIPromptLoader


class ExcelWinCOMReceiver(WinCOMReceiverBasic):
    """
    The base class for Windows COM client.
    """

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

    def get_default_command_registry(self) -> Dict[str, Type[CommandBasic]]:
        """
        Get the default command registry.
        """

        api_prompt_loader = APIPromptLoader(self.app_root_name)
        api_prompt = api_prompt_loader.load_com_api_prompt()
        class_name_dict = api_prompt_loader.filter_api_dict(api_prompt)

        global_name_space = globals()
        command_registry = self.name_to_command_class(
            global_name_space, class_name_dict
        )

        return command_registry

    def table2markdown(self, sheet_name: str) -> str:
        """
        Convert the table in the sheet to a markdown table string.
        :param sheet_name: The sheet name.
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


class GetSheetContent(WinCOMCommand):
    """
    The command to insert a table.
    """

    def execute(self):
        """
        Execute the command to insert a table.
        :return: The inserted table.
        """
        return self.receiver.table2markdown(self.params.get("sheet_name"))
