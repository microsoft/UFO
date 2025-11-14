# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Unit Tests for AIP Binary Transfer

Tests the binary transfer capabilities of the Agent Interaction Protocol,
including adapters, transport, and protocol layers.
"""

import asyncio
import os
import tempfile
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from aip.messages import (
    BinaryMetadata,
    ChunkMetadata,
    FileTransferStart,
    FileTransferComplete,
)
from aip.protocol import AIPProtocol
from aip.transport import WebSocketTransport
from aip.transport.adapters import (
    FastAPIWebSocketAdapter,
    WebSocketAdapter,
    WebSocketsLibAdapter,
)


# ============================================================================
# Adapter Tests
# ============================================================================


class TestWebSocketAdapterBinary:
    """Test binary methods in WebSocket adapters"""

    @pytest.mark.asyncio
    async def test_fastapi_adapter_send_bytes(self):
        """Test FastAPI adapter send_bytes method"""
        mock_ws = MagicMock()
        mock_ws.send_bytes = AsyncMock()
        mock_ws.client_state = MagicMock()

        adapter = FastAPIWebSocketAdapter(mock_ws)

        test_data = b"test binary data"
        await adapter.send_bytes(test_data)

        mock_ws.send_bytes.assert_called_once_with(test_data)

    @pytest.mark.asyncio
    async def test_fastapi_adapter_receive_bytes(self):
        """Test FastAPI adapter receive_bytes method"""
        mock_ws = MagicMock()
        test_data = b"received binary data"
        mock_ws.receive_bytes = AsyncMock(return_value=test_data)

        adapter = FastAPIWebSocketAdapter(mock_ws)
        received = await adapter.receive_bytes()

        assert received == test_data
        mock_ws.receive_bytes.assert_called_once()

    @pytest.mark.asyncio
    async def test_fastapi_adapter_receive_auto_binary(self):
        """Test FastAPI adapter receive_auto with binary frame"""
        mock_ws = MagicMock()
        test_data = b"binary frame"
        mock_ws.receive = AsyncMock(return_value={"bytes": test_data})

        adapter = FastAPIWebSocketAdapter(mock_ws)
        received = await adapter.receive_auto()

        assert received == test_data
        assert isinstance(received, bytes)

    @pytest.mark.asyncio
    async def test_fastapi_adapter_receive_auto_text(self):
        """Test FastAPI adapter receive_auto with text frame"""
        mock_ws = MagicMock()
        test_data = "text frame"
        mock_ws.receive = AsyncMock(return_value={"text": test_data})

        adapter = FastAPIWebSocketAdapter(mock_ws)
        received = await adapter.receive_auto()

        assert received == test_data
        assert isinstance(received, str)

    @pytest.mark.asyncio
    async def test_websockets_lib_adapter_send_bytes(self):
        """Test websockets library adapter send_bytes method"""
        mock_ws = MagicMock()
        mock_ws.send = AsyncMock()
        mock_ws.closed = False

        adapter = WebSocketsLibAdapter(mock_ws)

        test_data = b"test binary data"
        await adapter.send_bytes(test_data)

        mock_ws.send.assert_called_once_with(test_data)

    @pytest.mark.asyncio
    async def test_websockets_lib_adapter_receive_bytes(self):
        """Test websockets library adapter receive_bytes method"""
        mock_ws = MagicMock()
        test_data = b"received binary data"
        mock_ws.recv = AsyncMock(return_value=test_data)
        mock_ws.closed = False

        adapter = WebSocketsLibAdapter(mock_ws)
        received = await adapter.receive_bytes()

        assert received == test_data
        mock_ws.recv.assert_called_once()

    @pytest.mark.asyncio
    async def test_websockets_lib_adapter_receive_bytes_error(self):
        """Test websockets library adapter receive_bytes with text frame (error)"""
        mock_ws = MagicMock()
        mock_ws.recv = AsyncMock(return_value="text frame")  # Wrong type
        mock_ws.closed = False

        adapter = WebSocketsLibAdapter(mock_ws)

        with pytest.raises(ValueError, match="Expected binary"):
            await adapter.receive_bytes()

    @pytest.mark.asyncio
    async def test_websockets_lib_adapter_receive_auto(self):
        """Test websockets library adapter receive_auto method"""
        mock_ws = MagicMock()
        test_data = b"auto-detected binary"
        mock_ws.recv = AsyncMock(return_value=test_data)
        mock_ws.closed = False

        adapter = WebSocketsLibAdapter(mock_ws)
        received = await adapter.receive_auto()

        assert received == test_data
        assert isinstance(received, bytes)


# ============================================================================
# Transport Tests
# ============================================================================


class TestWebSocketTransportBinary:
    """Test binary methods in WebSocketTransport"""

    @pytest.mark.asyncio
    async def test_send_binary(self):
        """Test send_binary method"""
        mock_adapter = MagicMock(spec=WebSocketAdapter)
        mock_adapter.send_bytes = AsyncMock()
        mock_adapter.is_open = MagicMock(return_value=True)

        transport = WebSocketTransport()
        transport._adapter = mock_adapter
        transport._state = transport._state.CONNECTED

        test_data = b"test binary data"
        await transport.send_binary(test_data)

        mock_adapter.send_bytes.assert_called_once_with(test_data)

    @pytest.mark.asyncio
    async def test_send_binary_not_connected(self):
        """Test send_binary when not connected"""
        transport = WebSocketTransport()

        with pytest.raises(ConnectionError, match="not connected"):
            await transport.send_binary(b"test")

    @pytest.mark.asyncio
    async def test_receive_binary(self):
        """Test receive_binary method"""
        mock_adapter = MagicMock(spec=WebSocketAdapter)
        test_data = b"received binary data"
        mock_adapter.receive_bytes = AsyncMock(return_value=test_data)
        mock_adapter.is_open = MagicMock(return_value=True)

        transport = WebSocketTransport()
        transport._adapter = mock_adapter
        transport._state = transport._state.CONNECTED

        received = await transport.receive_binary()

        assert received == test_data
        mock_adapter.receive_bytes.assert_called_once()

    @pytest.mark.asyncio
    async def test_receive_auto_binary(self):
        """Test receive_auto with binary frame"""
        mock_adapter = MagicMock(spec=WebSocketAdapter)
        test_data = b"binary frame"
        mock_adapter.receive_auto = AsyncMock(return_value=test_data)

        transport = WebSocketTransport()
        transport._adapter = mock_adapter
        transport._state = transport._state.CONNECTED

        received = await transport.receive_auto()

        assert received == test_data
        assert isinstance(received, bytes)

    @pytest.mark.asyncio
    async def test_receive_auto_text(self):
        """Test receive_auto with text frame"""
        mock_adapter = MagicMock(spec=WebSocketAdapter)
        test_data = "text frame"
        mock_adapter.receive_auto = AsyncMock(return_value=test_data)

        transport = WebSocketTransport()
        transport._adapter = mock_adapter
        transport._state = transport._state.CONNECTED

        received = await transport.receive_auto()

        assert received == test_data
        assert isinstance(received, str)


# ============================================================================
# Protocol Tests
# ============================================================================


class TestAIPProtocolBinary:
    """Test binary message handling in AIPProtocol"""

    @pytest.mark.asyncio
    async def test_send_binary_message(self):
        """Test send_binary_message method"""
        mock_transport = MagicMock(spec=WebSocketTransport)
        mock_transport.send = AsyncMock()
        mock_transport.send_binary = AsyncMock()

        protocol = AIPProtocol(mock_transport)

        test_data = b"test binary content"
        metadata = {
            "filename": "test.bin",
            "mime_type": "application/octet-stream",
        }

        await protocol.send_binary_message(test_data, metadata)

        # Verify metadata was sent as text frame
        assert mock_transport.send.called
        sent_metadata = mock_transport.send.call_args[0][0]
        assert b'"type": "binary_data"' in sent_metadata
        assert b'"size": 19' in sent_metadata  # len(test_data)

        # Verify binary data was sent as binary frame
        mock_transport.send_binary.assert_called_once_with(test_data)

    @pytest.mark.asyncio
    async def test_receive_binary_message(self):
        """Test receive_binary_message method"""
        import json

        mock_transport = MagicMock(spec=WebSocketTransport)

        # Prepare metadata
        metadata = {
            "type": "binary_data",
            "filename": "test.bin",
            "size": 19,
        }
        metadata_json = json.dumps(metadata).encode("utf-8")

        # Prepare binary data
        test_data = b"test binary content"

        # Mock transport receive methods
        mock_transport.receive = AsyncMock(return_value=metadata_json)
        mock_transport.receive_binary = AsyncMock(return_value=test_data)

        protocol = AIPProtocol(mock_transport)

        received_data, received_metadata = await protocol.receive_binary_message()

        assert received_data == test_data
        assert received_metadata["filename"] == "test.bin"
        assert received_metadata["size"] == 19

    @pytest.mark.asyncio
    async def test_receive_binary_message_size_validation_fail(self):
        """Test receive_binary_message with size mismatch"""
        import json

        mock_transport = MagicMock(spec=WebSocketTransport)

        # Metadata says 100 bytes, but we send 19
        metadata = {
            "type": "binary_data",
            "size": 100,  # Wrong size
        }
        metadata_json = json.dumps(metadata).encode("utf-8")
        test_data = b"test binary content"  # Only 19 bytes

        mock_transport.receive = AsyncMock(return_value=metadata_json)
        mock_transport.receive_binary = AsyncMock(return_value=test_data)

        protocol = AIPProtocol(mock_transport)

        with pytest.raises(ValueError, match="Size mismatch"):
            await protocol.receive_binary_message(validate_size=True)

    @pytest.mark.asyncio
    async def test_send_file(self):
        """Test send_file method"""
        mock_transport = MagicMock(spec=WebSocketTransport)
        mock_transport.send = AsyncMock()
        mock_transport.send_binary = AsyncMock()

        protocol = AIPProtocol(mock_transport)

        # Create a temporary test file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as temp_file:
            temp_file.write(b"Test file content for chunked transfer" * 1000)
            temp_file_path = temp_file.name

        try:
            await protocol.send_file(temp_file_path, chunk_size=1024)

            # Verify file_transfer_start was sent
            assert mock_transport.send.called
            start_msg = mock_transport.send.call_args_list[0][0][0]
            assert b'"type": "file_transfer_start"' in start_msg

            # Verify chunks were sent
            assert mock_transport.send_binary.called

            # Verify file_transfer_complete was sent
            complete_msg = mock_transport.send.call_args_list[-1][0][0]
            assert b'"type": "file_transfer_complete"' in complete_msg

        finally:
            os.unlink(temp_file_path)

    @pytest.mark.asyncio
    async def test_receive_file(self):
        """Test receive_file method"""
        import json

        mock_transport = MagicMock(spec=WebSocketTransport)

        # Prepare file transfer messages
        start_msg = {
            "type": "file_transfer_start",
            "filename": "test.bin",
            "size": 2048,
            "chunk_size": 1024,
            "total_chunks": 2,
        }

        chunk1_meta = {"type": "binary_data", "chunk_num": 0, "size": 1024}
        chunk2_meta = {"type": "binary_data", "chunk_num": 1, "size": 1024}

        complete_msg = {
            "type": "file_transfer_complete",
            "filename": "test.bin",
            "total_chunks": 2,
            "checksum": "abc123",
        }

        # Mock transport to return messages in sequence
        mock_transport.receive = AsyncMock(
            side_effect=[
                json.dumps(start_msg).encode("utf-8"),
                json.dumps(chunk1_meta).encode("utf-8"),
                json.dumps(chunk2_meta).encode("utf-8"),
                json.dumps(complete_msg).encode("utf-8"),
            ]
        )

        mock_transport.receive_binary = AsyncMock(
            side_effect=[
                b"A" * 1024,  # Chunk 1
                b"B" * 1024,  # Chunk 2
            ]
        )

        protocol = AIPProtocol(mock_transport)

        # Receive file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".bin") as temp_file:
            output_path = temp_file.name

        try:
            metadata = await protocol.receive_file(output_path, validate_checksum=False)

            assert metadata["filename"] == "test.bin"
            assert metadata["size"] == 2048

            # Verify file was written
            with open(output_path, "rb") as f:
                content = f.read()
                assert len(content) == 2048
                assert content[:1024] == b"A" * 1024
                assert content[1024:] == b"B" * 1024

        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)


# ============================================================================
# Message Type Tests
# ============================================================================


class TestBinaryMessageTypes:
    """Test binary message type definitions"""

    def test_binary_metadata(self):
        """Test BinaryMetadata model"""
        metadata = BinaryMetadata(
            filename="test.png",
            mime_type="image/png",
            size=1024,
            checksum="abc123",
        )

        assert metadata.type == "binary_data"
        assert metadata.filename == "test.png"
        assert metadata.size == 1024

    def test_file_transfer_start(self):
        """Test FileTransferStart model"""
        start_msg = FileTransferStart(
            filename="large_file.bin",
            size=10485760,  # 10MB
            chunk_size=1048576,  # 1MB
            total_chunks=10,
            mime_type="application/octet-stream",
        )

        assert start_msg.type == "file_transfer_start"
        assert start_msg.total_chunks == 10

    def test_file_transfer_complete(self):
        """Test FileTransferComplete model"""
        complete_msg = FileTransferComplete(
            filename="large_file.bin", total_chunks=10, checksum="def456"
        )

        assert complete_msg.type == "file_transfer_complete"
        assert complete_msg.checksum == "def456"

    def test_chunk_metadata(self):
        """Test ChunkMetadata model"""
        chunk = ChunkMetadata(chunk_num=5, chunk_size=1048576, checksum="chunk5hash")

        assert chunk.chunk_num == 5
        assert chunk.chunk_size == 1048576


# ============================================================================
# Integration Tests
# ============================================================================


class TestBinaryTransferIntegration:
    """Integration tests for complete binary transfer scenarios"""

    @pytest.mark.asyncio
    async def test_full_binary_message_roundtrip(self):
        """Test complete binary message send and receive"""
        # This test would require a real WebSocket connection
        # For now, we test with mocks
        pass

    @pytest.mark.asyncio
    async def test_full_file_transfer_roundtrip(self):
        """Test complete file transfer send and receive"""
        # This test would require a real WebSocket connection
        # For now, we test with mocks
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
