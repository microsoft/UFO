# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.


from ..client import WinCOMClient
from typing import List, Dict, Type
import win32com.client


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

