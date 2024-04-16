# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from ..client import WinCOMClient


class Word(WinCOMClient):
    """
    The base class for Windows COM client.
    """


    def __init__(self, app_root_name: str, process_name: str) -> None:
        """
        Initialize the Windows COM client.
        :param clsid: The CLSID of the COM object.
        :param interface: The interface of the COM object.
        """
        super().__init__(app_root_name, process_name)


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
    

    @property
    def registry(self) -> dict:
        """
        Get the method registry of the COM object.
        :return: The method registry.
        """
        mappping = {
            "insert_table": self.__insert_table,
        }

        return mappping
    

    def __insert_table(self, rows: int, columns: int) -> object:
        """
        Insert a table at the end of the document.
        :param rows: The number of rows.
        :param columns: The number of columns.
        :return: The inserted table.
        """

        # Get the range at the end of the document
        end_range = self.object.Range()
        end_range.Collapse(0)  # Collapse the range to the end

        # Insert a paragraph break (optional)
        end_range.InsertParagraphAfter()
        table = self.object.Tables.Add(end_range, rows, columns)
        table.Borders.Enable = True

        return table


