import argparse
import asyncio
import json
import logging
import sys
import datetime
from typing import Dict, List, Optional

import aiohttp
import websockets
from ufo.client.computer import CommandRouter, ComputerManager
from ufo.client.mcp import MCPServerManager
from ufo.config import Config
from ufo.cs.contracts import ClientRequest, Command, Result, ServerResponse
from ufo.client.websocket import UFOWebSocketClient

CONFIGS = Config.get_instance().config_data


# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


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
            response = self.send_request(request_text)

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
                response = self.send_request(None, action_results)

            if response.status == "failure":
                logger.error(f"Task failed: {response.error}")
                return False

            elif response.status == "completed":
                logger.info("Task completed successfully")
                return True

        except aiohttp.ClientError as e:
            logger.error(f"Network error: {e}")
            return False
        except ValueError as e:
            logger.error(f"Data error: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error: {e}", exc_info=True)
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
            timestamp=datetime.datetime.utcnow().isoformat(),
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
                logger.info(f"Received response: {response_data}")
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
            logger.info(f"Executing {len(commands)} actions in total")
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
        logger.info(f"Session ID set to: {self._session_id}")

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
        logger.info(f"Agent name set to: {self._agent_name}")

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
        logger.info(f"Process name set to: {self._process_name}")

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
        logger.info(f"Root name set to: {self._root_name}")

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

        logger.info("Client state has been reset.")


async def websocket_client_main(
    server_addr: str, ufo_client: "UFOClient", max_retries: int = 3
):
    """
    Main entry point for the WebSocket client
    """
    retry_count = 0
    while retry_count < max_retries:
        try:
            logger.info(
                f"Connecting to {server_addr} (attempt {retry_count + 1}/{max_retries})"
            )
            async with websockets.connect(server_addr) as ws:
                client_id = ufo_client.client_id
                await ws.send(json.dumps({"client_id": client_id}))
                logger.info(
                    f"[WebSocket] Registered as {client_id}, waiting for task..."
                )
                retry_count = 0  # Reset retry count on successful connection

                async for msg in ws:
                    try:
                        task = json.loads(msg)
                        if task.get("type") == "task":
                            task_id = task["task_id"]
                            request_text = task["request"]
                            logger.info(
                                f"[WebSocket] Got task {task_id}: {request_text}"
                            )

                            async with ufo_client.task_lock:

                                ufo_client.reset()
                                success = await ufo_client.run(request_text)
                                result = {"success": success}
                                await ws.send(
                                    json.dumps(
                                        {
                                            "type": "result",
                                            "task_id": task_id,
                                            "result": result,
                                        }
                                    )
                                )
                                logger.info(f"[WebSocket] Sent result for {task_id}")
                    except Exception as task_exc:
                        logger.error(
                            f"Error handling task message: {task_exc}", exc_info=True
                        )
        except (websockets.ConnectionClosedError, websockets.ConnectionClosedOK) as e:
            logger.error(f"WebSocket connection closed: {e}")
            retry_count += 1
            if retry_count < max_retries:
                logger.info(
                    f"Retrying WebSocket connection ({retry_count}/{max_retries}) after {2 ** retry_count}s..."
                )
                await asyncio.sleep(2**retry_count)

        except Exception as e:
            logger.error(f"Unexpected WebSocket client error: {e}", exc_info=True)
            retry_count += 1
            if retry_count < max_retries:
                logger.info(
                    f"Retrying WebSocket connection ({retry_count}/{max_retries}) after {2 ** retry_count}s..."
                )
                await asyncio.sleep(2**retry_count)
    logger.error("Max retries reached. Exiting websocket client.")


async def main():
    """Main entry point for the UFO web client"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="UFO Web Client")
    parser.add_argument(
        "--server",
        dest="server_url",
        default="http://localhost:5000",
        help="UFO Web Service URL (default: http://localhost:5000)",
    )
    parser.add_argument(
        "--client-id",
        dest="client_id",
        default="client_001",
        help="Client ID for the UFO Web Client (default: client_001)",
    )
    parser.add_argument(
        "--ws-server",
        dest="ws_server_url",
        default="ws://localhost:8765",
        help="WebSocket server address (default: ws://localhost:8765)",
    )
    parser.add_argument("--ws", action="store_true", help="Run in WebSocket mode")
    parser.add_argument(
        "--max-retries",
        type=int,
        default=3,
        dest="max_retries",
        help="Maximum retries for failed requests (default: 3)",
    )
    parser.add_argument(
        "--request",
        dest="request_text",
        default='open notepad and write "Hello, World!"',
        help="The task request text",
    )
    args = parser.parse_args()

    # Initialize the MCP server manager and computer manager
    mcp_server_manager = MCPServerManager()
    computer_manager = ComputerManager(CONFIGS, mcp_server_manager)

    # Create and run the client
    client = UFOClient(
        args.server_url,
        mcp_server_manager=mcp_server_manager,
        computer_manager=computer_manager,
        client_id=args.client_id,
    )

    if args.ws:
        # Run in WebSocket mode
        try:
            ws_client = UFOWebSocketClient(args.ws_server_url, client, max_retries=3)
            await ws_client.connect_and_listen()
        except Exception as e:
            logger.error(f"WebSocket client error: {str(e)}", exc_info=True)
            sys.exit(1)
    else:
        if not args.request_text:
            logger.error("No request text provided. Use --request to specify a task.")
            sys.exit(1)

        success = client.run(args.request_text)

        # Exit with appropriate status code
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
