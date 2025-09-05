import asyncio
import datetime
import logging
import uuid
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Awaitable, Callable, Dict, List, Optional

from fastapi import WebSocket

from ufo.client.computer import CommandRouter, ComputerManager
from ufo.client.mcp.mcp_server_manager import MCPServerManager
from ufo.config import get_config
from ufo.contracts.contracts import (
    ClientMessage,
    Command,
    Result,
    ServerMessage,
    ServerMessageType,
    TaskStatus,
)

if TYPE_CHECKING:
    from ufo.module.basic import BaseSession


class BasicCommandDispatcher(ABC):
    """
    Abstract base class for command dispatcher handling.
    Provides methods to send commands and receive results.
    """

    @abstractmethod
    async def execute_commands(
        self, commands: List[Command], timeout: float = 10.0
    ) -> Optional[List[Result]]:
        """
        Publish commands to the command dispatcher and wait for the result.
        :param commands: The list of commands to publish.
        :param timeout: The timeout for waiting for the result.
        :return: The list of results from the commands, or None if timed out.
        """
        pass

    def generate_error_results(
        self, commands: List[Command], error: Exception
    ) -> Optional[List[Result]]:
        """
        Handle errors that occur during command execution.
        :param commands: The list of commands that were being executed.
        :param error: The error that occurred.
        :return: An error result indicating the failure.
        """

        result_list = []
        for command in commands:
            error_msg = f"Error occurred while executing command {command}: {error}, please retry or execute a different command."
            result = Result(
                status="failure",
                error=error_msg,
                result=error_msg,
                call_id=command.call_id,
            )
            result_list.append(result)

        return result_list


class LocalCommandDispatcher(BasicCommandDispatcher):
    """
    command dispatcher for local communication between components.
    """

    def __init__(
        self, session: "BaseSession", mcp_server_manager: MCPServerManager
    ) -> None:
        """
        Initializes the LocalCommandDispatcher.
        :param session: The session associated with the command dispatcher.
        :param mcp_server_manager: The MCP server manager.
        """
        self.session = session
        self.pending: Dict[str, asyncio.Future] = {}
        self.logger = logging.getLogger(__name__)

        configs = get_config()

        self.mcp_server_manager = mcp_server_manager
        self.computer_manager = ComputerManager(configs, mcp_server_manager)
        self.command_router = CommandRouter(self.computer_manager)

    async def execute_commands(
        self, commands: List[Command], timeout=60
    ) -> Optional[List[Result]]:
        """
        Publish commands to the command dispatcher and wait for the result.
        :param commands: The list of commands to publish.
        :param timeout: The timeout for waiting for the result.
        :return: The list of results from the commands, or None if timed out.
        """
        from ufo.module.context import ContextNames

        try:
            action_results = await asyncio.wait_for(
                self.command_router.execute(
                    agent_name=self.session.current_agent_class,
                    root_name=self.session.context.get(
                        ContextNames.APPLICATION_ROOT_NAME
                    ),
                    process_name=self.session.context.get(
                        ContextNames.APPLICATION_PROCESS_NAME
                    ),
                    commands=commands,
                ),
                timeout=timeout,
            )
        except asyncio.TimeoutError as e:
            self.logger.warning(f"Command execution timed out for commands: {commands}")
            return self.generate_error_results(commands, e)

        except Exception as e:
            self.logger.warning(
                f"Error occurred while executing commands {commands}: {e}"
            )
            return self.generate_error_results(commands, e)

        return action_results


class WebSocketCommandDispatcher(BasicCommandDispatcher):
    """
    command dispatcher for communication between components.
    Handles sending commands and receiving results via WebSocket using observers.
    """

    def __init__(self, session: "BaseSession", ws: Optional[WebSocket] = None) -> None:
        """
        Initializes the CommandDispatcher.
        :param session: The session associated with the command dispatcher.
        :param ws: The WebSocket connection (optional).
        """
        self.ws = ws
        self.session = session
        self.pending: Dict[str, asyncio.Future] = {}
        self.send_queue: asyncio.Queue = asyncio.Queue(maxsize=100)
        self.observers: List[asyncio.Task] = []
        self.logger = logging.getLogger(__name__)

        if ws:
            self.register_observer(self._send_loop)

    def register_observer(self, observer: Callable[[], Awaitable[None]]) -> None:
        """
        Register an observer (_send_loop task) to watch the send_queue.
        """
        task = asyncio.create_task(observer())
        self.observers.append(task)

    def make_server_response(self, commands: List[Command]) -> ServerMessage:
        """
        Create a server response message for the given commands.
        :param commands: The list of commands to include in the response.
        :return: A ServerMessage containing the response.
        """

        for command in commands:
            command.call_id = str(uuid.uuid4())

        from ufo.module.context import ContextNames

        agent_name = self.session.current_agent_class
        process_name = self.session.context.get(ContextNames.APPLICATION_ROOT_NAME)
        root_name = self.session.context.get(ContextNames.APPLICATION_PROCESS_NAME)
        session_id = self.session.id
        response_id = str(uuid.uuid4())
        timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()

        return ServerMessage(
            type=ServerMessageType.COMMAND,
            status=TaskStatus.CONTINUE,
            agent_name=agent_name,
            process_name=process_name,
            root_name=root_name,
            actions=commands,
            session_id=session_id,
            task_name=self.session.task,
            timestamp=timestamp,
            response_id=response_id,
        )

    async def notify_observers(self, message: str) -> None:
        """
        Notify observers that a new message is ready to send.
        :param message: The message to send.
        """
        await self.send_queue.put(message)

    async def execute_commands(
        self, commands: List[Command], timeout: float = 60
    ) -> Optional[List[Result]]:
        """
        Publish commands to the command dispatcher and wait for the result.
        :param commands: The list of commands to publish.
        :param timeout: The timeout for waiting for the result.
        :return: The list of results from the commands, or None if timed out.
        """
        server_message = self.make_server_response(commands)
        fut = asyncio.get_event_loop().create_future()
        self.pending[server_message.response_id] = fut

        # Push to send_queue to notify observer (_send_loop)
        await self.notify_observers(server_message.model_dump_json())

        try:
            result = await asyncio.wait_for(fut, timeout)
            return result
        except asyncio.TimeoutError as e:
            self.logger.warning(
                f"send_commands timed out for {server_message.response_id}"
            )
            return self.generate_error_results(commands, e)
        finally:
            self.pending.pop(server_message.response_id, None)

    async def _send_loop(self) -> None:
        """
        Observer task: constantly watch send_queue and send messages via websocket.
        """
        while True:
            message = await self.send_queue.get()
            try:
                await self.ws.send_text(message)
                self.logger.info(f"Sent message: {message}")
            except Exception as e:
                self.logger.error(f"Error sending message: {e}")

    async def set_result(self, response_id: str, result: ClientMessage) -> None:
        """
        Called by WebSocket handler when client returns a message.
        :param response_id: The ID of the response.
        :param result: The result from the client.
        """
        fut = self.pending.get(response_id)
        if fut and not fut.done():
            fut.set_result(result.action_results)
