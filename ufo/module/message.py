import asyncio
import datetime
import logging
import uuid
from typing import TYPE_CHECKING, Dict, List, Optional

from fastapi import WebSocket

from ufo.contracts.contracts import ClientMessage, Command, Result, ServerMessage

if TYPE_CHECKING:
    from ufo.module.basic import BaseSession


class MessageBus:
    """
    Message bus for communication between components.
    Handles sending commands and receiving results via WebSocket using observers.
    """

    def __init__(self, session: "BaseSession", ws: Optional[WebSocket] = None) -> None:
        """
        Initializes the MessageBus.
        :param session: The session associated with the message bus.
        :param ws: The WebSocket connection (optional).
        """
        self.ws = ws
        self.session = session
        self.pending: Dict[str, asyncio.Future] = {}
        self.send_queue: asyncio.Queue = asyncio.Queue()
        self.observers: List[asyncio.Task] = []
        self.logger = logging.getLogger(__name__)

        if ws:
            self.register_observer(self._send_loop)

    def register_observer(self, observer: asyncio.coroutine) -> None:
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

        from ufo.module.context import ContextNames

        for command in commands:
            command.call_id = str(uuid.uuid4())

        agent_name = self.session.current_agent_class
        process_name = self.session.context.get(ContextNames.APPLICATION_ROOT_NAME)
        root_name = self.session.context.get(ContextNames.APPLICATION_PROCESS_NAME)
        session_id = self.session.id
        response_id = str(uuid.uuid4())
        timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()

        return ServerMessage(
            type="commands",
            status="continue",
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

    async def publish_commands(
        self, commands: List[Command], timeout: float = 10.0
    ) -> Optional[List[Result]]:
        """
        Publish commands to the message bus and wait for the result.
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
        except asyncio.TimeoutError:
            self.logger.warning(
                f"send_commands timed out for {server_message.response_id}"
            )
            raise TimeoutError(f"Waiting for {server_message.response_id} timed out")
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
