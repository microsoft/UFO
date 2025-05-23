# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.


from abc import abstractmethod
from typing import Dict, List, Type

import win32com.client

from ufo.automator.basic import CommandBasic, ReceiverBasic


class WinCOMReceiverBasic(ReceiverBasic):
    """
    The base class for Windows COM client.
    """

    _command_registry: Dict[str, Type[CommandBasic]] = {}

    def __init__(self, app_root_name: str, process_name: str, clsid: str) -> None:
        """
        Initialize the Windows COM client.
        :param app_root_name: The app root name.
        :param process_name: The process name.
        :param clsid: The CLSID of the COM object.
        """

        self.app_root_name = app_root_name
        self.process_name = process_name

        self.clsid = clsid

        self.client = win32com.client.Dispatch(self.clsid)
        self.com_object = self.get_object_from_process_name()

    @abstractmethod
    def get_object_from_process_name(self) -> win32com.client.CDispatch:
        """
        Get the object from the process name.
        """
        pass

    def get_suffix_mapping(self) -> Dict[str, str]:
        """
        Get the suffix mapping.
        :return: The suffix mapping.
        """
        suffix_mapping = {
            "WINWORD.EXE": "docx",
            "EXCEL.EXE": "xlsx",
            "POWERPNT.EXE": "pptx",
            "olk.exe": "msg",
        }

        return suffix_mapping.get(self.app_root_name, None)

    def app_match(self, object_name_list: List[str]) -> str:
        """
        Check if the process name matches the app root.
        :param object_name_list: The list of object name.
        :return: The matched object name.
        """

        suffix = self.get_suffix_mapping()

        if self.process_name.endswith(suffix):
            clean_process_name = self.process_name[: -len(suffix)]
        else:
            clean_process_name = self.process_name

        if not object_name_list:
            return ""

        return max(
            object_name_list,
            key=lambda x: self.longest_common_substring_length(clean_process_name, x),
        )

    @property
    def full_path(self) -> str:
        """
        Get the full path of the process.
        :return: The full path of the process.
        """
        try:
            full_path = self.com_object.FullName
            return full_path
        except:
            return ""

    def save(self) -> None:
        """
        Save the current state of the app.
        """
        try:
            self.com_object.Save()
        except:
            pass

    def save_to_xml(self, file_path: str) -> None:
        """
        Save the current state of the app to XML.
        :param file_path: The file path to save the XML.
        """
        try:
            self.com_object.SaveAs(file_path, self.xml_format_code)
        except:
            pass

    def close(self) -> None:
        """
        Close the app.
        """
        try:
            self.com_object.Close()
        except:
            pass

    @property
    def type_name(self):
        return "COM"

    @property
    def xml_format_code(self) -> int:
        pass

    @staticmethod
    def longest_common_substring_length(str1: str, str2: str) -> int:
        """
        Get the longest common substring of two strings.
        :param str1: The first string.
        :param str2: The second string.
        :return: The length of the longest common substring.
        """

        m = len(str1)
        n = len(str2)

        dp = [[0] * (n + 1) for _ in range(m + 1)]

        max_length = 0

        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if str1[i - 1] == str2[j - 1]:
                    dp[i][j] = dp[i - 1][j - 1] + 1
                    if dp[i][j] > max_length:
                        max_length = dp[i][j]
                else:
                    dp[i][j] = 0

        return max_length


class WinCOMCommand(CommandBasic):
    """
    The abstract command interface.
    """

    def __init__(self, receiver: WinCOMReceiverBasic, params=None) -> None:
        """
        Initialize the command.
        :param receiver: The receiver of the command.
        """
        self.receiver = receiver
        self.params = params if params is not None else {}

    @abstractmethod
    def execute(self):
        pass
