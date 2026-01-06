import asyncio
import datetime
import logging
import uuid
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Callable, Coroutine, Any, Dict, List, Optional

from aip.protocol.task_execution import TaskExecutionProtocol
from ufo.client.mcp.mcp_server_manager import MCPServerManager
from ufo.config import get_config
from aip.messages import (
    ClientMessage,
    Command,
    Result,
    ServerMessage,
    ServerMessageType,
    TaskStatus,
    ResultStatus,
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
        self, commands: List[Command], timeout: float = 6000
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
                status=ResultStatus.FAILURE,
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
        # Lazy import to avoid circular dependency
        from ufo.client.computer import CommandRouter, ComputerManager

        self.session = session
        self.pending: Dict[str, asyncio.Future] = {}
        self.logger = logging.getLogger(__name__)

        configs = get_config() or {}

        self.mcp_server_manager = mcp_server_manager
        self.computer_manager = ComputerManager(configs, mcp_server_manager)
        self.command_router = CommandRouter(self.computer_manager)

    async def execute_commands(
        self, commands: List[Command], timeout=6000
    ) -> Optional[List[Result]]:
        """
        Publish commands to the command dispatcher and wait for the result.
        :param commands: The list of commands to publish.
        :param timeout: The timeout for waiting for the result.
        :return: The list of results from the commands, or None if timed out.
        """
        from ufo.module.context import ContextNames

        for command in commands:
            command.call_id = str(uuid.uuid4())

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
    Command dispatcher for communication between components.
    Handles sending commands and receiving results using AIP protocol.
    Uses AIP's TaskExecutionProtocol for structured message handling.
    """

    def __init__(
        self,
        session: "BaseSession",
        protocol: Optional[TaskExecutionProtocol] = None,
    ) -> None:
        """
        Initializes the CommandDispatcher.
        :param session: The session associated with the command dispatcher.
        :param protocol: AIP TaskExecutionProtocol instance.
        """
        self.session = session
        self.pending: Dict[str, asyncio.Future] = {}
        self.send_queue: asyncio.Queue = asyncio.Queue(maxsize=100)
        self.observers: List[asyncio.Task] = []
        self.logger = logging.getLogger(__name__)

        if not protocol:
            raise ValueError("protocol parameter is required")

        self.protocol = protocol

        # Note: No longer need _send_loop observer - AIP transport handles sending

    def register_observer(
        self, observer: Callable[[], Coroutine[Any, Any, None]]
    ) -> None:
        """
        Register an observer task (deprecated - kept for compatibility).
        AIP protocol handles message sending internally.
        """
        # Keep for backward compatibility but no longer needed
        pass

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
        process_name = self.session.context.get(ContextNames.APPLICATION_PROCESS_NAME)
        root_name = self.session.context.get(ContextNames.APPLICATION_ROOT_NAME)
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

    async def execute_commands(
        self, commands: List[Command], timeout: float = 6000
    ) -> Optional[List[Result]]:
        """
        Publish commands to the command dispatcher and wait for the result.
        Uses AIP's TaskExecutionProtocol for message handling.
        :param commands: The list of commands to publish.
        :param timeout: The timeout for waiting for the result.
        :return: The list of results from the commands, or None if timed out.
        """
        server_message = self.make_server_response(commands)
        fut = asyncio.get_event_loop().create_future()
        if server_message.response_id:
            self.pending[server_message.response_id] = fut

        # Use AIP protocol to send commands
        try:
            await self.protocol.send_command(server_message)
            self.logger.info(
                f"[AIP] Sent commands via TaskExecutionProtocol: {server_message.response_id}"
            )
        except Exception as e:
            self.logger.error(f"[AIP] Error sending commands: {e}")
            self.pending.pop(server_message.response_id, None)
            return self.generate_error_results(commands, e)

        try:
            result = await asyncio.wait_for(fut, timeout)
            return result
        except asyncio.TimeoutError as e:
            self.logger.warning(
                f"send_commands timed out for {server_message.response_id}"
            )
            return self.generate_error_results(commands, e)
        finally:
            if server_message.response_id:
                self.pending.pop(server_message.response_id, None)

    async def set_result(self, response_id: str, result: ClientMessage) -> None:
        """
        Called by WebSocket handler when client returns a message.
        :param response_id: The ID of the response.
        :param result: The result from the client.
        """
        fut = self.pending.get(response_id)
        if fut and not fut.done():
            fut.set_result(result.action_results)
