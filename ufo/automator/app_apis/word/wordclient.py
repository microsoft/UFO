# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from typing import Dict

from ..basic import WinCOMCommand, WinCOMReceiverBasic


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
    
    @staticmethod
    def get_default_command_registry() -> Dict[str, WinCOMCommand]:
        """
        Get the method registry of the COM object.
        :return: The method registry.
        """
        mappping = {
            "insert_table": InsertTableCommand,
        }
        return mappping
    

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
    


class InsertTableCommand(WinCOMCommand):
    """
    The command to insert a table.
    """
    def execute(self):
        """
        Execute the command to insert a table.
        :return: The inserted table.
        """
        return self.receiver.insert_table(self.params.get("rows"), self.params.get("columns"))
    

