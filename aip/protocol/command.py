# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Command Protocol

Handles command execution at a fine-grained level.
"""

import logging
from typing import List

from aip.messages import Command, Result
from aip.protocol.base import AIPProtocol


class CommandProtocol(AIPProtocol):
    """
    Command execution protocol for AIP.

    Provides fine-grained command execution with:
    - Typed arguments
    - Result validation
    - Error propagation
    - Batch command support
    """

    def __init__(self, *args, **kwargs):
        """Initialize command protocol."""
        super().__init__(*args, **kwargs)
        self.logger = logging.getLogger(f"{__name__}.CommandProtocol")

    def validate_command(self, cmd: Command) -> bool:
        """
        Validate a command structure.

        :param cmd: Command to validate
        :return: True if valid, False otherwise
        """
        if not cmd.tool_name:
            self.logger.error("Command missing tool_name")
            return False
        if not cmd.tool_type:
            self.logger.error("Command missing tool_type")
            return False
        return True

    def validate_commands(self, commands: List[Command]) -> bool:
        """
        Validate a batch of commands.

        :param commands: Commands to validate
        :return: True if all valid, False otherwise
        """
        return all(self.validate_command(cmd) for cmd in commands)

    def validate_result(self, result: Result) -> bool:
        """
        Validate a command result.

        :param result: Result to validate
        :return: True if valid, False otherwise
        """
        if not result.status:
            self.logger.error("Result missing status")
            return False
        return True

    def validate_results(self, results: List[Result]) -> bool:
        """
        Validate a batch of results.

        :param results: Results to validate
        :return: True if all valid, False otherwise
        """
        return all(self.validate_result(res) for res in results)
