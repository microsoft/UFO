import asyncio
import datetime
import logging
import tracemalloc
from typing import Dict, List, Optional

import aiohttp
from ufo.client.computer import CommandRouter, ComputerManager
from ufo.client.mcp import MCPServerManager
from ufo.cs.contracts import ClientRequest, Command, Result, ServerResponse

tracemalloc.start()


class UFOClient:
    """
    Client for interacting with the UFO web service.
    Sends requests to the service, executes actions, and sends results back.
    """

    def __init__(
        self,
        server_url,
        mcp_server_manager: MCPServerManager,
        computer_manager: ComputerManager,
        client_id: Optional[str] = None,
    ):
        """
        Initialize the UFO web client.
        :param server_url: URL of the UFO web service
        :param mcp_server_manager: Instance of MCPServerManager to manage MCP servers
        :param computer_manager: Instance of ComputerManager to manage Computer instances
        """
        self.server_url = server_url.rstrip("/")
        self.mcp_server_manager = mcp_server_manager
        self.computer_manager = computer_manager
        self.command_router = CommandRouter(
            computer_manager=self.computer_manager,
        )
        self.logger = logging.getLogger(__name__)
        # Initialize task lock for thread safety
        self.task_lock = asyncio.Lock()

        self.client_id = client_id or "client_001"

        # Initialize session variables
        self._agent_name: Optional[str] = None
        self._process_name: Optional[str] = None
        self._root_name: Optional[str] = None

        self._session_id: Optional[str] = None

    async def run(self, request_text: str) -> bool:
        """
        Run a task by communicating with the UFO web service
        :param request_text: The request text to send to the server
        :returns: True if the task was completed successfully, False otherwise
        """
        try:
            # Initial request to start the session
            response = await self.send_request(request_text)

            # Sync with the server response
            self.agent_name = response.agent_name
            self.process_name = response.process_name
            self.root_name = response.root_name

            self.session_id = response.session_id

            # Process the session until it's completed or fails
            while response.status == "continue":
                # Execute the actions and collect results
                action_results = await self.execute_actions(response.actions)

                # Send the results back to the server and get next response
                response = await self.send_request(None, action_results)

            if response.status == "failure":
                self.logger.error(f"Task failed: {response.error}")
                return False

            elif response.status == "completed":
                self.logger.info("Task completed successfully")
                return True

        except aiohttp.ClientError as e:
            self.logger.error(f"Network error: {e}")
            return False
        except ValueError as e:
            self.logger.error(f"Data error: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}", exc_info=True)
            return False

    async def send_request(
        self,
        request_text: Optional[str] = None,
        action_results: Optional[Dict[str, Result]] = None,
    ):
        """
        Send a request to the UFO web service
        :param request_text: The request text to send to the server
        :param action_results: Results of previously executed actions
        :returns: UFOResponse object containing the server's response
        """

        request_data = ClientRequest(
            session_id=self.session_id,
            request=request_text,
            action_results=action_results,
            timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        )

        async with aiohttp.ClientSession() as session:

            async with session.post(
                f"{self.server_url}/api/ufo/task",
                json=request_data.model_dump(),
                headers={"Content-Type": "application/json"},
            ) as response:

                if response.status != 200:
                    text = await response.text()
                    raise Exception(f"Server returned error: {response.status}, {text}")

                response_data = await response.json()
                ufo_response = ServerResponse(**response_data)
                self.logger.info(f"Received response: {response_data}")
                return ufo_response

    async def execute_actions(
        self, commands: Optional[List[Command]]
    ) -> Dict[str, Result]:
        """
        Execute the actions provided by the server
        :param commands: List of actions to execute
        :returns: Results of the executed actions
        """
        action_results = {}

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
