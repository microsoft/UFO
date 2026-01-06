#!/usr/bin/env python3
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
UI MCP Servers
Provides two MCP servers:
1. UI Data MCP Server - for data retrieval operations
2. UI Action MCP Server - for UI automation actions
Both servers share the same UI state for coordinated operations.
"""

import platform
import sys

# Platform check - this module requires Windows
if platform.system() != "Windows":
    import logging

    logging.warning(
        f"word_wincom_mcp_server.py requires Windows platform. Current: {platform.system()}. Skipping module initialization."
    )
    # Exit module loading gracefully
    sys.exit(0)

from typing import Annotated, Any, Dict, Optional

from fastmcp import FastMCP
from fastmcp.client import Client
from pydantic import Field

from ufo.agents.processors.schemas.actions import ActionCommandInfo
from ufo.automator.action_execution import ActionExecutor
from ufo.automator.puppeteer import AppPuppeteer
from ufo.config import get_config
from ufo.client.mcp.mcp_registry import MCPRegistry

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


@MCPRegistry.register_factory_decorator("WordCOMExecutor")
def create_word_mcp_server(process_name: str, *args, **kwargs) -> FastMCP:
    """
    Create and return the AppAgent Action MCP server instance.
    :return: FastMCP instance for AppAgent action operations.
    """
    # Get singleton UI state instance
    ui_state = UIServerState()
    executor = ActionExecutor()

    ui_state.puppeteer = AppPuppeteer(
        process_name=process_name,
        app_root_name="WINWORD.EXE",
    )

    ui_state.puppeteer.receiver_manager.create_api_receiver(
        app_root_name="WINWORD.EXE",
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

    mcp = FastMCP("UFO UI AppAgent Action MCP Server")

    @mcp.tool(tags={"AppAgent"})
    def insert_table(
        rows: Annotated[int, Field(description="The number of rows in the table.")],
        columns: Annotated[
            int, Field(description="The number of columns in the table.")
        ],
    ) -> Annotated[
        str, Field(description="A message indicating the result of the operation.")
    ]:
        """
        Insert a table to a Word document.
        """
        action = ActionCommandInfo(
            function="insert_table",
            arguments={"rows": rows, "columns": columns},
        )

        return _execute_action(action)

    @mcp.tool(tags={"AppAgent"})
    def select_text(
        text: Annotated[str, Field(description="The exact text to be selected.")],
    ) -> Annotated[
        str,
        Field(
            description="A string of the selected text if successful, otherwise a text not found message."
        ),
    ]:
        """
        Select the text in a Word document for further operations, such as changing the font size or color.
        """
        action = ActionCommandInfo(
            function="select_text",
            arguments={"text": text},
        )

        return _execute_action(action)

    @mcp.tool(tags={"AppAgent"})
    def select_table(
        number: Annotated[
            int, Field(description="The index number of the table to be selected.")
        ],
    ) -> Annotated[
        str,
        Field(
            description="A string of the selected table if successful, otherwise an out of range message."
        ),
    ]:
        """
        Select a table in a Word document for further operations, such as deleting the table or changing the border color.
        """
        action = ActionCommandInfo(
            function="select_table",
            arguments={"number": number},
        )

        return _execute_action(action)

    @mcp.tool(tags={"AppAgent"})
    def select_paragraph(
        start_index: Annotated[
            int, Field(description="The start index of the paragraph to be selected.")
        ],
        end_index: Annotated[
            int,
            Field(
                description="The end index of the paragraph, if ==-1, select to the end of the document."
            ),
        ],
        non_empty: Annotated[
            bool, Field(description="If True, select the non-empty paragraphs only.")
        ] = True,
    ) -> Annotated[
        str, Field(description="A message indicating the result of the operation.")
    ]:
        """
        Select a paragraph in a Word document for further operations, such as changing the alignment or indentation.
        """
        action = ActionCommandInfo(
            function="select_paragraph",
            arguments={
                "start_index": start_index,
                "end_index": end_index,
                "non_empty": non_empty,
            },
        )

        return _execute_action(action)

    @mcp.tool(tags={"AppAgent"})
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
                description="The extension of the file. If not specified, the default extension is '.pdf'."
            ),
        ] = "",
    ) -> Annotated[
        str,
        Field(
            description="A message indicating the success or failure of saving the document."
        ),
    ]:
        """
        The fastest way to save or export the Word document to a specified file format with one command.
        You should use this API to save your work since it is more efficient than manually saving the document.
        """
        action = ActionCommandInfo(
            function="save_as",
            arguments={
                "file_dir": file_dir,
                "file_name": file_name,
                "file_ext": file_ext,
            },
        )

        return _execute_action(action)

    @mcp.tool(tags={"AppAgent"})
    def set_font(
        font_name: Annotated[
            Optional[str],
            Field(
                description="The name of the font (e.g., 'Arial', 'Times New Roman', '宋体'). If None, the font name will not be changed."
            ),
        ] = None,
        font_size: Annotated[
            Optional[int],
            Field(
                description="The font size (e.g., 12). If None, the font size will not be changed."
            ),
        ] = None,
    ) -> Annotated[
        str,
        Field(
            description="A message indicating the font and font size changes if successful, otherwise a message indicating no text selected."
        ),
    ]:
        """
        Set the font of the selected text in a Word document. The text must be selected before calling this command.
        """
        action = ActionCommandInfo(
            function="set_font",
            arguments={"font_name": font_name, "font_size": font_size},
        )

        return _execute_action(action)

    return mcp


async def main():
    """
    Main function to run the MCP server.
    """
    process_name = "word"

    mcp_server = create_word_mcp_server(process_name)

    async with Client(mcp_server) as client:
        print(f"Starting MCP server for {process_name}...")
        tool_list = await client.list_tools()
        for tool in tool_list:
            print(f"Available tool: {tool.name} - {tool.description}")

        result = await client.call_tool(
            "insert_table", arguments={"rows": 3, "columns": 2}
        )

        print(f"Insert table result: {result.data}")


if __name__ == "__main__":
    import asyncio

    # Run the main function in the event loop
    asyncio.run(main())
