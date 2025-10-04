# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Tests for GalaxyClient with proper interface usage.

This test module verifies that GalaxyClient works correctly with the updated
GalaxySession interface and provides proper functionality for both interactive
and batch modes.
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, mock_open
from pathlib import Path
import json

from galaxy.galaxy_client import GalaxyClient
from galaxy.client.constellation_client import ConstellationClient
from galaxy.session.galaxy_session import GalaxySession


class TestGalaxyClient:
    """Test suite for GalaxyClient functionality."""

    @pytest.fixture
    def mock_constellation_client(self):
        """Create a mock ConstellationClient."""
        mock_client = MagicMock(spec=ConstellationClient)
        mock_client.device_manager = MagicMock()
        mock_client.initialize = AsyncMock()
        mock_client.shutdown = AsyncMock()
        return mock_client

    @pytest.fixture
    def mock_galaxy_session(self):
        """Create a mock GalaxySession."""
        mock_session = MagicMock(spec=GalaxySession)
        mock_session.task = "test_task"
        mock_session._rounds = {}
        mock_session.run = AsyncMock()
        mock_session.force_finish = AsyncMock()
        mock_session._current_constellation = None
        mock_session.log_path = "test/path"
        return mock_session

    def test_galaxy_client_initialization(self):
        """Test GalaxyClient initialization."""
        # Test default initialization
        client = GalaxyClient()
        assert client.session_name.startswith("galaxy_session_")
        assert client.max_rounds == 10
        assert client.output_dir == Path("./logs")

        # Test custom initialization
        custom_client = GalaxyClient(
            session_name="custom_session",
            max_rounds=20,
            log_level="DEBUG",
            output_dir="/custom/output",
        )
        assert custom_client.session_name == "custom_session"
        assert custom_client.max_rounds == 20
        assert custom_client.output_dir == Path("/custom/output")

    @pytest.mark.asyncio
    async def test_galaxy_client_initialize(
        self, mock_constellation_client, mock_galaxy_session
    ):
        """Test GalaxyClient initialize method."""
        client = GalaxyClient(session_name="test_session")

        with patch(
            "ufo.galaxy.galaxy_client.ConstellationClient",
            return_value=mock_constellation_client,
        ), patch(
            "ufo.galaxy.galaxy_client.GalaxySession", return_value=mock_galaxy_session
        ):
            await client.initialize()

            # Verify initialization
            assert client._client == mock_constellation_client
            assert client._session == mock_galaxy_session
            mock_constellation_client.initialize.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_request(
        self, mock_constellation_client, mock_galaxy_session
    ):
        """Test processing a single request."""
        client = GalaxyClient(session_name="test_session")
        client._client = mock_constellation_client
        client._session = mock_galaxy_session

        # Mock constellation for result testing
        mock_constellation = MagicMock()
        mock_constellation.constellation_id = "test_constellation"
        mock_constellation.name = "Test Constellation"
        mock_constellation.tasks = ["task1", "task2"]
        mock_constellation.dependencies = []
        mock_constellation.state = MagicMock()
        mock_constellation.state.value = "completed"
        mock_galaxy_session._current_constellation = mock_constellation

        result = await client.process_request("Create a test workflow", "test_task")

        # Verify request processing
        assert result["status"] == "completed"
        assert result["request"] == "Create a test workflow"
        assert result["task_name"] == "test_task"
        assert "execution_time" in result
        assert result["constellation"]["name"] == "Test Constellation"
        mock_galaxy_session.run.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_request_failure(
        self, mock_constellation_client, mock_galaxy_session
    ):
        """Test processing request with failure."""
        client = GalaxyClient(session_name="test_session")
        client._client = mock_constellation_client
        client._session = mock_galaxy_session

        # Mock session run to raise an exception
        mock_galaxy_session.run.side_effect = Exception("Test error")

        result = await client.process_request("Failing request")

        # Verify error handling
        assert result["status"] == "failed"
        assert result["error"] == "Test error"
        assert "timestamp" in result

    @pytest.mark.asyncio
    async def test_shutdown(self, mock_constellation_client, mock_galaxy_session):
        """Test Galaxy client shutdown."""
        client = GalaxyClient(session_name="test_session")
        client._client = mock_constellation_client
        client._session = mock_galaxy_session

        await client.shutdown()

        # Verify shutdown calls
        mock_constellation_client.shutdown.assert_called_once()
        mock_galaxy_session.force_finish.assert_called_once_with("Client shutdown")

    @pytest.mark.asyncio
    async def test_interactive_mode_commands(
        self, mock_constellation_client, mock_galaxy_session
    ):
        """Test interactive mode command handling."""
        client = GalaxyClient(session_name="test_session")
        client._client = mock_constellation_client
        client._session = mock_galaxy_session

        # Mock user inputs
        user_inputs = ["help", "status", "quit"]

        with patch.object(client.display, "get_user_input", side_effect=user_inputs):
            await client.interactive_mode()

        # Verify that interactive mode processed commands without errors
        # (This is a basic test - in practice you'd mock more display methods)

    def test_display_integration(self):
        """Test that client properly integrates with ClientDisplay."""
        client = GalaxyClient(session_name="test_session")

        # Verify display manager is initialized
        assert client.display is not None
        assert hasattr(client.display, "show_galaxy_banner")
        assert hasattr(client.display, "display_result")
        assert hasattr(client.display, "show_status")

    @pytest.mark.asyncio
    async def test_galaxy_session_interface_compatibility(
        self, mock_constellation_client
    ):
        """Test that GalaxyClient uses the correct GalaxySession interface."""
        client = GalaxyClient(session_name="test_session")

        with patch(
            "ufo.galaxy.galaxy_client.ConstellationClient",
            return_value=mock_constellation_client,
        ):
            # Mock GalaxySession constructor to verify correct parameters
            with patch("ufo.galaxy.galaxy_client.GalaxySession") as mock_session_class:
                mock_session = MagicMock()
                mock_session_class.return_value = mock_session

                await client.initialize()

                # Verify GalaxySession is called with correct parameters
                mock_session_class.assert_called_once_with(
                    task="test_session",
                    should_evaluate=False,
                    id="test_session",
                    client=mock_constellation_client,
                    initial_request="",
                )

    def test_status_display_integration(self):
        """Test status display functionality."""
        client = GalaxyClient(session_name="test_session")

        # Test status display without session
        client._show_status()

        # Test status display with mock session
        mock_session = MagicMock()
        mock_session._rounds = {"round1": {}}
        client._session = mock_session

        client._show_status()


