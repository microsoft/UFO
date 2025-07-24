import asyncio
import copy
import inspect
import json
import logging
import time
from typing import Any, Callable, Dict, List, Optional

# Import UI MCP servers to ensure they're registered in the registry
import ufo.mcp.ui_mcp_server
from fastmcp import Client, FastMCP
from fastmcp.client.client import CallToolResult
from mcp.types import TextContent
from pydantic import BaseModel, ConfigDict
from ufo.client.mcp import BaseMCPServer, MCPServerManager
from ufo.cs.contracts import Command, Result


class MCPToolCall(BaseModel):
    """
    Information about a tool registered with the computer.
    """

    tool_key: str  # Unique key for the tool, e.g., "namespace.tool_name"
    tool_name: str  # Name of the tool
    title: Optional[str] = None  # Title of the tool, if any
    namespace: str  # Namespace of the tool, same as the MCP server namespace
    tool_type: str  # Type of the tool (e.g., "action", "data_collection")
    description: str  # Description of the tool
    tool_schema: Optional[Dict[str, Any]] = None  # Schema for the tool, if any
    parameters: Optional[Dict[str, Any]] = None  # Parameters for the tool, if any
    mcp_server: BaseMCPServer  # The BaseMCPServer instance where the tool is registered

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @property
    def tool_info(self) -> Dict[str, Any]:
        """
        Get a dictionary representation of the tool call.
        :return: Dictionary with tool information.
        """
        return {
            "tool_key": self.tool_key,
            "tool_name": self.tool_name,
            "title": self.title,
            "namespace": self.namespace,
            "tool_type": self.tool_type,
            "description": self.description,
            "tool_schema": self.tool_schema,
            "parameters": self.parameters or {},
        }


