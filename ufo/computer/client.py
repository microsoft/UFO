# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.



from abc import ABC, abstractmethod
from typing import List, Dict, Type
import win32com.client

class WinCOMClient(ABC):
    """
    The base class for Windows COM client.
    """


    def __init__(self, app_root_name: str, process_name: str) -> None:
        """
        Initialize the Windows COM client.
        :param clsid: The CLSID of the COM object.
        :param interface: The interface of the COM object.
        """
        self.clsid = self.app_root_mappping(app_root_name)
        self.client = win32com.client.Dispatch(self.clsid)
        self.object = self.get_object_from_process_name(process_name)



    @abstractmethod
    def get_object_from_process_name(self, process_name: str) -> None:
        """
        Get the object from the process name.
        :param process_name: The process name.
        """
        pass


    
    @classmethod
    def app_root_mappping(cls, app_root_name: str) -> str:
        """
        Map the app root to the corresponding app.
        :param app_root: The app root.
        :return: The app.
        """
        pass