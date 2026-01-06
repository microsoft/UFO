#!/usr/bin/env python3
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
PowerPoint MCP Server
Provides MCP server for PowerPoint automation operations.
"""

import platform
import sys

# Platform check - this module requires Windows
if platform.system() != "Windows":
    import logging

    logging.warning(
        f"ppt_wincom_mcp_server.py requires Windows platform. Current: {platform.system()}. Skipping module initialization."
    )
    # Exit module loading gracefully
    sys.exit(0)

from typing import Annotated, Any, Dict, List, Optional

from fastmcp import FastMCP
from fastmcp.client import Client
from pydantic import Field

from ufo.agents.processors.schemas.actions import ActionCommandInfo
from ufo.automator.action_execution import ActionExecutor
from ufo.automator.puppeteer import AppPuppeteer
from ufo.client.mcp.mcp_registry import MCPRegistry
from ufo.config import get_config

# Get config
configs = get_config()


# Singleton UI server state
class UIServerState:
    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(UIServerState, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self.puppeteer: Optional[AppPuppeteer] = None
            UIServerState._initialized = True


@MCPRegistry.register_factory_decorator("PowerPointCOMExecutor")
def create_powerpoint_mcp_server(process_name: str) -> FastMCP:
    """
    Create and return the PowerPoint MCP server instance.
    :return: FastMCP instance for PowerPoint operations.
    """
    # Get singleton UI state instance
    ui_state = UIServerState()
    executor = ActionExecutor()

    ui_state.puppeteer = AppPuppeteer(
        process_name=process_name,
        app_root_name="POWERPNT.EXE",
    )

    ui_state.puppeteer.receiver_manager.create_api_receiver(
        app_root_name="POWERPNT.EXE",
        process_name=process_name,
    )

    def _execute_action(action: ActionCommandInfo) -> Dict[str, Any]:
        """
        Execute a single UI action.
        :param action: ActionCommandInfo object to execute.
        :return: Execution result as a dictionary.
        """
        if not ui_state.puppeteer:
            raise ValueError("UI state not initialized.")

        return executor.execute(action, ui_state.puppeteer, control_dict={})

    mcp = FastMCP("UFO PowerPoint MCP Server")

    @mcp.tool(tags={"PowerPoint"})
    def set_background_color(
        color: Annotated[
            str,
            Field(
                description="The hex color code (in RGB format) to set the background color."
            ),
        ],
        slide_index: Annotated[
            Optional[List[int]],
            Field(
                description="The list of slide indexes to set the background color. If None, set the background color for all slides."
            ),
        ] = None,
    ) -> Annotated[
        str,
        Field(
            description="A message indicating the success or failure of setting the background color."
        ),
    ]:
        """
        A fast way to set the background color of one or more slides in a PowerPoint presentation.
        You should use this API to save your work since it is more efficient than using UI.
        """
        action = ActionCommandInfo(
            function="set_background_color",
            arguments={"color": color, "slide_index": slide_index},
        )

        return _execute_action(action)

    @mcp.tool(tags={"PowerPoint"})
    def save_as(
        file_dir: Annotated[
            str,
            Field(
                description="The directory to save the file. If not specified, the current directory will be used."
            ),
        ] = "",
        file_name: Annotated[
            str,
            Field(
                description="The name of the file without extension. If not specified, the name of the current document will be used."
            ),
        ] = "",
        file_ext: Annotated[
            str,
            Field(
                description="The extension of the file. If not specified, the default extension is '.pptx'."
            ),
        ] = "",
        current_slide_only: Annotated[
            bool,
            Field(
                description="This only applies to '.jpg', '.png', '.gif', '.bmp' and '.tiff' formats. If True, only the current slide will be saved to a PNG file. If False, all slides will be saved into a directory containing multiple PNG files."
            ),
        ] = False,
    ) -> Annotated[
        str,
        Field(
            description="A message indicating the success or failure of saving the document."
        ),
    ]:
        """
        The fastest way to save or export the PowerPoint presentation to a specified file format with one command.
        You should use this API to save your work since it is more efficient than manually saving the document.
        """
        action = ActionCommandInfo(
            function="save_as",
            arguments={
                "file_dir": file_dir,
                "file_name": file_name,
                "file_ext": file_ext,
                "current_slide_only": current_slide_only,
            },
        )

        return _execute_action(action)

    return mcp


async def main():
    """
    Main function to run the MCP server.
    """
    process_name = "powerpoint"

    mcp_server = create_powerpoint_mcp_server(process_name)

    async with Client(mcp_server) as client:
        print(f"Starting MCP server for {process_name}...")
        tool_list = await client.list_tools()
        for tool in tool_list:
            print(f"Available tool: {tool.name} - {tool.description}")

        # Example usage: set background color for first slide
        result = await client.call_tool(
            "set_background_color", arguments={"color": "FFFFFF", "slide_index": [1]}
        )

        print(f"Set background color result: {result.data}")


if __name__ == "__main__":
    import asyncio

    # Run the main function in the event loop
    asyncio.run(main())
