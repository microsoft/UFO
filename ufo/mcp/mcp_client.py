"""
Base MCP Client for communicating with MCP servers.

This client provides the base functionality for MCP protocol communication
that can be used by specialized clients for different types of MCP servers.
"""
import asyncio
import json
import logging
import requests
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urljoin
import urllib.parse
from fastmcp import Client

from ufo.cs.contracts import (
    MCPGetInstructionsAction,
    MCPGetAvailableToolsAction
)

logger = logging.getLogger(__name__)


class MCPClient:
    """
    Base client for communicating with MCP servers.
    
    This client provides general MCP protocol communication functionality
    that can be inherited by specialized clients for different MCP servers.
    """
    
    def __init__(self, host: str = "localhost", port: int = 8000, app_namespace: str = ""):
        """
        Initialize the MCP client.
        
        Args:
            host: The MCP server host
            port: The MCP server port
            app_namespace: The application namespace this client handles
        """
        self.host = host
        self.port = port
        self.app_namespace = app_namespace
        self.base_url = f"http://{host}:{port}"
        self.session = requests.Session()
        
        # Set up session headers
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        
        logger.info(f"Initialized MCP client for {app_namespace} at {self.base_url}")
    def _make_tool_call(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """
        Make a tool call to the MCP server using SSE transport.
        
        Args:
            tool_name: The name of the MCP tool to call
            arguments: The arguments to pass to the tool
            
        Returns:
            The result from the MCP tool execution
            
        Raises:
            Exception: If the MCP server returns an error
        """
        endpoint = f"http://{self.host}:{self.port}/sse"
        
        async def call_tool_async():
            async with Client(endpoint) as client:
                result = await client.call_tool(tool_name, arguments)
                return result
        
        try:
            result = asyncio.run(call_tool_async())
            
            # Handle the result content
            if hasattr(result, 'content') and result.content:
                content = result.content
                if isinstance(content, list) and len(content) > 0:
                    # Handle text content
                    if content[0].get("type") == "text":
                        try:
                            return json.loads(content[0]["text"])
                        except json.JSONDecodeError:
                            return content[0]["text"]
                    # Handle other content types
                    return content[0]
                return content
            else:
                content = result
                if isinstance(content, list) and len(content) > 0:
                    # Handle text content
                    if content[0].type == "text":
                        try:
                            return json.loads(content[0].text)
                        except json.JSONDecodeError:
                            return content[0].text
                    # Handle other content types
                    return content[0]
                return content
            
            # If no content attribute, return the result directly
            return result
            
        except Exception as e:
            logger.error(f"Failed to call MCP tool {tool_name}: {str(e)}")
            raise Exception(f"MCP communication error: {str(e)}")

    def _handle_mcp_get_instructions(self, action: MCPGetInstructionsAction) -> Dict[str, Any]:
        """
        Handle requests for MCP instructions.
        
        This is a base implementation that should be overridden by specialized clients.
        
        Args:
            action: The MCP get instructions action
            
        Returns:
            Dictionary containing instructions information
        """
        if not action.params:
            return {"error": "No MCP get instructions parameters provided"}
        
        params = action.params
        app_namespace = params.app_namespace
        
        # Base implementation - should be overridden by specialized clients
        return {
            "error": f"Instructions not available for app namespace: {app_namespace}",
            "app_namespace": app_namespace
        }

    def _handle_mcp_get_available_tools(self, action: MCPGetAvailableToolsAction) -> Dict[str, Any]:
        """
        Handle requests for available MCP tools.
        
        This is a base implementation that should be overridden by specialized clients.
        
        Args:
            action: The MCP get available tools action
            
        Returns:
            Dictionary containing available tools information
        """
        if not action.params:
            return {"error": "No MCP get available tools parameters provided"}
        
        params = action.params
        app_namespace = params.app_namespace
        
        endpoint = f"http://{self.host}:{self.port}/sse"
        async def get_tools_async():
            async with Client(endpoint) as client:
                tools_result = await client.list_tools()
                return tools_result
        
        try:
            tools = asyncio.run(get_tools_async())
            if not tools:
                return {"error": "No tools available for this app namespace"}
            
            # Convert Tool objects to dictionaries
            tools_dicts = []
            for tool in tools:
                tool_dict = {
                    "name": tool.name,
                    "description": tool.description,
                }
                # Add inputSchema if available
                if hasattr(tool, 'inputSchema') and tool.inputSchema:
                    tool_dict["inputSchema"] = tool.inputSchema
                tools_dicts.append(tool_dict)
            
            return {
                "tools": tools_dicts,
                "app_namespace": app_namespace
            }
        except Exception as e:
            logger.error(f"Failed to get available tools for {app_namespace}: {str(e)}")
            return {
                "error": f"Failed to retrieve tools: {str(e)}",
                "app_namespace": app_namespace
            }

    def test_connection(self) -> bool:
        """
        Test connection to the MCP server.
        
        Returns:
            True if connection is successful, False otherwise
        """
        try:
            response = self.session.get(
                urljoin(self.base_url, "/health"),
                timeout=5
            )
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"MCP server connection test failed: {str(e)}")
            return False

    @classmethod
    def create_client(cls, endpoint: str, app_namespace: str) -> 'MCPClient':
        """
        Factory method to create an MCP client from an endpoint URL.
        
        Args:
            endpoint: The MCP server endpoint URL
            app_namespace: The application namespace
            
        Returns:
            An MCPClient instance
        """
        parsed = urllib.parse.urlparse(endpoint)
        host = parsed.hostname or "localhost"
        port = parsed.port or 8000
        
        return cls(host=host, port=port, app_namespace=app_namespace)
