# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Base Protocol Implementation

Provides the core AIP protocol abstractions and message handling infrastructure.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Any, Awaitable, Callable, Dict, List, Optional

from aip.messages import ClientMessage, ServerMessage
from aip.transport import Transport


# Type aliases for clarity
MessageHandler = Callable[[Any], Awaitable[None]]
ProtocolHandler = Callable[[Any], Awaitable[Optional[Any]]]


class AIPProtocol:
    """
    Core AIP protocol implementation.

    This class provides the foundation for all AIP communication:
    - Message serialization and deserialization
    - Middleware pipeline for extensibility
    - Message routing and handler registration
    - Error handling and logging

    The protocol is transport-agnostic and works with any Transport implementation.

    Usage:
        transport = WebSocketTransport()
        protocol = AIPProtocol(transport)
        await protocol.send_message(ClientMessage(...))
        message = await protocol.receive_message()
    """

    def __init__(self, transport: Transport):
        """
        Initialize AIP protocol.

        :param transport: Transport layer for sending/receiving messages
        """
        self.transport = transport
        self.message_handlers: Dict[str, List[MessageHandler]] = {}
        self.middleware_chain: List["ProtocolMiddleware"] = []
        self.logger = logging.getLogger(f"{__name__}.AIPProtocol")

    async def send_message(self, msg: Any) -> None:
        """
        Send a message through the protocol.

        Applies outgoing middleware, serializes the message, and sends via transport.

        :param msg: Message to send (ClientMessage or ServerMessage)
        :raises: ConnectionError if transport not connected
        :raises: IOError if send fails
        """
        try:
            # Apply outgoing middleware
            for middleware in self.middleware_chain:
                msg = await middleware.process_outgoing(msg)

            # Serialize message
            if hasattr(msg, "model_dump_json"):
                # Pydantic model
                serialized = msg.model_dump_json().encode("utf-8")
            elif isinstance(msg, str):
                serialized = msg.encode("utf-8")
            elif isinstance(msg, bytes):
                serialized = msg
            else:
                raise ValueError(f"Unsupported message type: {type(msg)}")

            # Send via transport
            await self.transport.send(serialized)
            self.logger.debug(f"Sent message: {msg.__class__.__name__}")

        except Exception as e:
            self.logger.error(f"Error sending message: {e}")
            raise

    async def receive_message(self, message_type: type = ServerMessage) -> Any:
        """
        Receive a message through the protocol.

        Receives data from transport, deserializes, and applies incoming middleware.

        :param message_type: Expected message type (ClientMessage or ServerMessage)
        :return: Deserialized message
        :raises: ConnectionError if transport not connected
        :raises: IOError if receive fails
        """
        try:
            # Receive via transport
            data = await self.transport.receive()

            # Deserialize message
            if isinstance(data, bytes):
                data = data.decode("utf-8")

            if hasattr(message_type, "model_validate_json"):
                # Pydantic model
                msg = message_type.model_validate_json(data)
            else:
                raise ValueError(f"Unsupported message type: {message_type}")

            # Apply incoming middleware
            for middleware in reversed(self.middleware_chain):
                msg = await middleware.process_incoming(msg)

            self.logger.debug(f"Received message: {msg.__class__.__name__}")
            return msg

        except Exception as e:
            self.logger.error(f"Error receiving message: {e}")
            raise

    def add_middleware(self, middleware: "ProtocolMiddleware") -> None:
        """
        Add middleware to the protocol pipeline.

        Middleware is applied in order for outgoing messages,
        and in reverse order for incoming messages.

        :param middleware: Middleware to add
        """
        self.middleware_chain.append(middleware)
        self.logger.info(f"Added middleware: {middleware.__class__.__name__}")

    def register_handler(self, message_type: str, handler: MessageHandler) -> None:
        """
        Register a handler for a specific message type.

        :param message_type: Message type string (e.g., "task", "heartbeat")
        :param handler: Async function to handle the message
        """
        if message_type not in self.message_handlers:
            self.message_handlers[message_type] = []
        self.message_handlers[message_type].append(handler)
        self.logger.debug(f"Registered handler for: {message_type}")

    async def dispatch_message(self, msg: Any) -> None:
        """
        Dispatch a message to registered handlers.

        :param msg: Message to dispatch
        """
        msg_type = getattr(msg, "type", None)
        if msg_type and msg_type in self.message_handlers:
            for handler in self.message_handlers[msg_type]:
                try:
                    await handler(msg)
                except Exception as e:
                    self.logger.error(
                        f"Error in handler for {msg_type}: {e}", exc_info=True
                    )
        else:
            self.logger.warning(f"No handler for message type: {msg_type}")

    def is_connected(self) -> bool:
        """Check if protocol transport is connected."""
        return self.transport.is_connected

    async def send_error(
        self, error_msg: str, response_id: Optional[str] = None
    ) -> None:
        """
        Send a generic error message (server-side).

        :param error_msg: Error message
        :param response_id: Optional response ID for correlation
        """
        import datetime
        import uuid
        from aip.messages import ServerMessage, ServerMessageType, TaskStatus

        error_message = ServerMessage(
            type=ServerMessageType.ERROR,
            status=TaskStatus.ERROR,
            error=error_msg,
            timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),
            response_id=response_id or str(uuid.uuid4()),
        )
        await self.send_message(error_message)

    async def send_ack(
        self, session_id: Optional[str] = None, response_id: Optional[str] = None
    ) -> None:
        """
        Send a generic acknowledgment message (server-side).

        :param session_id: Optional session ID
        :param response_id: Optional response ID for correlation
        """
        import datetime
        import uuid
        from aip.messages import ServerMessage, ServerMessageType, TaskStatus

        ack_message = ServerMessage(
            type=ServerMessageType.HEARTBEAT,
            status=TaskStatus.OK,
            session_id=session_id,
            timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),
            response_id=response_id or str(uuid.uuid4()),
        )
        await self.send_message(ack_message)

    async def close(self) -> None:
        """Close protocol and transport."""
        await self.transport.close()


class ProtocolMiddleware(ABC):
    """
    Abstract base class for protocol middleware.

    Middleware can intercept and modify messages in both directions,
    enabling cross-cutting concerns like logging, metrics, and encryption.
    """

    @abstractmethod
    async def process_outgoing(self, msg: Any) -> Any:
        """
        Process outgoing message.

        :param msg: Outgoing message
        :return: Modified message
        """
        pass

    @abstractmethod
    async def process_incoming(self, msg: Any) -> Any:
        """
        Process incoming message.

        :param msg: Incoming message
        :return: Modified message
        """
        pass


class LoggingMiddleware(ProtocolMiddleware):
    """
    Middleware that logs all messages.

    Useful for debugging and monitoring protocol communication.
    """

    def __init__(self, log_level: int = logging.DEBUG):
        """
        Initialize logging middleware.

        :param log_level: Log level for messages
        """
        self.logger = logging.getLogger(f"{__name__}.LoggingMiddleware")
        self.log_level = log_level

    async def process_outgoing(self, msg: Any) -> Any:
        """Log outgoing message."""
        self.logger.log(self.log_level, f"[OUT] {msg}")
        return msg

    async def process_incoming(self, msg: Any) -> Any:
        """Log incoming message."""
        self.logger.log(self.log_level, f"[IN] {msg}")
        return msg
