# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Test AIP Resilience Mechanisms

Tests reconnection, heartbeat management, and timeout handling.
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from aip.protocol.heartbeat import HeartbeatProtocol
from aip.resilience import (
    HeartbeatManager,
    ReconnectionPolicy,
    ReconnectionStrategy,
    TimeoutManager,
)
from aip.transport import TransportState


class TestReconnectionStrategy:
    """Test reconnection strategy."""

    @pytest.mark.asyncio
    async def test_exponential_backoff(self):
        """Test exponential backoff calculation."""
        strategy = ReconnectionStrategy(
            max_retries=3,
            initial_backoff=1.0,
            max_backoff=10.0,
            backoff_multiplier=2.0,
            policy=ReconnectionPolicy.EXPONENTIAL_BACKOFF,
        )

        # Test backoff calculation
        assert strategy._calculate_backoff() == 1.0
        strategy._retry_count = 1
        assert strategy._calculate_backoff() == 2.0
        strategy._retry_count = 2
        assert strategy._calculate_backoff() == 4.0
        strategy._retry_count = 10
        assert strategy._calculate_backoff() == 10.0  # Capped at max_backoff

    @pytest.mark.asyncio
    async def test_linear_backoff(self):
        """Test linear backoff calculation."""
        strategy = ReconnectionStrategy(
            max_retries=3,
            initial_backoff=2.0,
            max_backoff=10.0,
            policy=ReconnectionPolicy.LINEAR_BACKOFF,
        )

        assert strategy._calculate_backoff() == 2.0
        strategy._retry_count = 1
        assert strategy._calculate_backoff() == 4.0
        strategy._retry_count = 2
        assert strategy._calculate_backoff() == 6.0

    @pytest.mark.asyncio
    async def test_immediate_reconnect(self):
        """Test immediate reconnection policy."""
        strategy = ReconnectionStrategy(
            policy=ReconnectionPolicy.IMMEDIATE,
        )

        assert strategy._calculate_backoff() == 0.0

    @pytest.mark.asyncio
    async def test_reset(self):
        """Test resetting retry counter."""
        strategy = ReconnectionStrategy()
        strategy._retry_count = 5

        strategy.reset()

        assert strategy._retry_count == 0


class TestHeartbeatManager:
    """Test heartbeat manager."""

    @pytest.fixture
    def mock_protocol(self):
        """Create mock heartbeat protocol."""
        from aip.transport import Transport, TransportState

        class MockTransport(Transport):
            def __init__(self):
                super().__init__()
                self._state = TransportState.CONNECTED

            async def connect(self, url: str, **kwargs) -> None:
                pass

            async def send(self, data: bytes) -> None:
                pass

            async def receive(self) -> bytes:
                return b""

            async def close(self) -> None:
                pass

            async def wait_closed(self) -> None:
                pass

        transport = MockTransport()
        protocol = HeartbeatProtocol(transport)
        protocol.send_heartbeat = AsyncMock()
        return protocol

    @pytest.mark.asyncio
    async def test_start_heartbeat(self, mock_protocol):
        """Test starting heartbeat."""
        manager = HeartbeatManager(mock_protocol, default_interval=0.1)

        await manager.start_heartbeat("test_client", interval=0.1)

        assert manager.is_running("test_client")
        assert manager.get_interval("test_client") == 0.1

        # Wait for heartbeat
        await asyncio.sleep(0.15)

        # Stop heartbeat
        await manager.stop_heartbeat("test_client")

        assert not manager.is_running("test_client")

    @pytest.mark.asyncio
    async def test_stop_nonexistent_heartbeat(self, mock_protocol):
        """Test stopping non-existent heartbeat."""
        manager = HeartbeatManager(mock_protocol)

        # Should not raise error
        await manager.stop_heartbeat("nonexistent_client")

    @pytest.mark.asyncio
    async def test_stop_all_heartbeats(self, mock_protocol):
        """Test stopping all heartbeats."""
        manager = HeartbeatManager(mock_protocol, default_interval=0.1)

        await manager.start_heartbeat("client1", interval=0.1)
        await manager.start_heartbeat("client2", interval=0.1)

        assert manager.is_running("client1")
        assert manager.is_running("client2")

        await manager.stop_all()

        assert not manager.is_running("client1")
        assert not manager.is_running("client2")


class TestTimeoutManager:
    """Test timeout manager."""

    @pytest.mark.asyncio
    async def test_with_timeout_success(self):
        """Test successful operation with timeout."""
        manager = TimeoutManager(default_timeout=1.0)

        async def quick_operation():
            await asyncio.sleep(0.1)
            return "success"

        result = await manager.with_timeout(quick_operation(), operation_name="test")

        assert result == "success"

    @pytest.mark.asyncio
    async def test_with_timeout_exceeded(self):
        """Test timeout exceeded."""
        manager = TimeoutManager(default_timeout=0.1)

        async def slow_operation():
            await asyncio.sleep(1.0)
            return "success"

        with pytest.raises(asyncio.TimeoutError):
            await manager.with_timeout(slow_operation(), operation_name="test")

    @pytest.mark.asyncio
    async def test_with_timeout_or_none(self):
        """Test timeout with None fallback."""
        manager = TimeoutManager(default_timeout=0.1)

        async def slow_operation():
            await asyncio.sleep(1.0)
            return "success"

        result = await manager.with_timeout_or_none(
            slow_operation(), operation_name="test"
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_custom_timeout_override(self):
        """Test overriding default timeout."""
        manager = TimeoutManager(default_timeout=0.1)

        async def medium_operation():
            await asyncio.sleep(0.2)
            return "success"

        # Should timeout with default
        with pytest.raises(asyncio.TimeoutError):
            await manager.with_timeout(medium_operation(), operation_name="test")

        # Should succeed with custom timeout
        result = await manager.with_timeout(
            medium_operation(), timeout=0.5, operation_name="test"
        )
        assert result == "success"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
