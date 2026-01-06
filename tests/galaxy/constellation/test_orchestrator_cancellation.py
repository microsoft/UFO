#!/usr/bin/env python3
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Unit tests for TaskConstellationOrchestrator cancellation mechanism.

Tests the cancel_execution method and execution loop interruption.
"""

import asyncio
import pytest
import pytest_asyncio
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

# Add project root to path
UFO_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(UFO_ROOT))

from galaxy.constellation.orchestrator.orchestrator import TaskConstellationOrchestrator
from galaxy.constellation import TaskConstellation, TaskStar
from galaxy.constellation.enums import TaskStatus, ConstellationState, TaskPriority


@pytest_asyncio.fixture
def mock_orchestrator():
    """Create a mock TaskConstellationOrchestrator for testing."""
    mock_device_manager = MagicMock()
    orchestrator = TaskConstellationOrchestrator(
        device_manager=mock_device_manager, enable_logging=True
    )
    yield orchestrator


@pytest_asyncio.fixture
def simple_constellation():
    """Create a simple constellation for testing."""
    constellation = TaskConstellation(
        constellation_id="test_constellation", name="Test Constellation"
    )

    task1 = TaskStar(
        task_id="task_1", description="Task 1", priority=TaskPriority.MEDIUM
    )
    task2 = TaskStar(
        task_id="task_2", description="Task 2", priority=TaskPriority.MEDIUM
    )

    constellation.add_task(task1)
    constellation.add_task(task2)

    return constellation


@pytest.mark.asyncio
async def test_cancel_execution_sets_flags(mock_orchestrator):
    """Test that cancel_execution sets cancellation flags."""
    # Arrange
    constellation_id = "test_constellation_123"

    # Act
    result = await mock_orchestrator.cancel_execution(constellation_id)

    # Assert
    assert result is True
    assert mock_orchestrator._cancellation_requested is True
    assert mock_orchestrator._cancelled_constellations[constellation_id] is True


@pytest.mark.asyncio
async def test_cancel_execution_cancels_running_tasks(mock_orchestrator):
    """Test that cancel_execution cancels all running tasks."""
    # Arrange
    mock_task1 = AsyncMock()
    mock_task1.done.return_value = False
    mock_task1.cancel = MagicMock()

    mock_task2 = AsyncMock()
    mock_task2.done.return_value = False
    mock_task2.cancel = MagicMock()

    mock_orchestrator._execution_tasks = {"task_1": mock_task1, "task_2": mock_task2}

    # Act
    await mock_orchestrator.cancel_execution("test_constellation")

    # Assert
    mock_task1.cancel.assert_called_once()
    mock_task2.cancel.assert_called_once()
    assert len(mock_orchestrator._execution_tasks) == 0  # 应该被清空


@pytest.mark.asyncio
async def test_cancel_execution_skips_completed_tasks(mock_orchestrator):
    """Test that cancel_execution skips already completed tasks."""
    # Arrange
    mock_task_done = AsyncMock()
    mock_task_done.done.return_value = True  # 已完成
    mock_task_done.cancel = MagicMock()

    mock_task_running = AsyncMock()
    mock_task_running.done.return_value = False  # 运行中
    mock_task_running.cancel = MagicMock()

    mock_orchestrator._execution_tasks = {
        "task_done": mock_task_done,
        "task_running": mock_task_running,
    }

    # Act
    await mock_orchestrator.cancel_execution("test_constellation")

    # Assert
    mock_task_done.cancel.assert_not_called()  # 不应该取消已完成的任务
    mock_task_running.cancel.assert_called_once()  # 应该取消运行中的任务


@pytest.mark.asyncio
async def test_execution_loop_checks_cancellation_flag(
    mock_orchestrator, simple_constellation
):
    """Test that _run_execution_loop checks cancellation flag."""
    # Arrange
    mock_orchestrator._cancellation_requested = False
    mock_orchestrator._cancelled_constellations[
        simple_constellation.constellation_id
    ] = False

    # Mock methods to track calls
    mock_orchestrator._sync_constellation_modifications = AsyncMock(
        return_value=simple_constellation
    )
    mock_orchestrator._validate_existing_device_assignments = MagicMock()
    mock_orchestrator._schedule_ready_tasks = AsyncMock()
    mock_orchestrator._wait_for_task_completion = AsyncMock()

    # Setup: 在第二次迭代时设置取消标志
    call_count = 0

    async def mock_wait():
        nonlocal call_count
        call_count += 1
        if call_count == 2:
            mock_orchestrator._cancellation_requested = True
        await asyncio.sleep(0.01)

    mock_orchestrator._wait_for_task_completion = mock_wait

    # Act
    await mock_orchestrator._run_execution_loop(simple_constellation)

    # Assert
    assert call_count >= 2  # 应该至少执行了2次迭代
    assert simple_constellation.state == ConstellationState.CANCELLED


@pytest.mark.asyncio
async def test_execution_loop_stops_immediately_on_cancellation(
    mock_orchestrator, simple_constellation
):
    """Test that execution loop stops immediately when cancellation is pre-set."""
    # Arrange
    mock_orchestrator._cancellation_requested = True  # 预先设置取消标志

    # Mock methods
    mock_orchestrator._sync_constellation_modifications = AsyncMock(
        return_value=simple_constellation
    )
    mock_orchestrator._schedule_ready_tasks = AsyncMock()

    # Act
    await mock_orchestrator._run_execution_loop(simple_constellation)

    # Assert
    # schedule_ready_tasks 不应该被调用
    mock_orchestrator._schedule_ready_tasks.assert_not_called()
    assert simple_constellation.state == ConstellationState.CANCELLED


@pytest.mark.asyncio
async def test_execution_loop_checks_constellation_specific_cancellation(
    mock_orchestrator, simple_constellation
):
    """Test that execution loop checks constellation-specific cancellation flag."""
    # Arrange
    mock_orchestrator._cancellation_requested = False  # 全局标志未设置
    mock_orchestrator._cancelled_constellations[
        simple_constellation.constellation_id
    ] = True  # 但特定constellation被取消

    mock_orchestrator._sync_constellation_modifications = AsyncMock(
        return_value=simple_constellation
    )
    mock_orchestrator._schedule_ready_tasks = AsyncMock()

    # Act
    await mock_orchestrator._run_execution_loop(simple_constellation)

    # Assert
    mock_orchestrator._schedule_ready_tasks.assert_not_called()
    assert simple_constellation.state == ConstellationState.CANCELLED


@pytest.mark.asyncio
async def test_cancel_execution_with_no_tasks(mock_orchestrator):
    """Test cancel_execution when no tasks are running."""
    # Arrange
    mock_orchestrator._execution_tasks = {}

    # Act
    result = await mock_orchestrator.cancel_execution("test_constellation")

    # Assert
    assert result is True
    assert mock_orchestrator._cancellation_requested is True


@pytest.mark.asyncio
async def test_cancel_execution_waits_for_task_cancellation(mock_orchestrator):
    """Test that cancel_execution waits for tasks to be cancelled."""
    # Arrange
    cancellation_completed = False

    async def mock_task_cancellation():
        await asyncio.sleep(0.1)
        nonlocal cancellation_completed
        cancellation_completed = True
        raise asyncio.CancelledError()

    mock_task = asyncio.create_task(mock_task_cancellation())
    mock_orchestrator._execution_tasks = {"task_1": mock_task}

    # Act
    await mock_orchestrator.cancel_execution("test_constellation")

    # Assert
    assert cancellation_completed is True
    assert len(mock_orchestrator._execution_tasks) == 0


@pytest.mark.asyncio
async def test_multiple_cancel_execution_calls_are_idempotent(mock_orchestrator):
    """Test that multiple cancel_execution calls are handled gracefully."""
    # Arrange
    mock_task = AsyncMock()
    mock_task.done.return_value = False
    mock_task.cancel = MagicMock()

    mock_orchestrator._execution_tasks = {"task_1": mock_task}

    # Act - 调用两次
    await mock_orchestrator.cancel_execution("test_constellation")
    await mock_orchestrator.cancel_execution("test_constellation")

    # Assert
    # 第二次调用时任务列表已清空，不应该有问题
    assert len(mock_orchestrator._execution_tasks) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
