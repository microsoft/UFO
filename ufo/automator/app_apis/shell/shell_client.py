# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from __future__ import annotations

import subprocess
from typing import Any, Dict, Type

from ufo.automator.basic import CommandBasic, ReceiverBasic


class ShellReceiver(ReceiverBasic):
    """
    The base class for Web COM client using crawl4ai.
    """

    _command_registry: Dict[str, Type[ShellCommand]] = {}

    def __init__(self) -> None:
        """
        Initialize the shell client.
        """

    def run_shell(self, params: Dict[str, Any]) -> Any:
        """
        Run the command.
        :param params: The parameters of the command.
        :return: The result content.
        """
        bash_command = params.get("command")
        powershell_path = 'C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe'
        process = subprocess.Popen(
            bash_command,  # command to run
            stdout=subprocess.PIPE,  # capture stdout
            stderr=subprocess.PIPE,  # capture stderr
            shell=True,
            text=True,
            executable=powershell_path,
        )
        return ""

    @property
    def type_name(self):
        return "SHELL"

    @property
    def xml_format_code(self) -> int:
        return 0  # This might not be applicable for shell commands.


class ShellCommand(CommandBasic):
    """
    The base class for Web commands.
    """

    def __init__(self, receiver: ShellReceiver, params: Dict[str, Any]) -> None:
        """
        Initialize the Web command.
        :param receiver: The receiver of the command.
        :param params: The parameters of the command.
        """
        super().__init__(receiver, params)
        self.receiver = receiver
        self.params = params

    @classmethod
    def name(cls) -> str:
        """
        The name of the command.
        """
        return "shell"


@ShellReceiver.register
class RunShellCommand(ShellCommand):
    """
    The command to run the crawler with various options.
    """

    def execute(self):
        """
        Execute the command to run the crawler.
        :return: The result content.
        """
        return self.receiver.run_shell(params=self.params)

    @classmethod
    def name(cls) -> str:
        """
        The name of the command.
        """
        return "run_shell"
