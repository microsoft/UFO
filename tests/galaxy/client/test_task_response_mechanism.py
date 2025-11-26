# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Test Task Response Mechanism

Comprehensive tests for the task response Future-based mechanism that enables
synchronous waiting for asynchronous task completion.

This test suite validates:
1. Future creation and registration in ConnectionManager
2. MessageProcessor completing the Future when TASK_END is received
3. send_task_to_device() receiving the response
4. Error handling (timeout, duplicate responses, unknown tasks)
5. Memory cleanup (Future removal after completion/timeout)
"""

import asyncio
import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch, call
from websockets import WebSocketClientProtocol

# Import components under test
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from galaxy.client.components.connection_manager import WebSocketConnectionManager
from galaxy.client.components.message_processor import MessageProcessor
from galaxy.client.components.device_registry import DeviceRegistry
from galaxy.client.components.heartbeat_manager import HeartbeatManager
from galaxy.client.components.types import AgentProfile, TaskRequest

from aip.messages import (
    ServerMessage,
    ServerMessageType,
    TaskStatus,
    ClientMessage,
    ClientMessageType,
)


class TestTaskResponseMechanism:
    """Test suite for the Future-based task response mechanism"""

    @pytest.fixture
    def constellation_id(self):
        """Constellation ID for testing"""
        return "test_constellation_001"

    @pytest.fixture
    def device_id(self):
        """Device ID for testing"""
        return "device_001"

    @pytest.fixture
    def task_id(self):
        """Task ID for testing"""
        return "task_12345"

    @pytest.fixture
    def connection_manager(self, constellation_id):
        """Create ConnectionManager instance"""
        return WebSocketConnectionManager(constellation_id=constellation_id)

    @pytest.fixture
    def device_registry(self):
        """Create DeviceRegistry instance"""
        return DeviceRegistry()

    @pytest.fixture
    def heartbeat_manager(self, connection_manager, device_registry):
        """Create HeartbeatManager instance"""
        return HeartbeatManager(
            connection_manager=connection_manager,
            device_registry=device_registry,
            heartbeat_interval=30.0,
        )

    @pytest.fixture
    def message_processor(self, device_registry, heartbeat_manager):
        """Create MessageProcessor instance"""
        return MessageProcessor(
            device_registry=device_registry,
            heartbeat_manager=heartbeat_manager,
        )

    @pytest.fixture
    def mock_websocket(self):
        """Create mock WebSocket connection"""
        mock_ws = AsyncMock(spec=WebSocketClientProtocol)
        mock_ws.closed = False
        mock_ws.send = AsyncMock()
        mock_ws.recv = AsyncMock()
        mock_ws.close = AsyncMock()
        return mock_ws

    @pytest.fixture
    def device_info(self, device_id):
        """Create device info for testing"""
        return AgentProfile(
            device_id=device_id,
            server_url="ws://localhost:8000/ws",
            capabilities={},
        )

    @pytest.fixture
    def task_request(self, task_id, device_id):
        """Create task request for testing"""
        return TaskRequest(
            task_id=task_id,
            device_id=device_id,
            task_name="test_task",
            request="Execute test command",
            timeout=10.0,
        )

    @pytest.mark.asyncio
    async def test_wait_for_task_response_creates_future(
        self, connection_manager, device_id, task_id
    ):
        """
        Test that _wait_for_task_response creates and registers a Future.

        Validates:
        - Future is created and stored in _pending_tasks
        - Future is in pending state initially
        - task_id is used as the dictionary key
        """
        # Start waiting in the background
        wait_task = asyncio.create_task(
            connection_manager._wait_for_task_response(device_id, task_id)
        )

        # Give it time to create the Future
        await asyncio.sleep(0.1)

        # Verify Future was created and is pending
        assert task_id in connection_manager._pending_tasks
        task_future = connection_manager._pending_tasks[task_id]
        assert isinstance(task_future, asyncio.Future)
        assert not task_future.done()

        # Clean up - complete the Future to allow wait_task to finish
        response = ServerMessage(
            type=ServerMessageType.TASK_END,
            response_id=task_id,
            status=TaskStatus.COMPLETED,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        task_future.set_result(response)
        await wait_task

    @pytest.mark.asyncio
    async def test_complete_task_response_resolves_future(
        self, connection_manager, device_id, task_id
    ):
        """
        Test that complete_task_response resolves the pending Future.

        Validates:
        - complete_task_response finds the correct Future
        - Future is resolved with the ServerMessage
        - _wait_for_task_response returns the ServerMessage
        """
        # Start waiting for response
        wait_task = asyncio.create_task(
            connection_manager._wait_for_task_response(device_id, task_id)
        )

        # Give it time to register the Future
        await asyncio.sleep(0.1)

        # Create server response
        server_response = ServerMessage(
            type=ServerMessageType.TASK_END,
            response_id=task_id,
            status=TaskStatus.COMPLETED,
            result={"output": "success"},
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

        # Complete the task response (simulating MessageProcessor)
        connection_manager.complete_task_response(task_id, server_response)

        # Verify wait_task completes with the correct response
        result = await wait_task
        assert result == server_response
        assert result.status == TaskStatus.COMPLETED
        assert result.result == {"output": "success"}

    @pytest.mark.asyncio
    async def test_complete_task_response_cleans_up_future(
        self, connection_manager, device_id, task_id
    ):
        """
        Test that Future is cleaned up after completion.

        Validates:
        - Future is removed from _pending_tasks after completion
        - No memory leaks from completed Futures
        """
        # Start waiting for response
        wait_task = asyncio.create_task(
            connection_manager._wait_for_task_response(device_id, task_id)
        )
        await asyncio.sleep(0.1)

        # Verify Future exists
        assert task_id in connection_manager._pending_tasks

        # Complete the response
        server_response = ServerMessage(
            type=ServerMessageType.TASK_END,
            response_id=task_id,
            status=TaskStatus.COMPLETED,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        connection_manager.complete_task_response(task_id, server_response)

        # Wait for completion
        await wait_task

        # Verify Future was cleaned up
        assert task_id not in connection_manager._pending_tasks

    @pytest.mark.asyncio
    async def test_complete_task_response_unknown_task_warning(
        self, connection_manager, task_id, caplog
    ):
        """
        Test that completing an unknown task logs a warning.

        Validates:
        - Warning is logged when task_id not found
        - No exception is raised
        - System continues to operate normally
        """
        import logging

        with caplog.at_level(logging.WARNING):
            # Create response for unknown task
            server_response = ServerMessage(
                type=ServerMessageType.TASK_END,
                response_id=task_id,
                status=TaskStatus.COMPLETED,
                timestamp=datetime.now(timezone.utc).isoformat(),
            )

            # Try to complete unknown task
            connection_manager.complete_task_response(task_id, server_response)

            # Verify warning was logged
            assert "unknown task" in caplog.text.lower()
            assert task_id in caplog.text

    @pytest.mark.asyncio
    async def test_complete_task_response_duplicate_warning(
        self, connection_manager, device_id, task_id, caplog
    ):
        """
        Test that duplicate completion logs a warning.

        Validates:
        - Warning is logged on duplicate completion
        - Second completion is ignored
        - Original result is preserved
        """
        import logging

        # Start waiting
        wait_task = asyncio.create_task(
            connection_manager._wait_for_task_response(device_id, task_id)
        )
        await asyncio.sleep(0.1)

        # First completion
        response1 = ServerMessage(
            type=ServerMessageType.TASK_END,
            response_id=task_id,
            status=TaskStatus.COMPLETED,
            result={"first": "response"},
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        connection_manager.complete_task_response(task_id, response1)

        # Get the result
        result = await wait_task
        assert result.result == {"first": "response"}

        # Try duplicate completion
        with caplog.at_level(logging.WARNING):
            response2 = ServerMessage(
                type=ServerMessageType.TASK_END,
                response_id=task_id,
                status=TaskStatus.COMPLETED,
                result={"second": "response"},
                timestamp=datetime.now(timezone.utc).isoformat(),
            )
            connection_manager.complete_task_response(task_id, response2)

            # Verify warning was logged
            assert (
                "duplicate" in caplog.text.lower()
                or "already completed" in caplog.text.lower()
            )

    @pytest.mark.asyncio
    async def test_message_processor_calls_complete_task_response(
        self, message_processor, connection_manager, device_id, task_id
    ):
        """
        Test that MessageProcessor calls complete_task_response on TASK_END.

        Validates:
        - MessageProcessor correctly identifies TASK_END messages
        - complete_task_response is called with correct parameters
        - Event handlers are also notified
        """
        # Set connection manager reference
        message_processor.set_connection_manager(connection_manager)

        # Create mock to track complete_task_response calls
        with patch.object(
            connection_manager,
            "complete_task_response",
            wraps=connection_manager.complete_task_response,
        ) as mock_complete:
            # Create TASK_END message
            server_msg = ServerMessage(
                type=ServerMessageType.TASK_END,
                response_id=task_id,
                session_id="session_001",
                status=TaskStatus.COMPLETED,
                result={"output": "task completed"},
                timestamp=datetime.now(timezone.utc).isoformat(),
            )

            # Process the message
            await message_processor._handle_task_completion(device_id, server_msg)

            # Verify complete_task_response was called
            mock_complete.assert_called_once_with(task_id, server_msg)

    @pytest.mark.asyncio
    async def test_send_task_to_device_end_to_end(
        self,
        connection_manager,
        message_processor,
        mock_websocket,
        device_info,
        task_request,
    ):
        """
        Test the complete end-to-end task execution flow.

        Validates the full workflow:
        1. send_task_to_device sends task and waits
        2. MessageProcessor receives TASK_END
        3. complete_task_response resolves Future
        4. send_task_to_device returns with result
        """
        # Set up connection
        connection_manager._connections[device_info.device_id] = mock_websocket
        message_processor.set_connection_manager(connection_manager)

        # Simulate server response after delay
        async def simulate_server_response():
            await asyncio.sleep(0.2)  # Simulate server processing time

            # Create server response
            server_response = ServerMessage(
                type=ServerMessageType.TASK_END,
                response_id=task_request.task_id,
                session_id="session_001",
                status=TaskStatus.COMPLETED,
                result={"output": "task executed successfully"},
                timestamp=datetime.now(timezone.utc).isoformat(),
            )

            # Simulate MessageProcessor receiving and handling the message
            await message_processor._handle_task_completion(
                device_info.device_id, server_response
            )

        # Start both tasks
        send_task = asyncio.create_task(
            connection_manager.send_task_to_device(device_info.device_id, task_request)
        )
        response_task = asyncio.create_task(simulate_server_response())

        # Wait for both to complete
        result = await send_task
        await response_task

        # Verify result
        assert result.status == True  # ExecutionResult.status is a boolean
        assert result.result == {"output": "task executed successfully"}
        assert result.task_id == task_request.task_id

        # Verify WebSocket was used
        mock_websocket.send.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_task_timeout_cleans_up_future(
        self, connection_manager, mock_websocket, device_info
    ):
        """
        Test that timeout properly cleans up the pending Future.

        Validates:
        - Timeout exception is raised
        - Future is removed from _pending_tasks
        - No memory leaks
        """
        # Set up connection
        connection_manager._connections[device_info.device_id] = mock_websocket

        # Create task with short timeout
        task_request = TaskRequest(
            task_id="timeout_task",
            device_id=device_info.device_id,
            task_name="test_task",
            request="test request",
            timeout=0.5,  # Short timeout
        )

        # Try to send task (should timeout)
        with pytest.raises(ConnectionError, match="timed out"):
            await connection_manager.send_task_to_device(
                device_info.device_id, task_request
            )

        # Verify Future was cleaned up
        assert task_request.task_id not in connection_manager._pending_tasks

    @pytest.mark.asyncio
    async def test_send_task_exception_cleans_up_future(
        self, connection_manager, mock_websocket, device_info, task_request
    ):
        """
        Test that exceptions during send properly clean up the Future.

        Validates:
        - Exception is propagated
        - Future is removed from _pending_tasks
        - No memory leaks on error
        """
        # Set up connection with failing WebSocket
        connection_manager._connections[device_info.device_id] = mock_websocket
        mock_websocket.send.side_effect = Exception("WebSocket send failed")

        # Try to send task (should fail)
        with pytest.raises(Exception):
            await connection_manager.send_task_to_device(
                device_info.device_id, task_request
            )

        # Verify Future was cleaned up
        assert task_request.task_id not in connection_manager._pending_tasks

    @pytest.mark.asyncio
    async def test_multiple_concurrent_tasks(
        self, connection_manager, message_processor, mock_websocket, device_info
    ):
        """
        Test handling multiple concurrent tasks.

        Validates:
        - Multiple tasks can wait simultaneously
        - Each task gets its own Future
        - Responses are matched correctly to tasks
        - No interference between tasks
        """
        # Set up connection
        connection_manager._connections[device_info.device_id] = mock_websocket
        message_processor.set_connection_manager(connection_manager)

        # Create multiple task requests
        task_requests = [
            TaskRequest(
                task_id=f"task_{i}",
                device_id=device_info.device_id,
                task_name=f"test_task_{i}",
                request=f"request {i}",
                timeout=10.0,
            )
            for i in range(3)
        ]

        # Simulate server responses for each task
        async def simulate_responses():
            await asyncio.sleep(0.1)
            for i, req in enumerate(task_requests):
                server_response = ServerMessage(
                    type=ServerMessageType.TASK_END,
                    response_id=req.task_id,
                    status=TaskStatus.COMPLETED,
                    result={"task_index": i},
                    timestamp=datetime.now(timezone.utc).isoformat(),
                )
                await message_processor._handle_task_completion(
                    device_info.device_id, server_response
                )
                await asyncio.sleep(0.05)  # Small delay between responses

        # Send all tasks concurrently
        send_tasks = [
            asyncio.create_task(
                connection_manager.send_task_to_device(device_info.device_id, req)
            )
            for req in task_requests
        ]
        response_task = asyncio.create_task(simulate_responses())

        # Wait for all tasks
        results = await asyncio.gather(*send_tasks)
        await response_task

        # Verify each result matches its request
        for i, result in enumerate(results):
            assert result.task_id == f"task_{i}"
            assert result.result == {"task_index": i}
            assert result.status == True  # ExecutionResult.status is boolean

        # Verify all Futures are cleaned up
        for req in task_requests:
            assert req.task_id not in connection_manager._pending_tasks

    @pytest.mark.asyncio
    async def test_task_with_error_status(
        self,
        connection_manager,
        message_processor,
        mock_websocket,
        device_info,
        task_request,
    ):
        """
        Test handling of tasks that complete with ERROR status.

        Validates:
        - ERROR status is properly propagated
        - Future is still completed (not left hanging)
        - Error information is preserved
        """
        # Set up connection
        connection_manager._connections[device_info.device_id] = mock_websocket
        message_processor.set_connection_manager(connection_manager)

        # Simulate server error response
        async def simulate_error_response():
            await asyncio.sleep(0.1)
            server_response = ServerMessage(
                type=ServerMessageType.TASK_END,
                response_id=task_request.task_id,
                status=TaskStatus.ERROR,
                error="Task execution failed: Invalid command",
                timestamp=datetime.now(timezone.utc).isoformat(),
            )
            await message_processor._handle_task_completion(
                device_info.device_id, server_response
            )

        # Send task and simulate response
        send_task = asyncio.create_task(
            connection_manager.send_task_to_device(device_info.device_id, task_request)
        )
        response_task = asyncio.create_task(simulate_error_response())

        result = await send_task
        await response_task

        # Verify error status and message
        assert (
            result.status == False
        )  # ExecutionResult.status is boolean (False for error)
        assert result.error == "Task execution failed: Invalid command"

    @pytest.mark.asyncio
    async def test_message_processor_without_connection_manager(
        self, message_processor, device_id, task_id, caplog
    ):
        """
        Test that MessageProcessor handles missing ConnectionManager gracefully.

        Validates:
        - Warning is logged when ConnectionManager not set
        - Event handlers are still notified
        - No exception is raised
        """
        import logging

        # Don't set connection_manager (leave as None)
        assert message_processor.connection_manager is None

        with caplog.at_level(logging.WARNING):
            server_msg = ServerMessage(
                type=ServerMessageType.TASK_END,
                response_id=task_id,
                status=TaskStatus.COMPLETED,
                timestamp=datetime.now(timezone.utc).isoformat(),
            )

            # Process message without ConnectionManager
            await message_processor._handle_task_completion(device_id, server_msg)

            # Verify warning was logged
            assert (
                "ConnectionManager not set" in caplog.text
                or "cannot complete" in caplog.text
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
