# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Base Protocol Implementation

Provides the core AIP protocol abstractions and message handling infrastructure.
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Awaitable, Callable, Dict, List, Optional

from aip.messages import ServerMessage
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

        except (ConnectionError, IOError, OSError) as e:
            # Connection closed or I/O error - this is common during disconnection
            # Log at DEBUG level to avoid alarming ERROR logs during normal shutdown
            error_msg = str(e).lower()
            if "closed" in error_msg or "not connected" in error_msg:
                self.logger.debug(f"Cannot send message (connection closed): {e}")
            else:
                self.logger.warning(f"Connection error sending message: {e}")
            raise
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

        except (ConnectionError, IOError, OSError) as e:
            # Connection closed or I/O error - this is common during disconnection
            error_msg = str(e).lower()
            if "closed" in error_msg or "not connected" in error_msg:
                self.logger.debug(f"Cannot receive message (connection closed): {e}")
            else:
                self.logger.warning(f"Connection error receiving message: {e}")
            raise
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

    # ========================================================================
    # Binary Message Handling (New Feature)
    # ========================================================================

    async def send_binary_message(
        self, data: bytes, metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Send a binary message with optional metadata.

        Uses a two-frame approach for structured binary transfers:
        1. Text frame with JSON metadata (filename, size, mime_type, checksum, etc.)
        2. Binary frame with actual file data

        This approach allows receivers to prepare for incoming binary data
        and validate it after reception.

        :param data: Binary data to send (image, file, etc.)
        :param metadata: Optional metadata dict with fields like:
                        - filename: str
                        - mime_type: str (e.g., "image/png", "application/pdf")
                        - size: int (will be auto-filled)
                        - checksum: str (optional, for validation)
                        - session_id: str (optional)
                        - custom fields as needed

        :raises: ConnectionError if transport not connected
        :raises: IOError if send fails

        Example:
            # Send an image with metadata
            with open("screenshot.png", "rb") as f:
                image_data = f.read()

            await protocol.send_binary_message(
                data=image_data,
                metadata={
                    "filename": "screenshot.png",
                    "mime_type": "image/png",
                    "description": "Desktop screenshot"
                }
            )
        """
        import datetime
        import json

        try:
            # 1. Prepare and send metadata as text frame
            meta = metadata or {}
            meta.update(
                {
                    "type": "binary_data",
                    "size": len(data),
                    "timestamp": datetime.datetime.now(
                        datetime.timezone.utc
                    ).isoformat(),
                }
            )

            meta_json = json.dumps(meta)
            await self.transport.send(meta_json.encode("utf-8"))
            self.logger.debug(f"Sent binary metadata: {meta}")

            # 2. Send actual data as binary frame
            await self.transport.send_binary(data)
            self.logger.debug(f"Sent {len(data)} bytes of binary data")

        except Exception as e:
            self.logger.error(f"Error sending binary message: {e}")
            raise

    async def receive_binary_message(
        self, validate_size: bool = True
    ) -> tuple[bytes, Dict[str, Any]]:
        """
        Receive a binary message with metadata.

        Expects a two-frame sequence:
        1. Text frame with JSON metadata
        2. Binary frame with actual data

        :param validate_size: If True, validates received size matches metadata
        :return: Tuple of (binary_data, metadata_dict)
        :raises: ConnectionError if connection closed
        :raises: IOError if receive fails
        :raises: ValueError if size validation fails

        Example:
            # Receive a binary file
            data, metadata = await protocol.receive_binary_message()

            filename = metadata.get("filename", "received_file.bin")
            with open(filename, "wb") as f:
                f.write(data)

            print(f"Received: {filename} ({len(data)} bytes)")
        """
        import json

        try:
            # 1. Receive metadata as text frame
            meta_bytes = await self.transport.receive()
            meta = json.loads(meta_bytes.decode("utf-8"))
            self.logger.debug(f"Received binary metadata: {meta}")

            # Validate metadata type
            if meta.get("type") != "binary_data":
                self.logger.warning(
                    f"Expected binary_data message, got: {meta.get('type')}"
                )

            # 2. Receive actual binary data
            data = await self.transport.receive_binary()
            self.logger.debug(f"Received {len(data)} bytes of binary data")

            # 3. Validate size if requested
            if validate_size and "size" in meta:
                expected_size = meta["size"]
                actual_size = len(data)
                if actual_size != expected_size:
                    error_msg = (
                        f"Size mismatch: expected {expected_size} bytes, "
                        f"got {actual_size} bytes"
                    )
                    self.logger.error(error_msg)
                    raise ValueError(error_msg)

            return data, meta

        except Exception as e:
            self.logger.error(f"Error receiving binary message: {e}")
            raise

    async def send_file(
        self,
        file_path: str,
        chunk_size: int = 1024 * 1024,  # 1MB chunks
        compute_checksum: bool = True,
    ) -> None:
        """
        Send a file in chunks (for large files).

        Sends large files by splitting them into chunks and sending
        a completion message with checksum for validation.

        Protocol:
        1. Send file_transfer_start message (text frame)
        2. Send file chunks as binary messages
        3. Send file_transfer_complete message with checksum (text frame)

        :param file_path: Path to file to send
        :param chunk_size: Size of each chunk in bytes (default: 1MB)
        :param compute_checksum: If True, computes and sends MD5 checksum
        :raises: FileNotFoundError if file doesn't exist
        :raises: IOError if send fails

        Example:
            # Send a large video file
            await protocol.send_file(
                "video.mp4",
                chunk_size=2 * 1024 * 1024  # 2MB chunks
            )
        """
        import hashlib
        import os

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        file_size = os.path.getsize(file_path)
        file_name = os.path.basename(file_path)
        total_chunks = (file_size + chunk_size - 1) // chunk_size

        # Detect MIME type
        import mimetypes
        import json

        mime_type, _ = mimetypes.guess_type(file_path)

        # Send file header (as JSON string)
        header_msg = {
            "type": "file_transfer_start",
            "filename": file_name,
            "size": file_size,
            "chunk_size": chunk_size,
            "total_chunks": total_chunks,
            "mime_type": mime_type,
        }
        await self.transport.send(json.dumps(header_msg).encode("utf-8"))

        # Send file in chunks
        md5_hash = hashlib.md5() if compute_checksum else None

        with open(file_path, "rb") as f:
            chunk_num = 0

            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break

                if md5_hash:
                    md5_hash.update(chunk)

                await self.send_binary_message(
                    chunk, {"chunk_num": chunk_num, "chunk_size": len(chunk)}
                )

                chunk_num += 1
                self.logger.info(f"Sent chunk {chunk_num}/{total_chunks}")

        # Send completion with checksum (as JSON string)
        completion_msg = {
            "type": "file_transfer_complete",
            "filename": file_name,
            "total_chunks": chunk_num,
        }

        if md5_hash:
            completion_msg["checksum"] = md5_hash.hexdigest()

        await self.transport.send(json.dumps(completion_msg).encode("utf-8"))
        self.logger.info(f"File transfer complete: {file_name}")

    async def receive_file(
        self, output_path: str, validate_checksum: bool = True
    ) -> Dict[str, Any]:
        """
        Receive a file that was sent in chunks.

        Receives a chunked file transfer and writes to the specified path.
        Validates checksum if provided.

        :param output_path: Path where received file should be saved
        :param validate_checksum: If True, validates MD5 checksum
        :return: Dictionary with transfer metadata (filename, size, checksum, etc.)
        :raises: IOError if receive fails
        :raises: ValueError if checksum validation fails

        Example:
            # Receive a file
            metadata = await protocol.receive_file("downloads/received_video.mp4")
            print(f"Received: {metadata['filename']} ({metadata['size']} bytes)")
        """
        import hashlib
        import json
        import os

        # 1. Receive file header
        header_bytes = await self.transport.receive()
        header = json.loads(header_bytes.decode("utf-8"))

        if header.get("type") != "file_transfer_start":
            raise ValueError(f"Expected file_transfer_start, got: {header.get('type')}")

        filename = header["filename"]
        total_size = header["size"]
        total_chunks = header["total_chunks"]

        self.logger.info(
            f"Receiving file: {filename} ({total_size} bytes, {total_chunks} chunks)"
        )

        # 2. Receive chunks and write to file
        md5_hash = hashlib.md5() if validate_checksum else None
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

        with open(output_path, "wb") as f:
            for chunk_num in range(total_chunks):
                data, chunk_meta = await self.receive_binary_message()

                if md5_hash:
                    md5_hash.update(data)

                f.write(data)
                self.logger.info(f"Received chunk {chunk_num + 1}/{total_chunks}")

        # 3. Receive completion message
        completion_bytes = await self.transport.receive()
        completion = json.loads(completion_bytes.decode("utf-8"))

        if completion.get("type") != "file_transfer_complete":
            raise ValueError(
                f"Expected file_transfer_complete, got: {completion.get('type')}"
            )

        # 4. Validate checksum
        if validate_checksum and "checksum" in completion:
            expected_checksum = completion["checksum"]
            actual_checksum = md5_hash.hexdigest()

            if actual_checksum != expected_checksum:
                error_msg = (
                    f"Checksum mismatch: expected {expected_checksum}, "
                    f"got {actual_checksum}"
                )
                self.logger.error(error_msg)
                raise ValueError(error_msg)

            self.logger.info(f"Checksum validated: {actual_checksum}")

        self.logger.info(f"File received successfully: {output_path}")

        return {
            "filename": filename,
            "size": total_size,
            "output_path": output_path,
            "checksum": completion.get("checksum"),
        }


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
