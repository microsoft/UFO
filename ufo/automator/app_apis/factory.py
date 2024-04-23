# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from typing import Type

from ..basic import ReceiverFactory
from .basic import WinCOMReceiverBasic
from .word.wordclient import WordWinCOMReceiver


class COMReceiverFactory(ReceiverFactory):
    """
    The factory class for the COM receiver.
    """
    def create_receiver(self, app_root_name: str, process_name: str) -> WinCOMReceiverBasic:
        """
        Create the wincom receiver.
        :param app_root_name: The app root name.
        :param process_name: The process name.
        :return: The receiver.
        """

        com_receiver = self.com_client_mapper(app_root_name)
        clsid = self.app_root_mappping(app_root_name)

        if clsid is None:
            raise ValueError(f"App root name {app_root_name} is not supported.")
        
        return com_receiver(app_root_name, process_name)
    

    def com_client_mapper(self, app_root_name: str) -> Type[WinCOMReceiverBasic]:
        """
        Map the app root to the corresponding COM client.
        :param app_root_name: The app root name.
        :return: The COM client.
        """
        win_com_client_mapping = {
            "WINWORD.EXE": WordWinCOMReceiver
        }

        com_receiver = win_com_client_mapping.get(app_root_name, None)
        if com_receiver is None:
            raise ValueError(f"Receiver for app root {app_root_name} is not found.")

        return com_receiver
    

    def app_root_mappping(self, app_root_name:str) -> str:
        """
        Map the app root to the corresponding app.
        :return: The CLSID of the COM object.
        """
        
        win_com_map = {
            "WINWORD.EXE": "Word.Application",
            "EXCEL.EXE": "Excel.Application",
            "POWERPNT.EXE": "PowerPoint.Application",
            "olk.exe": "Outlook.Application"
        }

        return win_com_map.get(app_root_name, None)