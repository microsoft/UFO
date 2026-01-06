"""
Integration tests for device agent server-client communication using AIP.

Tests the complete message flow between UFO server and client using the
refactored AIP protocol implementation.
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, Mock, patch

from aip.messages import (
    ClientMessage,
    ClientMessageType,
    Command,
    Result,
    ResultStatus,
    ServerMessage,
    ServerMessageType,
    TaskStatus,
)
from ufo.module.dispatcher import WebSocketCommandDispatcher


class MockWebSocket:
    """Mock WebSocket for testing (simulates FastAPI WebSocket)."""

    def __init__(self):
        self.sent_messages = []
        # Simulate FastAPI WebSocket with client_state attribute
        from starlette.websockets import WebSocketState

        self.client_state = WebSocketState.CONNECTED
        self.closed = False
        # Add application_state to be recognized as FastAPI WebSocket
        self.application_state = "connected"

    async def send_text(self, message: str):
        """Mock send_text method."""
        self.sent_messages.append(message)

    async def close(self):
        """Mock close method."""
        from starlette.websockets import WebSocketState

        self.client_state = WebSocketState.DISCONNECTED
        self.closed = True

    async def receive_text(self):
        """Mock receive_text method."""
        # Return a mock client message
        return ClientMessage(
            type=ClientMessageType.COMMAND_RESULTS,
            session_id="test_session",
            client_id="test_device",
            request_id="req_123",
            prev_response_id="resp_123",
            action_results=[
                Result(
                    status=ResultStatus.SUCCESS,
                    result="Command executed",
                    call_id="cmd_123",
                )
            ],
            status=TaskStatus.CONTINUE,
            timestamp="2024-01-01T00:00:00Z",
        ).model_dump_json()

    def send(self, data):
        """Synchronous send for compatibility."""
        self.sent_messages.append(data)


class MockSession:
    """Mock session for testing."""

    def __init__(self):
        self.id = "test_session"
        self.task = "test_task"
        self.current_agent_class = "TestAgent"
        self.context = MagicMock()
        self.context.get = Mock(return_value="test_value")
        self.context.command_dispatcher = None


@pytest.mark.asyncio
async def test_websocket_command_dispatcher_with_aip():
    """Test that WebSocketCommandDispatcher uses AIP protocol correctly."""
    # Setup
    mock_ws = MockWebSocket()
    mock_session = MockSession()

    dispatcher = WebSocketCommandDispatcher(mock_session, mock_ws)

    # Verify AIP components are initialized
    assert dispatcher.transport is not None
    assert dispatcher.protocol is not None

    # Manually set transport to connected state (mock doesn't auto-connect)
    from aip.transport.base import TransportState

    dispatcher.transport._state = TransportState.CONNECTED

    # Create test commands
    commands = [
        Command(
            tool_name="screenshot",
            tool_type="data_collection",
            call_id="cmd_1",
        ),
        Command(
            tool_name="click",
            tool_type="action",
            arguments={"x": 100, "y": 200},
            call_id="cmd_2",
        ),
    ]

    # Execute commands (this will timeout waiting for response, but we just want to verify sending)
    try:
        await asyncio.wait_for(
            dispatcher.execute_commands(commands, timeout=0.1), timeout=0.2
        )
    except asyncio.TimeoutError:
        pass  # Expected - we're not mocking the full response flow

    # Verify message was sent through AIP transport
    assert len(mock_ws.sent_messages) > 0

    # Parse the sent message
    sent_message = ServerMessage.model_validate_json(mock_ws.sent_messages[0])
    assert sent_message.type == ServerMessageType.COMMAND
    assert sent_message.actions is not None
    assert len(sent_message.actions) == 2
    assert sent_message.actions[0].tool_name == "screenshot"
    assert sent_message.actions[1].tool_name == "click"


@pytest.mark.asyncio
async def test_command_dispatcher_error_handling():
    """Test error handling in WebSocketCommandDispatcher."""
    mock_ws = MockWebSocket()
    mock_session = MockSession()

    dispatcher = WebSocketCommandDispatcher(mock_session, mock_ws)

    # Create a command that will fail
    commands = [
        Command(
            tool_name="invalid_tool",
            tool_type="action",
            call_id="cmd_error",
        )
    ]

    # Mock transport to raise an error
    with patch.object(
        dispatcher.protocol, "send_command", side_effect=Exception("Network error")
    ):
        results = await dispatcher.execute_commands(commands, timeout=1.0)

    # Verify error results are returned
    assert results is not None
    assert len(results) == 1
    assert results[0].status == ResultStatus.FAILURE
    assert "Network error" in results[0].error


@pytest.mark.asyncio
async def test_dispatcher_backward_compatibility():
    """Test that refactored dispatcher maintains backward compatibility."""
    mock_ws = MockWebSocket()
    mock_session = MockSession()

    # Old code should still work
    dispatcher = WebSocketCommandDispatcher(mock_session, mock_ws)

    # Test make_server_response (used by existing code)
    commands = [Command(tool_name="test", tool_type="action")]
    server_msg = dispatcher.make_server_response(commands)

    assert server_msg.type == ServerMessageType.COMMAND
    assert server_msg.session_id == mock_session.id
    assert server_msg.task_name == mock_session.task
    assert len(server_msg.actions) == 1


@pytest.mark.asyncio
async def test_set_result_with_aip():
    """Test that set_result works correctly with AIP refactoring."""
    mock_ws = MockWebSocket()
    mock_session = MockSession()

    dispatcher = WebSocketCommandDispatcher(mock_session, mock_ws)

    # Create a pending request
    response_id = "resp_test_123"
    fut = asyncio.get_event_loop().create_future()
    dispatcher.pending[response_id] = fut

    # Create mock client message with results
    client_msg = ClientMessage(
        type=ClientMessageType.COMMAND_RESULTS,
        session_id="test_session",
        client_id="test_device",
        prev_response_id=response_id,
        action_results=[
            Result(
                status=ResultStatus.SUCCESS,
                result="Success",
                call_id="cmd_123",
            )
        ],
        status=TaskStatus.CONTINUE,
        timestamp="2024-01-01T00:00:00Z",
    )

    # Set the result
    await dispatcher.set_result(response_id, client_msg)

    # Verify the future was resolved
    assert fut.done()
    result = fut.result()
    assert len(result) == 1
    assert result[0].status == ResultStatus.SUCCESS


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
