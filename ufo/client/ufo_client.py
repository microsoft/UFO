import asyncio
import logging
import tracemalloc
from typing import List, Optional


from ufo.client.computer import CommandRouter, ComputerManager
from ufo.client.mcp.mcp_server_manager import MCPServerManager
from aip.messages import Command, Result, ServerMessage

tracemalloc.start()


class UFOClient:
    """
    Client for interacting with the UFO web service.
    Sends requests to the service, executes actions, and sends results back.
    """

    def __init__(
        self,
        mcp_server_manager: MCPServerManager,
        computer_manager: ComputerManager,
        client_id: Optional[str] = None,
        platform: Optional[str] = None,
    ):
        """
        Initialize the UFO web client.
        :param mcp_server_manager: Instance of MCPServerManager to manage MCP servers
        :param computer_manager: Instance of ComputerManager to manage Computer instances
        :param client_id: Optional client ID for the UFO client
        :param platform: Platform type ('windows', 'linux', or 'mobile'). Auto-detected if not specified.
        """
        self.mcp_server_manager = mcp_server_manager
        self.computer_manager = computer_manager
        self.command_router = CommandRouter(
            computer_manager=self.computer_manager,
        )
        self.logger = logging.getLogger(__name__)
        # Initialize task lock for thread safety
        self.task_lock = asyncio.Lock()

        self.client_id = client_id or "client_001"
        self.platform = platform

        # Initialize session variables
        self._agent_name: Optional[str] = None
        self._process_name: Optional[str] = None
        self._root_name: Optional[str] = None

        self._session_id: Optional[str] = None

    async def execute_step(self, response: ServerMessage) -> List[Result]:
        """
        Perform a single step execution.
        :param response: The ServerMessage instance to process.
        :return: A list of Result instances.
        """

        self.agent_name = response.agent_name
        self.process_name = response.process_name
        self.root_name = response.root_name

        # Execute the actions and collect results
        action_results = await self.execute_actions(response.actions)

        return action_results

    async def execute_actions(self, commands: Optional[List[Command]]) -> List[Result]:
        """
        Execute the actions provided by the server
        :param commands: List of actions to execute
        :returns: Results of the executed actions
        """
        action_results = []

        if commands:
            self.logger.info(f"Executing {len(commands)} actions in total")
            # Process each action

            action_results = await self.command_router.execute(
                agent_name=self.agent_name,
                process_name=self.process_name,
                root_name=self.root_name,
                commands=commands,
            )

        return action_results

    @property
    def session_id(self) -> Optional[str]:
        """
        Get the current session ID.
        :return: The current session ID or None if not set.
        """
        return self._session_id

    @session_id.setter
    def session_id(self, value: Optional[str]):
        """
        Set the current session ID.
        :param value: The session ID to set.
        """
        if value is not None and not isinstance(value, str):
            raise ValueError("Session ID must be a string or None.")
        self._session_id = value
        self.logger.info(f"Session ID set to: {self._session_id}")

    @property
    def agent_name(self) -> Optional[str]:
        """
        Get the agent name.
        :return: The agent name or None if not set.
        """
        return self._agent_name

    @agent_name.setter
    def agent_name(self, value: Optional[str]):
        """
        Set the agent name.
        :param value: The agent name to set.
        """
        if value is not None and not isinstance(value, str):
            raise ValueError("Agent name must be a string or None.")
        self._agent_name = value
        self.logger.info(f"Agent name set to: {self._agent_name}")

    @property
    def process_name(self) -> Optional[str]:
        """
        Get the process name.
        :return: The process name or None if not set.
        """
        return self._process_name

    @process_name.setter
    def process_name(self, value: Optional[str]):
        """
        Set the process name.
        :param value: The process name to set.
        """
        if value is not None and not isinstance(value, str):
            raise ValueError("Process name must be a string or None.")
        self._process_name = value
        self.logger.info(f"Process name set to: {self._process_name}")

    @property
    def root_name(self) -> Optional[str]:
        """
        Get the root name.
        :return: The root name or None if not set.
        """
        return self._root_name

    @root_name.setter
    def root_name(self, value: Optional[str]):
        """
        Set the root name.
        :param value: The root name to set.
        """
        if value is not None and not isinstance(value, str):
            raise ValueError("Root name must be a string or None.")
        self._root_name = value
        self.logger.info(f"Root name set to: {self._root_name}")

    def reset(self):
        """
        Reset session state and dependent managers.
        """
        self._session_id = None
        self._agent_name = None
        self._process_name = None
        self._root_name = None

        self.computer_manager.reset()
        self.mcp_server_manager.reset()

        self.logger.info("Client state has been reset.")
