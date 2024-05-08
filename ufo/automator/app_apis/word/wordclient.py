# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from typing import Dict, Type

from ufo.automator.app_apis.basic import WinCOMCommand, WinCOMReceiverBasic
from ufo.automator.basic import CommandBasic
from ufo.prompter.agent_prompter import APIPromptLoader


class WordWinCOMReceiver(WinCOMReceiverBasic):
    """
    The base class for Windows COM client.
    """

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

    def select_table(self, number: int) -> None:
        """
        Select a table in the document.
        :param number: The number of the table.
        """
        tables = self.com_object.Tables
        if not number or number < 1 or number > tables.Count:
            return f"Table number {number} is out of range."

        tables[number].Select()
        return f"Table {number} is selected."

    @property
    def type_name(self):
        return "COM/WORD"


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
