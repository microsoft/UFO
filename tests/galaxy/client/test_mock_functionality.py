#!/usr/bin/env python3
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Test mock functionality and visualization for GalaxyClient.

This module tests:
1. Mock constellation agent integration
2. Visualization display functions
3. Mock constellation creation
4. TaskStarLine dependency handling
"""

import pytest


def test_create_simple_test_constellation():
    """Test creating a simple test constellation with dependencies."""
    from tests.galaxy.mocks import create_simple_test_constellation

    # Test sequential constellation
    tasks = ["Task 1", "Task 2", "Task 3"]
    constellation = create_simple_test_constellation(
        task_descriptions=tasks, constellation_name="TestConstellation", sequential=True
    )

    assert constellation is not None
    assert constellation.task_count == 3
    assert (
        constellation.dependency_count == 2
    )  # Two dependencies for 3 sequential tasks


@pytest.mark.asyncio
async def test_mock_constellation_agent_creation():
    """Test MockConstellationAgent constellation creation."""
    from tests.galaxy.mocks import (
        MockConstellationAgent,
        MockTaskConstellationOrchestrator,
    )
    from ufo.module.context import Context, ContextNames

    # Create mock orchestrator
    mock_orchestrator = MockTaskConstellationOrchestrator(enable_logging=False)

    # Create mock agent
    mock_agent = MockConstellationAgent(
        orchestrator=mock_orchestrator, name="test_mock_constellation"
    )

    # Create mock context
    context = Context()
    context.set(ContextNames.REQUEST, "Create a simple test workflow")

    # Test constellation creation
    constellation = await mock_agent.process_creation(context)

    assert constellation is not None
    assert constellation.name is not None
    assert constellation.task_count > 0
    print(f"Created constellation with {constellation.task_count} tasks")


def test_visualization_display():
    """Test basic visualization display functionality."""
    from galaxy.visualization.client_display import ClientDisplay
    from rich.console import Console

    console = Console()
    display = ClientDisplay(console)

    # Test basic display functions without errors
    display.show_galaxy_banner()
    display.print_success("Test success message")
    display.print_info("Test info message")

    # Test result display
    mock_result = {
        "status": "completed",
        "execution_time": 5.5,
        "constellation": {
            "name": "Test Constellation",
            "task_count": 3,
            "state": "completed",
        },
    }
    display.display_result(mock_result)

    print("✅ All visualization tests passed")
