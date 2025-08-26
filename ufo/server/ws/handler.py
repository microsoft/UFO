import asyncio
import datetime
import logging
import uuid

from fastapi import WebSocket, WebSocketDisconnect

from ufo.contracts.contracts import (
    ClientMessage,
    ClientMessageType,
    ServerMessage,
    ServerMessageType,
    TaskStatus,
)
from ufo.module.dispatcher import WebSocketCommandDispatcher
from ufo.server.services.session_manager import SessionManager
from ufo.server.services.ws_manager import WSManager


class UFOWebSocketHandler:
    """
    Handles WebSocket connections for the UFO server.
    """

    def __init__(
        self,
        ws_manager: WSManager,
        session_manager: SessionManager,
    ):
        self.ws_manager = ws_manager
        self.session_manager = session_manager
        self.logger = logging.getLogger(self.__class__.__name__)

    async def connect(self, websocket: WebSocket) -> str:
        """
        Connects a client and registers it in the WS manager.
        Expects the first message to contain {"client_id": ...}.
        :param websocket: The WebSocket connection.
        :return: The client ID.
        """
        await websocket.accept()
        reg_msg = await websocket.receive_text()
        reg_info = ClientMessage.model_validate_json(reg_msg)

        if not reg_info.client_id:
            raise ValueError("Client ID is required for WebSocket registration")
        if reg_info.type != ClientMessageType.REGISTER:
            raise ValueError("First message must be a registration message")

        client_id = reg_info.client_id
        self.ws_manager.add_client(client_id, websocket)
        self.logger.info(f"[WS] {client_id} connected")
        return client_id

    async def disconnect(self, client_id: str) -> None:
        """
        Disconnects a client and removes it from the WS manager.
        :param client_id: The ID of the client.
        """

        self.ws_manager.remove_client(client_id)
        self.logger.info(f"[WS] {client_id} disconnected")

    async def handler(self, websocket: WebSocket) -> None:
        """
        FastAPI WebSocket entry point.
        :param websocket: The WebSocket connection.
        """
        client_id = None
        try:
            client_id = await self.connect(websocket)
            while True:
                msg = await websocket.receive_text()
                asyncio.create_task(self.handle_message(msg, websocket))
        except WebSocketDisconnect:
            self.logger.info(f"[WS] {client_id} disconnected normally")
            if client_id:
                await self.disconnect(client_id)
        except Exception as e:
            self.logger.error(f"[WS] Error with client {client_id}: {e}")
            if client_id:
                await self.disconnect(client_id)

    async def handle_message(self, msg: str, websocket: WebSocket) -> None:
        """
        Dispatch incoming WS messages to specific handlers.
        :param msg: The message received from the client.
        :param websocket: The WebSocket connection.
        """
        import traceback

        try:
            data = ClientMessage.model_validate_json(msg)

            client_id = data.client_id

            self.logger.info(
                f"[WS] Received message from {client_id}, type: {data.type}"
            )
            msg_type = data.type

            if msg_type == ClientMessageType.TASK:
                await self.handle_task_request(data, websocket)
            elif msg_type == ClientMessageType.COMMAND_RESULTS:
                await self.handle_command_result(data)
            elif msg_type == ClientMessageType.HEARTBEAT:
                await self.handle_heartbeat(data, websocket)
            elif msg_type == ClientMessageType.ERROR:
                await self.handle_error(data, websocket)
            else:
                await self.handle_unknown(data, websocket)
        except Exception as e:
            traceback.print_exc()
            self.logger.error(f"[WS] Error handling message from {client_id}: {e}")

            server_message = ServerMessage(
                status=TaskStatus.ERROR,
                type=ServerMessageType.ERROR,
                error=str(e),
                timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                response_id=str(uuid.uuid4()),
            )
            await websocket.send_text(server_message.model_dump_json())

    async def handle_heartbeat(self, data: ClientMessage, websocket: WebSocket) -> None:
        """
        Handle heartbeat messages from the client.
        :param data: The data from the client.
        :param websocket: The WebSocket connection.
        """
        self.logger.info(f"[WS] Heartbeat from {data.client_id}")
        server_message = ServerMessage(
            type=ServerMessageType.HEARTBEAT,
            status=TaskStatus.OK,
            timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),
            response_id=str(uuid.uuid4()),
        )
        await websocket.send_text(server_message.model_dump_json())

    async def handle_error(self, data: ClientMessage, websocket: WebSocket) -> None:
        """
        Handle error messages from the client.
        :param data: The data from the client.
        :param websocket: The WebSocket connection.
        """
        self.logger.error(f"[WS] Error from {data.client_id}: {data.error}")
        server_message = ServerMessage(
            type=ServerMessageType.ERROR,
            error=data.error,
            timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),
            response_id=str(uuid.uuid4()),
        )
        await websocket.send_text(server_message.model_dump_json())

    async def handle_unknown(self, data: ClientMessage, websocket: WebSocket) -> None:
        """
        Handle unknown message types.
        :param data: The data from the client.
        :param websocket: The WebSocket connection.
        """
        self.logger.warning(f"[WS] Unknown message type: {data.type}")

        server_message = ServerMessage(
            type=ServerMessageType.ERROR,
            error=f"Unknown message type: {data.type}",
            timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),
            response_id=str(uuid.uuid4()),
        )

        await websocket.send_text(server_message.model_dump_json())

    async def handle_task_request(
        self, data: ClientMessage, websocket: WebSocket
    ) -> None:
        """
        Handle a task request message from the client.
        :param data: The data from the client.
        :param websocket: The WebSocket connection.
        """
        self.logger.info(
            f"[WS] Handling task request: {data.request} from {data.client_id}"
        )

        session_id = str(uuid.uuid4()) if not data.session_id else data.session_id
        task_name = data.task_name if data.task_name else str(uuid.uuid4())

        session = self.session_manager.get_or_create_session(
            session_id, task_name, data.request, websocket
        )

        error = None

        try:
            await session.run()
            if session.is_error():
                status = TaskStatus.FAILED
                session.results = {"failure": "session ended with an error"}
            elif session.is_finished():
                status = TaskStatus.COMPLETED

            self.logger.info(f"[WS] Task {session_id} is ending with status: {status}")

        except Exception as e:
            import traceback

            traceback.print_exc()
            self.logger.error(f"[WS] Error running session {session_id}: {e}")
            status = TaskStatus.FAILED
            error = str(e)
        finally:
            server_message = ServerMessage(
                type=ServerMessageType.TASK_END,
                status=status,
                timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                session_id=session_id,
                error=error,
                response_id=str(uuid.uuid4()),
            )
            await websocket.send_text(server_message.model_dump_json())

            # Save results to session manager
            self.session_manager.set_results(session_id)

    async def handle_command_result(self, data: ClientMessage) -> None:
        """
        Handle the result of commands. Run in background.
        :param data: The data from the client.
        """

        self.logger.debug(f"[WS] Handling command result: {data.action_results}")

        response_id = data.prev_response_id
        session_id = data.session_id
        session = self.session_manager.get_or_create_session(session_id)

        command_dispatcher: WebSocketCommandDispatcher = (
            session.context.command_dispatcher
        )

        await command_dispatcher.set_result(response_id, data)
