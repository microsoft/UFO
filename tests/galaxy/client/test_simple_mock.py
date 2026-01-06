#!/usr/bin/env python3
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Simple test for mock client functionality and visualization for GalaxyClient.
"""


def test_simple():
    """Simple test to verify pytest is working."""
    assert True


def test_import_client_display():
    """Test importing ClientDisplay."""
    from galaxy.visualization.client_display import ClientDisplay
    from rich.console import Console

    console = Console()
    display = ClientDisplay(console)
    assert display is not None


def test_import_mock_agent():
    """Test importing MockConstellationAgent."""
    from tests.galaxy.mocks import (
        MockConstellationAgent,
        MockTaskConstellationOrchestrator,
    )

    mock_orchestrator = MockTaskConstellationOrchestrator()
    mock_agent = MockConstellationAgent(
        orchestrator=mock_orchestrator, name="test_mock"
    )
    assert mock_agent is not None
