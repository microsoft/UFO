import asyncio
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union

from fastmcp import Client, FastMCP
from pydantic import BaseModel
from ufo.client.mcp import DefaultMCPServerManager
from ufo.config import Config
from ufo.cs.contracts import Command

configs = Config.get_instance().config_data

if configs is not None:
    CONTROL_BACKEND = configs.get("CONTROL_BACKEND", ["uia"])
    BACKEND = "win32" if "win32" in CONTROL_BACKEND else "uia"


class MCPToolCall(BaseModel):
    """
    Information about a tool registered with the computer.
    """

    tool_key: str  # Unique key for the tool, e.g., "namespace.tool_name"
    tool_name: str  # Name of the tool
    namespace: str  # Namespace of the tool, same as the MCP server namespace
    tool_type: str  # Type of the tool (e.g., "action", "data_collection")
    description: str  # Description of the tool
    parameters: Dict[str, Any]  # Parameters for the tool, if any
    mcp_server: Union[
        str, FastMCP
    ]  # The url string (for HTTP servers) or FastMCP instance (for local in-memory servers)


class Computer(ABC):
    """
    Basic class for managing computer operations and actions.
    """

    _tools_registry: Dict[str, MCPToolCall] = {}
    _data_collection_namespaces: str = "data_collection"
    _action_namespaces: str = "action"

    def __init__(self, name: str):
        self._name = name

        self._data_collection_servers = {}
        self._action_servers = {}

        self._agent_name = "HostAgent/HostAgent"
        self.local_mcp_server_manager = DefaultMCPServerManager()

    async def async_init(self) -> None:
        """
        Asynchronous initialization of the computer.
        """
        self._data_collection_servers = await self._init_data_collection_servers()
        self._action_servers = await self._init_action_servers()

        await asyncio.gather(
            self.register_mcp_servers(
                self._data_collection_servers,
                tool_type=self._data_collection_namespaces,
            ),
            self.register_mcp_servers(
                self._action_servers, tool_type=self._action_namespaces
            ),
        )

    def create_mcp_server(
        self, mcp_config: Dict[str, Any], *args, **kwargs
    ) -> Union[str, FastMCP]:
        """
        Create an MCP server based on the type and parameters.
        :param mcp_config: Configuration dictionary for the MCP server.
        :return: A string URL for HTTP servers or a FastMCP instance for local servers.
        """

        namespace = mcp_config.get("namespace", "default_mcp_server")
        server_type = mcp_config.get("type", "http")
        host = mcp_config.get("host", "localhost")
        port = mcp_config.get("port", 8000)

        if server_type == "http":
            return f"http://{host}:{port}/mcp"
        elif server_type == "local":
            return self.local_mcp_server_manager.start_server(
                namespace=namespace, *args, **kwargs
            )
        else:
            raise ValueError(f"Unsupported server type: {server_type}")

    def _init_data_collection_servers(self) -> Dict[str, str]:
        """
        Initialize data collection servers for the computer of the
        """
        # Get the base directory for UFO2
        for data_collection_server in configs.get("data_collection_servers", []):
            # If the server is set to auto-start, create a FastMCP server
            namespace = data_collection_server.get("namespace")
            if not namespace:
                namespace = "default_data_collection"
            mcp_server = self.create_mcp_server(data_collection_server)
            self._data_collection_servers[namespace] = mcp_server

    def _init_action_servers(self) -> Dict[str, str]:
        """
        Initialize action servers for the computer.
        """
        # Get the base directory for UFO2
        for action_server in configs.get("action_servers", []):
            # If the server is set to auto-start, create a FastMCP server
            namespace = action_server.get("namespace")
            if not namespace:
                namespace = "default_action"
            mcp_server = self.create_mcp_server(action_server)
            self._data_collection_servers[namespace] = mcp_server

    async def _run_action(self, tool_call: MCPToolCall) -> Any:
        """
        Run a one-step action on the computer.
        :param tool_call: The tool call to run.
        :return: The result of the single action.
        """

        tool_key = tool_call.tool_key
        tool_info = self._tools_registry.get(tool_key, None)
        if not tool_info:
            raise ValueError(f"Tool {tool_key} is not registered.")

        # Check if the tool is a meta tool for listing tools
        if tool_info.tool_type == "meta" and tool_info.tool_name == "list_tools":
            # Special case for listing tools, which does not require a server call
            return self.list_tools(
                tool_type=tool_info.tool_type, namespace=tool_info.namespace
            )

        server = tool_info.server
        params = tool_info.parameters or {}
        async with Client(server) as client:
            result = await client.call_tool(name=tool_call, arguments=params)
            return result

    async def run_actions(self, tool_calls: List[MCPToolCall]) -> Any:
        """
        Run an action on the computer.
        :param tool_calls: The list of tool calls to run.
        :return: The result of the action.
        """

        results = []
        for tool_call in tool_calls:
            result = await self._run_action(tool_call)
            results.append(result)

        return results

    async def register_mcp_servers(
        self, server_dict: Dict[str, str], tool_type: str
    ) -> None:
        """
        Register a tool with the computer.
        :param server_dict: A dictionary mapping namespaces to MCP servers.
        :param tool_type: The type of the tool (e.g., "action", "data_collection").
        :return: None
        """
        tasks = [
            self.register_one_mcp_server(namespace, tool_type, server)
            for namespace, server in server_dict.items()
        ]

        # Run all registration tasks concurrently
        await asyncio.gather(*tasks)

    async def register_one_mcp_server(
        self, namespace: str, tool_type: str, mcp_server: Union[str, FastMCP]
    ) -> None:
        """
        Register tools from a single MCP server.
        :param namespace: The namespace of the tools.
        :param tool_type: The type of the tools (e.g., "action", "data_collection").
        :param server: The MCP server to register tools from.
        :return: None
        """

        async with Client(mcp_server) as client:
            tools = await client.list_tools()
            for tool in tools:
                tool_key = f"{tool_type}.{tool.name}"
                if tool_key not in self._tools_registry:
                    self._register_tool(
                        tool_key=tool_key,
                        tool_name=tool.name,
                        namespace=namespace,
                        tool_type=tool_type,
                        description=tool.description,
                        parameters=(
                            tool.inputSchema
                            if hasattr(tool, "inputSchema") and tool.inputSchema
                            else {}
                        ),
                        mcp_server=mcp_server,
                    )
                else:
                    print(f"Tool {tool_key} is already registered.")

    def _register_tool(
        self,
        tool_key: str,
        tool_name: str,
        namespace: str,
        tool_type: str,
        description: str,
        parameters: Dict[str, Any],
        mcp_server: Union[str, FastMCP],
    ) -> None:
        """
        Register a tool with the computer.
        :param tool_name: The name of the tool.
        :param namespace: The namespace of the tool.
        :param tool_type: The type of the tool (e.g., "action", "
        :param description: The description of the tool.
        :param parameters: The parameters for the tool.
        :param mcp_server: The MCP server where the tool is registered.
        """
        if tool_name in self._tools_registry:
            raise ValueError(f"Tool {tool_key} is already registered.")

        tool_info = MCPToolCall(
            tool_key=tool_key,
            tool_name=tool_name,
            description=description,
            namespace=namespace,
            tool_type=tool_type,
            parameters=parameters,
            mcp_server=mcp_server,
        )
        self._tools_registry[tool_key] = tool_info

    async def add_server(
        self,
        namespace: str,
        mcp_server: Union[str, FastMCP],
        tool_type: Optional[str] = None,
    ) -> None:
        """
        Add a server and its tools to the computer.
        :param namespace: The namespace of the server.
        :param server: The MCP server to add.
        :param tool_type: Optional type of tools (e.g., "action", "data_collection").
        :return: None
        """
        if tool_type is None:
            raise ValueError(
                f"Tool type must be specified (i.e., {self._data_collection_namespaces} or {self._action_namespaces})."
            )

        if tool_type == self._data_collection_namespaces:
            self._data_collection_servers[namespace] = mcp_server
        elif tool_type == self._action_namespaces:
            self._action_servers[namespace] = mcp_server
        else:
            raise ValueError(
                f"Invalid tool type: {tool_type}. Must be one of {self._data_collection_namespaces} or {self._action_namespaces}."
            )

        await self.register_one_mcp_server(namespace, tool_type, mcp_server)

    async def delete_server(
        self, namespace: str, tool_type: Optional[str] = None
    ) -> None:
        """
        Delete a server and its tools from the computer.
        :param namesspace: The namespace of the server to delete.
        :param tool_type: Optional type of tools to delete (e.g., "action", "data_collection").
        :return: None
        """
        keys_to_remove = [
            key
            for key, tool in self._tools_registry.items()
            if tool.namespace == namespace
            and (tool_type is None or tool.tool_type == tool_type)
        ]

        for key in keys_to_remove:
            del self._tools_registry[key]

        # Remove the server from the action or data collection servers
        if tool_type == self._data_collection_namespaces:
            self._data_collection_servers.pop(namespace, None)
        elif tool_type == self._action_namespaces:
            self._action_servers.pop(namespace, None)

    async def agent_update(self, agent_name: str):
        """
        Update the agent name for the computer.
        :param agent_name: The new name for the agent.
        """
        if not agent_name:
            raise ValueError("Agent name cannot be empty.")
        if agent_name == self._agent_name:
            # No change needed
            return

    def list_tools(
        self, tool_type: Optional[str] = None, namespace: Optional[str] = None
    ) -> List[MCPToolCall]:
        """
        Get the available tools of a specific type (action or data_collection).
        :param tool_type: The type of tools to retrieve (e.g., "action", "data_collection").
        :param namespace: Optional namespace to filter tools.
        :return: A list of MCPToolCall objects representing the available tools.
        """
        return [
            tool
            for tool in self._tools_registry.values()
            if (tool_type is None or tool.tool_type == tool_type)
            and (namespace is None or tool.namespace == namespace)
        ]

    def command2tool(self, command: Command) -> MCPToolCall:
        """
        Convert a Command object to an MCPToolCall object.
        :param command: The Command object to convert.
        :return: An MCPToolCall object representing the tool call.
        """
        tool_name = command.tool_name
        tool_key = f"{command.tool_type}.{tool_name}"
        tool_info = self._tools_registry.get(tool_key, None)

        if not tool_info:
            raise ValueError(f"Tool {tool_key} is not registered.")
        return tool_info

    @property
    def agent_name(self) -> str:
        """
        Get the name of the agent.
        :return: The name of the agent.
        """
        return self._agent_name

    @agent_name.setter
    def agent_name(self, name: str):
        """
        Set the name of the agent.
        :param name: The name to set for the agent.
        """
        self._agent_name = name

    @property
    def data_collection_servers(self) -> Dict[str, FastMCP]:
        """
        Get the data collection servers for the computer.
        """

        return self._data_collection_servers

    @property
    def action_servers(self) -> Dict[str, FastMCP]:
        """
        Get the action servers for the computer.
        """

        return self._action_servers

    @property
    def name(self) -> str:
        """
        Get the name of the computer
        """
        return self._name
