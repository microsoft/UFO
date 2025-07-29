#!/usr/bin/env python3
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
CLI MCP Server
Provides MCP server for command line operations:
- Application launching via command execution
"""

import subprocess
import time

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError

from ufo.config import get_config

# Get config
configs = get_config()


def create_cli_mcp_server():
    """
    Create and return the CLI MCP server instance.
    :return: FastMCP instance for CLI operations.
    """

    cli_mcp = FastMCP("UFO CLI MCP Server")

    @cli_mcp.tool()
    def launch_application(
        bash_command: str,
    ) -> None:
        """
        Launch an application using the provided bash command.
        :param bash_command: The command to execute to launch the application.
        :return: None
        """

        if not bash_command:
            raise ToolError("Bash command cannot be empty.")

        try:
            # Create an AppPuppeteer instance to launch the application
            subprocess.Popen(bash_command, shell=True)
            time.sleep(5)  # Wait for the application to launch
        except Exception as e:
            raise ToolError(f"Failed to launch application: {str(e)}")

    return cli_mcp


# Registry decorators for automatic registration
try:
    from ufo.client.mcp.mcp_registry import MCPRegistry

    @MCPRegistry.register_factory_decorator("CommandLineExecutor")
    def create_command_line_executor_factory() -> FastMCP:
        """
        Factory function to create the Command Line Executor MCP server.
        :return: FastMCP instance for command line executor operations.
        """
        return create_cli_mcp_server()

except ImportError:
    print("Warning: MCPRegistry not found. CLI MCP servers will not be registered.")
