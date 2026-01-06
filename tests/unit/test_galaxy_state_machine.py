# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
单元测试：Galaxy状态机系统

测试范围：
1. GalaxyAgentState状态转换逻辑
2. GalaxyAgentStateManager状态管理
3. MonitoringGalaxyAgentState任务跟踪
4. Observer与状态机集成
"""

import pytest
import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any

from galaxy.agents.galaxy_agent_state import (
    GalaxyAgentStatus,
    GalaxyAgentState,
    CreatingGalaxyAgentState,
    MonitoringGalaxyAgentState,
    FinishedGalaxyAgentState,
    FailedGalaxyAgentState,
)
from galaxy.agents.galaxy_agent_state_manager import GalaxyAgentStateManager
from galaxy.core.events import EventType
from ufo.module.context import Context


class MockGalaxyWeaverAgent:
    """Mock GalaxyWeaverAgent for testing"""
    
    def __init__(self):
        self._status = GalaxyAgentStatus.CREATING.value
        self._current_constellation = None
        
    @property
    def current_constellation(self):
        return self._current_constellation
        
    @current_constellation.setter
    def current_constellation(self, value):
        self._current_constellation = value
        
    async def process_initial_request(self, request, context=None):
        # Mock constellation creation
        mock_constellation = MagicMock()
        mock_constellation.task_count = 3
        mock_constellation.is_complete.return_value = False
        self._current_constellation = mock_constellation
        return mock_constellation
        
    async def update_constellation_with_lock(self, task_result, context=None):
        # Mock constellation update
        return self._current_constellation
        
    async def should_continue(self, constellation, context=None):
        # Mock decision logic
        return False  # Default to stop


class TestGalaxyAgentStateManager:
    """测试状态管理器"""
    
    def test_state_manager_initialization(self):
        """测试状态管理器初始化"""
        manager = GalaxyAgentStateManager()
        
        # 检查所有状态都已注册
        creating_state = manager.get_state(GalaxyAgentStatus.CREATING.value)
        monitoring_state = manager.get_state(GalaxyAgentStatus.MONITORING.value)
        finished_state = manager.get_state(GalaxyAgentStatus.FINISHED.value)
        failed_state = manager.get_state(GalaxyAgentStatus.FAILED.value)
        
        assert isinstance(creating_state, CreatingGalaxyAgentState)
        assert isinstance(monitoring_state, MonitoringGalaxyAgentState)
        assert isinstance(finished_state, FinishedGalaxyAgentState)
        assert isinstance(failed_state, FailedGalaxyAgentState)
    
    def test_state_caching(self):
        """测试状态实例缓存"""
        manager = GalaxyAgentStateManager()
        
        # 第一次获取
        state1 = manager.get_state(GalaxyAgentStatus.CREATING.value)
        # 第二次获取应该是同一个实例
        state2 = manager.get_state(GalaxyAgentStatus.CREATING.value)
        
        assert state1 is state2
    
    def test_unknown_status_handling(self):
        """测试未知状态处理"""
        manager = GalaxyAgentStateManager()
        
        # 获取未知状态应该返回默认状态
        unknown_state = manager.get_state("unknown_status")
        assert isinstance(unknown_state, CreatingGalaxyAgentState)


class TestCreatingGalaxyAgentState:
    """测试创建状态"""
    
    @pytest.mark.asyncio
    async def test_successful_constellation_creation(self):
        """测试成功创建constellation"""
        state = CreatingGalaxyAgentState()
        agent = MockGalaxyWeaverAgent()
        context = MagicMock()
        context.get.return_value = "test request"
        
        await state.handle(agent, context)
        
        assert agent._status == GalaxyAgentStatus.MONITORING.value
        assert agent.current_constellation is not None
    
    @pytest.mark.asyncio
    async def test_failed_constellation_creation(self):
        """测试创建constellation失败"""
        state = CreatingGalaxyAgentState()
        agent = MockGalaxyWeaverAgent()
        context = MagicMock()
        context.get.return_value = "test request"
        
        # Mock失败场景
        agent.process_initial_request = AsyncMock(return_value=None)
        
        await state.handle(agent, context)
        
        assert agent._status == GalaxyAgentStatus.FAILED.value
    
    @pytest.mark.asyncio
    async def test_existing_constellation_handling(self):
        """测试已存在constellation的处理"""
        state = CreatingGalaxyAgentState()
        agent = MockGalaxyWeaverAgent()
        
        # 预设constellation
        mock_constellation = MagicMock()
        agent._current_constellation = mock_constellation
        
        await state.handle(agent, None)
        
        assert agent._status == GalaxyAgentStatus.MONITORING.value
    
    def test_state_properties(self):
        """测试状态属性"""
        state = CreatingGalaxyAgentState()
        
        assert state.name() == GalaxyAgentStatus.CREATING.value
        assert not state.is_round_end()
        assert not state.is_subtask_end()


class TestMonitoringGalaxyAgentState:
    """测试监控状态"""
    
    def setup_method(self):
        """每个测试方法的设置"""
        self.state = MonitoringGalaxyAgentState()
        self.agent = MockGalaxyWeaverAgent()
        self.agent._status = GalaxyAgentStatus.MONITORING.value
        
        # 创建mock constellation
        self.mock_constellation = MagicMock()
        self.mock_constellation.is_complete.return_value = False
        self.agent._current_constellation = self.mock_constellation
    
    @pytest.mark.asyncio
    async def test_task_started_tracking(self):
        """测试任务开始跟踪"""
        task_update = {
            "task_id": "task_1",
            "event_type": EventType.TASK_STARTED.value,
            "status": "running",
        }
        
        await self.state.queue_task_update(task_update)
        
        # 处理更新
        await self.state._process_pending_updates(self.agent, None)
        
        # 检查任务被跟踪
        assert "task_1" in self.state._running_tasks
    
    @pytest.mark.asyncio
    async def test_task_completed_tracking(self):
        """测试任务完成跟踪"""
        # 先添加运行中任务
        self.state._running_tasks.add("task_1")
        
        task_update = {
            "task_id": "task_1",
            "event_type": EventType.TASK_COMPLETED.value,
            "status": "completed",
            "result": {"output": "success"}
        }
        
        await self.state.queue_task_update(task_update)
        
        # Mock update_constellation_with_lock
        self.agent.update_constellation_with_lock = AsyncMock()
        
        # 处理更新
        await self.state._process_pending_updates(self.agent, None)
        
        # 检查任务从跟踪中移除
        assert "task_1" not in self.state._running_tasks
        # 检查constellation被更新
        self.agent.update_constellation_with_lock.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_completion_check_with_running_tasks(self):
        """测试有运行中任务时的完成检查"""
        # 设置constellation为完成但有运行中任务
        self.mock_constellation.is_complete.return_value = True
        self.state._running_tasks.add("task_1")
        
        is_complete = await self.state._check_true_completion(self.agent, None)
        
        assert not is_complete  # 不应该完成因为还有运行中任务
    
    @pytest.mark.asyncio
    async def test_completion_check_with_pending_updates(self):
        """测试有待处理更新时的完成检查"""
        # 设置constellation为完成但有待处理更新
        self.mock_constellation.is_complete.return_value = True
        await self.state.queue_task_update({"task_id": "task_1", "status": "completed"})
        
        is_complete = await self.state._check_true_completion(self.agent, None)
        
        assert not is_complete  # 不应该完成因为有待处理更新
    
    @pytest.mark.asyncio
    async def test_true_completion(self):
        """测试真正完成的情况"""
        # 设置完成条件
        self.mock_constellation.is_complete.return_value = True
        self.agent.should_continue = AsyncMock(return_value=False)
        
        is_complete = await self.state._check_true_completion(self.agent, None)
        
        assert is_complete
        self.agent.should_continue.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_agent_wants_to_continue(self):
        """测试agent希望继续的情况"""
        # 设置完成条件但agent希望继续
        self.mock_constellation.is_complete.return_value = True
        self.agent.should_continue = AsyncMock(return_value=True)
        
        is_complete = await self.state._check_true_completion(self.agent, None)
        
        assert not is_complete  # agent希望继续，所以不完成
    
    def test_state_properties(self):
        """测试状态属性"""
        assert self.state.name() == GalaxyAgentStatus.MONITORING.value
        assert not self.state.is_round_end()
        assert not self.state.is_subtask_end()


class TestFinishedAndFailedStates:
    """测试完成和失败状态"""
    
    @pytest.mark.asyncio
    async def test_finished_state(self):
        """测试完成状态"""
        state = FinishedGalaxyAgentState()
        agent = MockGalaxyWeaverAgent()
        
        await state.handle(agent, None)
        
        assert state.name() == GalaxyAgentStatus.FINISHED.value
        assert state.is_round_end()
        assert not state.is_subtask_end()
    
    @pytest.mark.asyncio
    async def test_failed_state(self):
        """测试失败状态"""
        state = FailedGalaxyAgentState()
        agent = MockGalaxyWeaverAgent()
        
        await state.handle(agent, None)
        
        assert state.name() == GalaxyAgentStatus.FAILED.value
        assert state.is_round_end()
        assert not state.is_subtask_end()


class TestStateTransitions:
    """测试状态转换"""
    
    def test_creating_to_monitoring_transition(self):
        """测试从创建到监控的状态转换"""
        agent = MockGalaxyWeaverAgent()
        agent._status = GalaxyAgentStatus.MONITORING.value
        
        creating_state = CreatingGalaxyAgentState()
        next_state = creating_state.next_state(agent)
        
        assert isinstance(next_state, MonitoringGalaxyAgentState)
    
    def test_monitoring_to_finished_transition(self):
        """测试从监控到完成的状态转换"""
        agent = MockGalaxyWeaverAgent()
        agent._status = GalaxyAgentStatus.FINISHED.value
        
        monitoring_state = MonitoringGalaxyAgentState()
        next_state = monitoring_state.next_state(agent)
        
        assert isinstance(next_state, FinishedGalaxyAgentState)
    
    def test_any_to_failed_transition(self):
        """测试转换到失败状态"""
        agent = MockGalaxyWeaverAgent()
        agent._status = GalaxyAgentStatus.FAILED.value
        
        creating_state = CreatingGalaxyAgentState()
        next_state = creating_state.next_state(agent)
        
        assert isinstance(next_state, FailedGalaxyAgentState)


class TestTaskUpdateQueueing:
    """测试任务更新队列"""
    
    @pytest.mark.asyncio
    async def test_queue_multiple_updates(self):
        """测试队列多个更新"""
        state = MonitoringGalaxyAgentState()
        
        updates = [
            {"task_id": "task_1", "event_type": EventType.TASK_STARTED.value},
            {"task_id": "task_2", "event_type": EventType.TASK_STARTED.value},
            {"task_id": "task_1", "event_type": EventType.TASK_COMPLETED.value},
        ]
        
        for update in updates:
            await state.queue_task_update(update)
        
        # 队列应该有3个更新
        assert state._pending_task_updates.qsize() == 3
    
    @pytest.mark.asyncio
    async def test_process_updates_in_order(self):
        """测试按顺序处理更新"""
        state = MonitoringGalaxyAgentState()
        agent = MockGalaxyWeaverAgent()
        agent.update_constellation_with_lock = AsyncMock()
        
        # 添加一系列更新
        await state.queue_task_update({
            "task_id": "task_1", 
            "event_type": EventType.TASK_STARTED.value
        })
        await state.queue_task_update({
            "task_id": "task_1", 
            "event_type": EventType.TASK_COMPLETED.value
        })
        
        # 处理更新
        await state._process_pending_updates(agent, None)
        
        # 检查处理结果
        assert "task_1" not in state._running_tasks  # 任务应该被移除
        agent.update_constellation_with_lock.assert_called_once()  # 只有完成事件触发更新
    
    @pytest.mark.asyncio
    async def test_queue_update_on_non_monitoring_state(self):
        """测试在非监控状态队列更新"""
        state = CreatingGalaxyAgentState()
        
        # 创建状态不支持队列更新，应该警告但不抛异常
        await state.queue_task_update({"task_id": "task_1"})
        
        # 应该没有队列
        assert not hasattr(state, '_pending_task_updates') or state._pending_task_updates.empty()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
