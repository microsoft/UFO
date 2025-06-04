#!/usr/bin/env python3
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Base MCP Server
Provides the common functionality for all UFO MCP servers.
"""

import os
import sys
import yaml
from typing import Dict, Any
from fastmcp import FastMCP

# Add UFO2 to the path
ufo_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if ufo_root not in sys.path:
    sys.path.insert(0, ufo_root)

from ufo.automator.app_apis.factory import MCPReceiverFactory
from ufo.utils import print_with_color


class BaseMCPServer:
    """
    Base class for all UFO MCP servers.
    """
    
    def __init__(self, app_namespace: str, server_name: str = None, port: int = None):
        """
        Initialize the base MCP server.
        :param app_namespace: The application namespace (word, excel, powerpoint, web, shell)
        :param server_name: Optional custom server name
        :param port: Optional port number for HTTP mode
        """
        self.app_namespace = app_namespace
        self.server_name = server_name or f"ufo-{app_namespace}"
        self.port = port
        
        # Initialize FastMCP
        self.mcp = FastMCP(self.server_name)
        
        # Load instructions and create receiver
        self.instructions = self._load_instructions()
        self.receiver = self._create_receiver()
        
        # Register tools
        self._register_tools()
      
    def _load_instructions(self) -> Dict[str, Any]:
        """
        Load instructions from YAML file.
        :return: Instructions dictionary
        """
        try:
            instructions_path = os.path.join(
                os.path.dirname(__file__),
                "..", "config", "mcp_instructions", f"{self.app_namespace}.yaml"
            )
            if os.path.exists(instructions_path):
                with open(instructions_path, 'r') as f:
                    instructions = yaml.safe_load(f)
                print_with_color(f"Loaded instructions for {self.app_namespace}", "green")
                return instructions
            else:
                print_with_color(f"Instructions file not found: {instructions_path}", "yellow")
                return {"tools": []}
        except Exception as e:
            print_with_color(f"Error loading instructions: {e}", "red")
            return {"tools": []}
    
    def _create_receiver(self):
        """
        Create the application receiver using the factory.
        :return: The receiver instance
        """
        try:
            factory = MCPReceiverFactory()
            receiver = factory.create_receiver(self.app_namespace)  # Use create_receiver method
            if receiver:
                print_with_color(f"Created {self.app_namespace} receiver", "green")
                return receiver
            else:
                print_with_color(f"Failed to create {self.app_namespace} receiver", "red")
                return None
        except Exception as e:
            print_with_color(f"Error creating receiver: {e}", "red")
            return None
    
    def _register_tools(self):
        """
        Register MCP tools based on the loaded instructions.
        """
        if not self.instructions or "tools" not in self.instructions:
            print_with_color(f"No tools found in instructions for {self.app_namespace}", "yellow")
            return
        
        for tool_def in self.instructions["tools"]:
            tool_name = tool_def.get("name")
            if tool_name:
                self._register_tool(tool_def)
    
    def _register_tool(self, tool_def: Dict[str, Any]):
        """
        Register a single MCP tool.
        :param tool_def: Tool definition from instructions
        """
        tool_name = tool_def["name"]
        description = tool_def.get("description", f"Execute {tool_name}")
        parameters = tool_def.get("parameters", [])
        
        # Create a dynamic function for this tool with explicit parameters
        # to avoid **kwargs which FastMCP doesn't support
        def create_tool_function(name: str):
            def tool_function(request: str = "{}") -> Dict[str, Any]:
                """Dynamic tool function for MCP."""
                try:
                    # Parse the request as JSON if it's a string
                    if isinstance(request, str):
                        import json
                        tool_args = json.loads(request) if request.strip() else {}
                    else:
                        tool_args = request if isinstance(request, dict) else {}
                except json.JSONDecodeError:
                    tool_args = {"raw_input": request}
                
                return self._execute_tool(name, tool_args)
            
            # Set function attributes for FastMCP
            tool_function.__name__ = name
            tool_function.__doc__ = description
            return tool_function
        
        # Register the tool with FastMCP
        try:
            tool_func = create_tool_function(tool_name)
            self.mcp.tool()(tool_func)
            print_with_color(f"Registered tool: {tool_name}", "green")
        except Exception as e:
            print_with_color(f"Error registering tool {tool_name}: {e}", "red")
    
    def _execute_tool(self, tool_name: str, tool_args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a tool using the receiver.
        :param tool_name: Name of the tool to execute
        :param tool_args: Arguments for the tool
        :return: Tool execution result
        """
        if not self.receiver:
            return {
                "success": False,
                "error": f"No receiver available for {self.app_namespace}",
                "tool_name": tool_name,
                "namespace": self.app_namespace
            }
        
        try:
            result = self.receiver.execute_tool(tool_name, tool_args)
            print_with_color(f"Executed {tool_name} with result: {result.get('success', False)}", "green")
            return result
        except Exception as e:
            print_with_color(f"Error executing {tool_name}: {e}", "red")
            return {
                "success": False,
                "error": f"Error executing tool: {str(e)}",
                "tool_name": tool_name,
                "namespace": self.app_namespace
            }
    
    def run(self):
        """
        Start the MCP server.
        """
        print_with_color(f"Starting {self.app_namespace} MCP server: {self.server_name}", "blue")
        
        if self.instructions:
            print_with_color(f"Loaded {len(self.instructions.get('tools', []))} tools", "green")
        
        try:
            if self.port:
                # If port is specified, run as HTTP server
                print_with_color(f"Running on port {self.port}", "blue")
                # Note: FastMCP typically runs via stdio, but we can extend this for HTTP
                self.mcp.run(transport="sse", port=self.port)
            else:
                # Run via stdio (standard MCP protocol)
                self.mcp.run()
        except KeyboardInterrupt:
            print_with_color(f"\nShutting down {self.app_namespace} MCP server", "yellow")
        except Exception as e:
            print_with_color(f"Error running server: {e}", "red")
            raise
    
    @property
    def app(self):
        """
        Get the FastMCP app instance.
        :return: FastMCP app
        """
        return self.mcp
    
    def get_tools(self):
        """
        Get list of registered tools.
        :return: List of tool names
        """
        # Try different ways to access FastMCP tools
        if hasattr(self.mcp, '_tools'):
            return list(self.mcp._tools.keys())
        elif hasattr(self.mcp, 'tools'):
            return list(self.mcp.tools.keys())
        elif hasattr(self.mcp, '_handlers'):
            # Look for tool handlers
            tools = []
            for handler_type, handlers in self.mcp._handlers.items():
                if 'tool' in handler_type.lower():
                    tools.extend(handlers.keys())
            return tools
        else:
            # Fall back to instruction-based tool list
            if self.instructions and "tools" in self.instructions:
                return [tool.get("name") for tool in self.instructions["tools"] if tool.get("name")]
            return []


def create_mcp_server(app_namespace: str, server_name: str = None, port: int = None) -> BaseMCPServer:
    """
    Factory function to create an MCP server for a specific application.
    :param app_namespace: The application namespace
    :param server_name: Optional custom server name
    :param port: Optional port number
    :return: MCP server instance
    """
    return BaseMCPServer(app_namespace, server_name, port)


if __name__ == "__main__":
    # This is a base class, specific servers should be run individually
    print("This is the base MCP server class.")
    print("Run specific application servers like word_mcp_server.py, excel_mcp_server.py, etc.")