@pytest.mark.asyncio
class TestGalaxyClientIntegration:
    """Integration tests for GalaxyClient."""

    async def test_full_workflow_simulation(self):
        """Test a complete workflow simulation using mocks."""
        # Create client
        client = GalaxyClient(session_name="integration_test")

        # Mock all external dependencies
        with patch(
            "ufo.galaxy.galaxy_client.ConstellationClient"
        ) as mock_client_class, patch(
            "ufo.galaxy.galaxy_client.GalaxySession"
        ) as mock_session_class:

            # Setup mocks
            mock_client = MagicMock()
            mock_client.initialize = AsyncMock()
            mock_client.shutdown = AsyncMock()
            mock_client.device_manager = MagicMock()
            mock_client_class.return_value = mock_client

            mock_session = MagicMock()
            mock_session.run = AsyncMock()
            mock_session.force_finish = AsyncMock()
            mock_session._rounds = {}
            mock_session.log_path = "test/path"
            mock_session._current_constellation = None
            mock_session_class.return_value = mock_session

            # Initialize client
            await client.initialize()

            # Process request
            result = await client.process_request("Test integration request")

            # Shutdown
            await client.shutdown()

            # Verify workflow
            assert result["status"] == "completed"
            mock_client.initialize.assert_called_once()
            mock_session.run.assert_called_once()
            mock_client.shutdown.assert_called_once()


class TestGalaxyClientMockImplementation:
    """Test mock implementation for testing purposes."""

    def test_mock_creation(self):
        """Test creating a mock GalaxyClient for testing."""
        # Create mock client for use in other tests
        mock_client = MagicMock(spec=GalaxyClient)
        mock_client.session_name = "mock_session"
        mock_client.initialize = AsyncMock()
        mock_client.process_request = AsyncMock(return_value={"status": "completed"})
        mock_client.shutdown = AsyncMock()

        # Verify mock behavior
        assert mock_client.session_name == "mock_session"
        assert asyncio.iscoroutinefunction(mock_client.initialize)
        assert asyncio.iscoroutinefunction(mock_client.process_request)
        assert asyncio.iscoroutinefunction(mock_client.shutdown)


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
