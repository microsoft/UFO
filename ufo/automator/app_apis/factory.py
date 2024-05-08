# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from typing import Type

from ufo.automator.app_apis.basic import WinCOMReceiverBasic
from ufo.automator.app_apis.word.wordclient import WordWinCOMReceiver
from ufo.automator.basic import ReceiverFactory
from ufo.utils import print_with_color


class COMReceiverFactory(ReceiverFactory):
    """
    The factory class for the COM receiver.
    """

    def create_receiver(
        self, app_root_name: str, process_name: str
    ) -> WinCOMReceiverBasic:
        """
        Create the wincom receiver.
        :param app_root_name: The app root name.
        :param process_name: The process name.
        :return: The receiver.
        """

        com_receiver = self.__com_client_mapper(app_root_name)
        clsid = self.__app_root_mappping(app_root_name)

        if clsid is None or com_receiver is None:
            print_with_color(
                f"Win32COM API is not supported for {process_name}.", "yellow"
            )
            return None

        return com_receiver(app_root_name, process_name, clsid)

    def __com_client_mapper(self, app_root_name: str) -> Type[WinCOMReceiverBasic]:
        """
        Map the app root to the corresponding COM client.
        :param app_root_name: The app root name.
        :return: The COM client.
        """
        win_com_client_mapping = {"WINWORD.EXE": WordWinCOMReceiver}

        com_receiver = win_com_client_mapping.get(app_root_name, None)

        return com_receiver

    def __app_root_mappping(self, app_root_name: str) -> str:
        """
        Map the app root to the corresponding app.
        :return: The CLSID of the COM object.
        """

        win_com_map = {
            "WINWORD.EXE": "Word.Application",
            "EXCEL.EXE": "Excel.Application",
            "POWERPNT.EXE": "PowerPoint.Application",
            "olk.exe": "Outlook.Application",
        }

        return win_com_map.get(app_root_name, None)
