# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Test AIP Messages

Tests message validation, serialization, and deserialization.
"""

import pytest

from aip.messages import (
    ClientMessage,
    ClientMessageType,
    ClientType,
    Command,
    MessageValidator,
    Result,
    ResultStatus,
    ServerMessage,
    ServerMessageType,
    TaskStatus,
)


class TestMessages:
    """Test message structures and validation."""

    def test_client_message_creation(self):
        """Test creating a valid client message."""
        msg = ClientMessage(
            type=ClientMessageType.REGISTER,
            client_id="test_device",
            client_type=ClientType.DEVICE,
            status=TaskStatus.OK,
            metadata={"platform": "windows"},
        )

        assert msg.type == ClientMessageType.REGISTER
        assert msg.client_id == "test_device"
        assert msg.client_type == ClientType.DEVICE
        assert msg.status == TaskStatus.OK
        assert msg.metadata["platform"] == "windows"

    def test_server_message_creation(self):
        """Test creating a valid server message."""
        msg = ServerMessage(
            type=ServerMessageType.COMMAND,
            status=TaskStatus.CONTINUE,
            actions=[
                Command(
                    tool_name="test_tool",
                    tool_type="action",
                    parameters={"key": "value"},
                )
            ],
            response_id="resp_123",
        )

        assert msg.type == ServerMessageType.COMMAND
        assert msg.status == TaskStatus.CONTINUE
        assert len(msg.actions) == 1
        assert msg.actions[0].tool_name == "test_tool"
        assert msg.response_id == "resp_123"

    def test_message_serialization(self):
        """Test message serialization to JSON."""
        msg = ClientMessage(
            type=ClientMessageType.HEARTBEAT,
            client_id="test_device",
            status=TaskStatus.OK,
        )

        json_str = msg.model_dump_json()
        assert isinstance(json_str, str)
        assert "heartbeat" in json_str.lower()
        assert "test_device" in json_str

    def test_message_deserialization(self):
        """Test message deserialization from JSON."""
        json_str = """
        {
            "type": "register",
            "status": "ok",
            "client_type": "device",
            "client_id": "test_device",
            "metadata": {"platform": "linux"}
        }
        """

        msg = ClientMessage.model_validate_json(json_str)
        assert msg.type == ClientMessageType.REGISTER
        assert msg.client_id == "test_device"
        assert msg.metadata["platform"] == "linux"

    def test_command_structure(self):
        """Test command structure."""
        cmd = Command(
            tool_name="get_screenshot",
            tool_type="data_collection",
            parameters={"window": "active"},
            call_id="call_123",
        )

        assert cmd.tool_name == "get_screenshot"
        assert cmd.tool_type == "data_collection"
        assert cmd.parameters["window"] == "active"
        assert cmd.call_id == "call_123"

    def test_result_structure(self):
        """Test result structure."""
        result = Result(
            status=ResultStatus.SUCCESS,
            result={"screenshot": "base64data"},
            namespace="ui",
            call_id="call_123",
        )

        assert result.status == ResultStatus.SUCCESS
        assert result.result["screenshot"] == "base64data"
        assert result.namespace == "ui"

    def test_result_with_error(self):
        """Test result with error."""
        result = Result(
            status=ResultStatus.FAILURE,
            error="Window not found",
            call_id="call_123",
        )

        assert result.status == ResultStatus.FAILURE
        assert result.error == "Window not found"
        assert result.result is None


class TestMessageValidator:
    """Test message validation."""

    def test_validate_registration(self):
        """Test registration message validation."""
        valid_msg = ClientMessage(
            type=ClientMessageType.REGISTER,
            client_id="test_device",
            status=TaskStatus.OK,
        )

        assert MessageValidator.validate_registration(valid_msg) is True

    def test_validate_registration_missing_client_id(self):
        """Test registration validation fails without client_id."""
        invalid_msg = ClientMessage(
            type=ClientMessageType.REGISTER,
            status=TaskStatus.OK,
        )

        assert MessageValidator.validate_registration(invalid_msg) is False

    def test_validate_task_request(self):
        """Test task request validation."""
        valid_msg = ClientMessage(
            type=ClientMessageType.TASK,
            client_id="test_device",
            request="Execute task",
            status=TaskStatus.CONTINUE,
        )

        assert MessageValidator.validate_task_request(valid_msg) is True

    def test_validate_task_request_missing_request(self):
        """Test task request validation fails without request."""
        invalid_msg = ClientMessage(
            type=ClientMessageType.TASK,
            client_id="test_device",
            status=TaskStatus.CONTINUE,
        )

        assert MessageValidator.validate_task_request(invalid_msg) is False

    def test_validate_command_results(self):
        """Test command results validation."""
        valid_msg = ClientMessage(
            type=ClientMessageType.COMMAND_RESULTS,
            client_id="test_device",
            prev_response_id="resp_123",
            action_results=[Result(status=ResultStatus.SUCCESS)],
            status=TaskStatus.CONTINUE,
        )

        assert MessageValidator.validate_command_results(valid_msg) is True

    def test_validate_server_message(self):
        """Test server message validation."""
        valid_msg = ServerMessage(
            type=ServerMessageType.COMMAND,
            status=TaskStatus.CONTINUE,
            actions=[Command(tool_name="test", tool_type="action")],
            response_id="resp_123",
        )

        assert MessageValidator.validate_server_message(valid_msg) is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
