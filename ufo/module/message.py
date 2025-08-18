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
    def __init__(self, session: "BaseSession", ws: Optional[WebSocket] = None):
        """
        Initialize the message bus.
        :param ws: The WebSocket connection.
        :param session: The session information.
        """
        self.ws = ws
        self.session = session
        self.pending: Dict[str, asyncio.Future] = {}
        self.send_queue: asyncio.Queue = asyncio.Queue()
        self.logger = logging.getLogger(self.__class__.__name__)

        if ws is not None:
            self._send_task = asyncio.create_task(self._send_loop())

    def make_server_response(self, commands: List[Command]) -> ServerMessage:
        """
        Create a server response from the given commands.
        :param commands: The list of commands to include in the response.
        :return: The complete server response.
        """
        from ufo.module.context import ContextNames

        for command in commands:
            command.call_id = str(uuid.uuid4())

        agent_name = self.session.current_round.agent.__class__.__name__
        process_name = self.session.context.get(ContextNames.APPLICATION_ROOT_NAME)
        root_name = self.session.context.get(ContextNames.APPLICATION_PROCESS_NAME)
        actions = commands
        session_id = self.session.id
        response_id = str(uuid.uuid4())
        timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()

        return ServerMessage(
            type="commands",
            status="continue",
            agent_name=agent_name,
            process_name=process_name,
            root_name=root_name,
            actions=actions,
            session_id=session_id,
            timestamp=timestamp,
            response_id=response_id,
        )

    async def send_commands(
        self, commands: List[Command], timeout: float = 10.0
    ) -> Dict[str, Result]:
        """
        Send commands from the server to the client.
        :param commands: The list of commands to send.
        :param timeout: The timeout for the operation.
        """

        fut = asyncio.get_event_loop().create_future()

        server_response = self.make_server_response(commands)

        response_id = server_response.response_id

        self.pending[response_id] = fut

        self.logger.info(f"Sending response_id: {response_id}")

        await self.send_queue.put(server_response.model_dump_json())

        try:
            result = await asyncio.wait_for(fut, timeout)
            return result
        except asyncio.TimeoutError:
            self.logger.warning(f"Waiting for {server_response} timed out")
            raise TimeoutError(f"Waiting for {server_response} timed out")
        finally:
            self.pending.pop(response_id, None)

    async def _send_loop(self):
        """
        Background loop for sending messages to the client.
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
        Handle a message from the client.
        :param response_id: The response ID from the server.
        :param result: The result to set.
        """

        fut = self.pending.get(response_id)

        if fut and not fut.done():
            fut.set_result(result.action_results)