class Computer:
    """
    Basic class for managing computer operations and actions.
    """

    _data_collection_namespaces: str = "data_collection"
    _action_namespaces: str = "action"

    def __init__(
        self,
        name: str,
        mcp_server_manager: MCPServerManager,
        data_collection_servers_config: Optional[List[Dict[str, Any]]] = None,
        action_servers_config: Optional[List[Dict[str, Any]]] = None,
    ):
        """
        Initialize the computer with a name and optional agent name.
        :param name: The name of the computer.
        :param data_collection_servers_config: Configuration for data collection servers.
        :param action_servers_config: Configuration for action servers.
        """

        self._name = name

        self.data_collection_servers_config = data_collection_servers_config
        self.action_servers_config = action_servers_config

        self._data_collection_servers = {}
        self._action_servers = {}

        self._tools_registry: Dict[str, MCPToolCall] = {}

        self.mcp_server_manager = mcp_server_manager

        # Automatically register meta tools for the computer.

        self._meta_tools: Dict[str, Callable] = {}

        self.logger = logging.getLogger(self.__class__.__name__)

        for attr in dir(self):
            method = getattr(self, attr)
            if callable(method) and hasattr(method, "_meta_tool_name"):
                name = getattr(method, "_meta_tool_name")
                self._meta_tools[name] = method

    async def async_init(self) -> None:
        """
        Asynchronous initialization of the computer.
        """
        self._data_collection_servers = self._init_data_collection_servers()
        self._action_servers = self._init_action_servers()

        await asyncio.gather(
            self.register_mcp_servers(
                self._data_collection_servers,
                tool_type=self._data_collection_namespaces,
            ),
            self.register_mcp_servers(
                self._action_servers, tool_type=self._action_namespaces
            ),
        )

    @staticmethod
    def meta_tool(name: str):
        """
        Decorator to register a function as a meta tool.
        :param name: The name of the meta tool.
        :return: A decorator that registers the function as a meta tool.
        """

        def decorator(func):
            func._meta_tool_name = name  # Store the meta tool name
            return func

        return decorator

    def _init_data_collection_servers(self) -> Dict[str, BaseMCPServer]:
        """
        Initialize data collection servers for the computer of the
        """
        # Get the base directory for UFO2
        for data_collection_server in self.data_collection_servers_config:

            # If the server is set to auto-start, create a FastMCP server
            namespace = data_collection_server.get("namespace")
            reset = data_collection_server.get("reset", False)

            if not namespace:
                namespace = "default_data_collection"

            mcp_server = self.mcp_server_manager.create_or_get_server(
                mcp_config=data_collection_server, reset=reset
            )

            self._data_collection_servers[namespace] = mcp_server

        return self._data_collection_servers

    def _init_action_servers(self) -> Dict[str, BaseMCPServer]:
        """
        Initialize action servers for the computer.
        """
        # Get the base directory for UFO2
        for action_server in self.action_servers_config:
            # If the server is set to auto-start, create a FastMCP server
            namespace = action_server.get("namespace")
            reset = action_server.get("reset", False)

            if not namespace:
                namespace = "default_action"

            mcp_server = self.mcp_server_manager.create_or_get_server(
                mcp_config=action_server, reset=reset
            )

            self._action_servers[namespace] = mcp_server

        return self._action_servers

    async def _run_action(self, tool_call: MCPToolCall) -> CallToolResult:
        """
        Run a one-step action on the computer.
        :param tool_call: The tool call to run.
        :return: The result of the single action.
        """

        tool_key = tool_call.tool_key
        tool_info = self._tools_registry.get(tool_key, None)

        self.logger.info(
            f"Running tool: {tool_info.tool_name} with parameters: {tool_info.parameters}"
        )

        if not tool_info:
            raise ValueError(f"Tool {tool_key} is not registered.")

        # Check if the tool is a meta tool for listing tools
        if tool_info.tool_name in self._meta_tools:
            # Special case for listing tools, which does not require a server call

            parameters = tool_info.parameters or {}
            self.logger.info(
                f"Running meta tool: {tool_info.tool_name} with parameters: {parameters}"
            )

            result = self._meta_tools[tool_info.tool_name](**parameters)

            # If the result is an awaitable, await it
            if inspect.isawaitable(result):
                return await result
            else:
                return result

        server = tool_info.mcp_server.server

        tool_name = tool_info.tool_name
        params = tool_info.parameters or {}

        async with Client(server) as client:
            result: CallToolResult = await client.call_tool(
                name=tool_name, arguments=params
            )
            return result

    async def run_actions(self, tool_calls: List[MCPToolCall]) -> List[CallToolResult]:
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
        self, server_dict: Dict[str, BaseMCPServer], tool_type: str
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
        self, namespace: str, tool_type: str, mcp_server: BaseMCPServer
    ) -> None:
        """
        Register tools from a single MCP server.
        :param namespace: The namespace of the tools.
        :param tool_type: The type of the tools (e.g., "action", "data_collection").
        :param server: The MCP server to register tools from.
        :return: None
        """

        self.logger.info(
            f"Registering tools from [{namespace}] server for ({tool_type})."
        )

        async with Client(mcp_server.server) as client:
            tools = await client.list_tools()
            for tool in tools:
                tool_key = self.make_tool_key(tool_type, tool.name)
                if tool_key not in self._tools_registry:
                    self._register_tool(
                        tool_key=tool_key,
                        tool_name=tool.name,
                        title=tool.title,
                        namespace=namespace,
                        tool_type=tool_type,
                        description=tool.description,
                        tool_schema=(
                            tool.inputSchema
                            if hasattr(tool, "inputSchema") and tool.inputSchema
                            else {}
                        ),
                        mcp_server=mcp_server,
                    )
                else:
                    self.logger.warning(
                        f"Tool {tool_key} is already registered. Skipping registration."
                    )

            for meta_tool_name, meta_tool_func in self._meta_tools.items():
                tool_key = self.make_tool_key(tool_type, meta_tool_name)

                self._register_tool(
                    tool_key=tool_key,
                    tool_name=meta_tool_name,
                    title=meta_tool_func.__name__,
                    namespace=namespace,
                    tool_type=tool_type,
                    description=meta_tool_func.__doc__ or "Meta tool",
                    tool_schema=meta_tool_func.__annotations__,
                    mcp_server=mcp_server,
                )

    def _register_tool(
        self,
        tool_key: str,
        tool_name: str,
        title: str,
        namespace: str,
        tool_type: str,
        description: str,
        tool_schema: Dict[str, Any],
        mcp_server: BaseMCPServer,
    ) -> None:
        """
        Register a tool with the computer in its tools registry.
        :param tool_key: Unique key for the tool, e.g., "tool_type.tool_name".
        :param tool_name: The name of the tool.
        :param title: The title of the tool, used for display.
        :param namespace: The namespace of the tool.
        :param tool_type: The type of the tool (e.g., "action", "
        :param description: The description of the tool.
        :param tool_schema: The tool_schema for the tool.
        :param mcp_server: The MCP server where the tool is registered.
        """
        if tool_key in self._tools_registry:
            raise ValueError(f"Tool {tool_key} is already registered.")

        tool_info = MCPToolCall(
            tool_key=tool_key,
            tool_name=tool_name,
            title=title,
            description=description,
            namespace=namespace,
            tool_type=tool_type,
            tool_schema=tool_schema,
            mcp_server=mcp_server,
        )
        self._tools_registry[tool_key] = tool_info

    async def add_server(
        self,
        namespace: str,
        mcp_server: BaseMCPServer,
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

    @meta_tool("list_tools")
    async def list_tools(
        self,
        tool_type: Optional[str] = None,
        namespace: Optional[str] = None,
        remove_meta: bool = True,
    ) -> CallToolResult:
        """
        Get the available tools of a specific type (action or data_collection).
        :param tool_type: The type of tools to retrieve (e.g., "action", "data_collection").
        :param namespace: Optional namespace to filter tools.
        :param remove_meta: Whether to remove meta tools from the list for listing.
        :return: A list of MCPToolCall objects representing the available tools.
        """

        tools = []

        for tool in self._tools_registry.values():
            if (
                # Check if the tool matches the specified type and namespace
                (tool_type is None or tool.tool_type == tool_type)
                # Check if the tool matches the specified namespace
                and (namespace is None or tool.namespace == namespace)
                # Check if the tool is not a meta tool or if meta tools should be included
                and (not remove_meta or tool.tool_name not in self._meta_tools)
            ):
                tools.append(tool.tool_info)

        content = [
            TextContent(
                type="text",
                text=json.dumps(tools),
                annotations=None,
                meta=None,
            )
        ]

        tool_result = CallToolResult(
            data=tools,
            content=content,
            structured_content=None,
        )

        return tool_result

    def command2tool(self, command: Command) -> MCPToolCall:
        """
        Convert a Command object to an MCPToolCall object.
        :param command: The Command object to convert.
        :return: An MCPToolCall object representing the tool call.
        """
        tool_name = command.tool_name
        tool_type = command.tool_type

        if not tool_type:
            if (
                self.make_tool_key(self._data_collection_namespaces, tool_name)
                in self._tools_registry
            ):
                tool_type = self._data_collection_namespaces
                Warning(
                    f"Tool {tool_name} is registered as a data collection tool, but no tool type was specified in the command. Using {tool_type} as default."
                )

            elif (
                self.make_tool_key(self._action_namespaces, tool_name)
                in self._tools_registry
            ):
                tool_type = self._action_namespaces

                Warning(
                    f"Tool {tool_name} is registered as an action tool, but no tool type was specified in the command. Using {tool_type} as default."
                )
            else:
                raise ValueError(
                    f"Tool {tool_name} is not registered in the computer's tools registry with {self._data_collection_namespaces} or {self._action_namespaces} as tool type."
                )

        tool_key = self.make_tool_key(tool_type, tool_name)
        tool_info = self._tools_registry.get(tool_key, None)

        parameters = copy.deepcopy(command.parameters) if command.parameters else {}

        tool_info.parameters = parameters

        if not tool_info:
            raise ValueError(f"Tool {tool_key} is not registered.")
        return tool_info

    @staticmethod
    def make_tool_key(tool_type: str, tool_name: str) -> str:
        """
        Create a unique key for a tool based on its type and name.
        :param tool_type: The type of the tool (e.g., "action", "data_collection").
        :param tool_name: The name of the tool.
        :return: A unique key for the tool in the format "tool_type::tool_name".
        """
        return f"{tool_type}::{tool_name}"

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


class ComputerManager:
    """Manager for managing multiple Computer instances.
    This class provides methods to get or create Computer instances based on configurations.
    """

    _configs_key = "mcp"

    def __init__(self, configs: Dict[str, Any], mcp_server_manager: MCPServerManager):
        """
        Initialize the ComputerManager with configurations.
        :param configs: Configuration dictionary containing agent_name, process_name, and root_name.
        """
        self.configs = configs
        self.mcp_server_manager = mcp_server_manager
        self.computers = {}

    async def get_or_create(
        self,
        agent_name: str,
        process_name: Optional[str] = None,
        root_name: Optional[str] = None,
    ) -> Computer:
        """
        Get or create a Computer instance based on the provided configuration.
        :param config: Configuration dictionary containing agent_name, process_name, and root_name.
        :return: An instance of Computer.
        """

        key = f"{agent_name}::{process_name}::{root_name or 'default'}"
        if key not in self.computers:
            mcp_config = self.configs.get(self._configs_key, {})
            agent_config = mcp_config.get(agent_name, {})
            if not agent_config:
                raise ValueError(f"Agent configuration for {agent_name} not found.")
            root = root_name or "default"
            agent_instance_config = agent_config.get(root, None)
            if agent_instance_config is None:
                raise ValueError(
                    f"Agent configuration for root_name={root} not found for agent_name={agent_name}."
                )

            data_collection_servers_config = agent_instance_config.get(
                Computer._data_collection_namespaces, []
            )
            action_servers_config = agent_instance_config.get(
                Computer._action_namespaces, []
            )

            computer = Computer(
                name=key,
                data_collection_servers_config=data_collection_servers_config,
                action_servers_config=action_servers_config,
                mcp_server_manager=self.mcp_server_manager,
            )
            await computer.async_init()
            self.computers[key] = computer

        return self.computers[key]

    def reset(self) -> None:
        """
        Reset the ComputerManager by clearing all Computer instances.
        This is useful for reinitializing the manager without restarting the application.
        """
        self.computers.clear()


class CommandRouter:
    """
    Router for executing commands on a Computer instance.
    This class takes a ComputerManager and executes commands on the appropriate Computer instance.
    """

    def __init__(self, computer_manager: ComputerManager):
        """
        Initialize the CommandRouter with a ComputerManager.
        :param manager: An instance of ComputerManager to manage Computer instances.
        """
        self.computer_manager = computer_manager
        self.logger = logging.getLogger(self.__class__.__name__)

    async def execute(
        self,
        agent_name: str,
        process_name: Optional[str],
        root_name: Optional[str],
        commands: List[Command],
        early_exit: bool = True,
    ) -> Dict[str, Result]:
        """
        Execute a command on the appropriate Computer instance based on the provided configuration.
        :param agent_name: The name of the agent to execute the command for.
        :param process_name: The name of the process to control, or None if not specified
        :param root_name: The root name of the computer, or None if not specified.
        :param commands: The list of Command objects to execute.
        :param early_exit: If True, stop executing commands after the first failure.
        :return: The list of results from executing the commands.
        """

        computer = await self.computer_manager.get_or_create(
            agent_name=agent_name, process_name=process_name, root_name=root_name
        )

        results: Dict[str, Result] = {}

        for command in commands:
            call_id = command.call_id

            tool_call = computer.command2tool(command)
            result = await computer.run_actions([tool_call])

            call_tool_result: CallToolResult = result[0]

            if not call_tool_result.is_error:
                results[call_id] = Result(
                    status="success",
                    result=call_tool_result.data,
                    error=None,
                )
            else:
                results[call_id] = Result(
                    status="failure",
                    error=call_tool_result.content[0].text,
                    result=None,
                )

            if early_exit and results[call_id].status == "failure":
                self.logger.warning(
                    f"Early exit due to failure in command {call_id}: {results[call_id].error}"
                )
                break

            # Sleep to avoid overwhelming the server with requests
            time.sleep(0.1)

        return results


def test_command_router():
    """
    Test function for the CommandRouter.
    This function creates a ComputerManager and a CommandRouter, then executes a sample command.
    """
    from ufo.config import Config

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    configs = Config.get_instance().config_data

    mcp_server_manager = MCPServerManager()
    computer_manager = ComputerManager(configs, mcp_server_manager)
    command_router = CommandRouter(computer_manager)

    print("Starting CommandRouter test...")

    # Example command execution, all from the server
    commands = [
        Command(
            tool_name="double_click_mouse",
            tool_type="action",
            parameters={"button": "left"},
        ),
        Command(
            tool_name="list_tools",
            tool_type="action",
            parameters={"namespace": "HardwareExecutor"},
        ),
    ]

    results = asyncio.run(
        command_router.execute(
            agent_name="HardwareAgent",  # From server
            process_name="HardwareAgent",  # From server
            root_name="default",  # From server
            commands=commands,
        )
    )

    for call_id, result in results.items():
        print(f"Command {call_id} executed with status: {result.status}")
        if result.status == "failure":
            print(f"Error: {result.error}")
        else:
            print(f"Result: {result.result}")


if __name__ == "__main__":
    # Example usage for testing the ComputerManager and CommandRouter

    test_command_router()
