# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
集成测试：Galaxy状态机与观察者系统

测试范围：
1. GalaxyRound与状态机集成
2. Observer与状态机的事件流
3. 完整的任务执行生命周期
4. 竞态条件解决验证
"""

import pytest
import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any, List

from galaxy.session.galaxy_session import GalaxyRound, GalaxySession
from galaxy.agents.galaxy_agent import MockGalaxyWeaverAgent
from galaxy.session.observers import ConstellationProgressObserver
from galaxy.constellation import TaskConstellation, TaskStar, create_simple_constellation
from galaxy.core.events import EventType, TaskEvent, get_event_bus
from galaxy.client.constellation_client import ConstellationClient
from galaxy.constellation.orchestrator import TaskConstellationOrchestrator
from ufo.module.context import Context


class IntegrationTestHelper:
    """集成测试助手类"""
    
    @staticmethod
    def create_test_constellation() -> TaskConstellation:
        """创建测试用constellation"""
        return create_simple_constellation(
            task_descriptions=["Task 1", "Task 2", "Task 3"],
            constellation_name="test_constellation",
            sequential=True
        )
    
    @staticmethod
    def create_mock_client() -> ConstellationClient:
        """创建mock客户端"""
        client = MagicMock(spec=ConstellationClient)
        client.device_manager = MagicMock()
        return client
    
    @staticmethod
    def create_mock_orchestrator() -> TaskConstellationOrchestrator:
        """创建mock编排器"""
        orchestrator = MagicMock(spec=TaskConstellationOrchestrator)
        orchestrator.assign_devices_automatically = AsyncMock()
        orchestrator.orchestrate_constellation = AsyncMock()
        return orchestrator


class TestGalaxyRoundStateMachineIntegration:
    """测试GalaxyRound与状态机集成"""
    
    def setup_method(self):
        """测试设置"""
        self.agent = MockGalaxyWeaverAgent()
        self.context = Context()
        self.orchestrator = IntegrationTestHelper.create_mock_orchestrator()
        
        # 创建测试constellation
        self.test_constellation = IntegrationTestHelper.create_test_constellation()
        self.agent.process_initial_request = AsyncMock(return_value=self.test_constellation)
    
    @pytest.mark.asyncio
    async def test_round_state_machine_execution(self):
        """测试round状态机执行"""
        # 创建round
        round_instance = GalaxyRound(
            request="test request",
            agent=self.agent,
            context=self.context,
            should_evaluate=False,
            id=1,
            orchestratior=self.orchestrator
        )
        
        # Mock状态机执行
        with patch.object(round_instance, 'is_finished') as mock_finished:
            # 模拟状态机循环：先运行，然后结束
            mock_finished.side_effect = [False, False, True]
            
            # 运行round
            await round_instance.run()
            
            # 验证orchestrator被调用
            self.orchestrator.assign_devices_automatically.assert_called_once()
            self.orchestrator.orchestrate_constellation.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_round_state_transitions(self):
        """测试round状态转换"""
        round_instance = GalaxyRound(
            request="test request",
            agent=self.agent,
            context=self.context,
            should_evaluate=False,
            id=1,
            orchestratior=self.orchestrator
        )
        
        # 检查初始状态
        assert round_instance.agent._status == "creating"
        
        # 模拟状态机执行一步
        await round_instance.agent.handle(round_instance._context)
        
        # 检查状态转换
        assert round_instance.agent._status == "monitoring"
        assert round_instance.agent.current_constellation is not None
    
    @pytest.mark.asyncio
    async def test_round_handles_agent_failure(self):
        """测试round处理agent失败"""
        # Mock失败场景
        self.agent.process_initial_request = AsyncMock(side_effect=Exception("Test failure"))
        
        round_instance = GalaxyRound(
            request="test request",
            agent=self.agent,
            context=self.context,
            should_evaluate=False,
            id=1,
            orchestratior=self.orchestrator
        )
        
        # 模拟状态机执行
        await round_instance.agent.handle(round_instance._context)
        
        # 检查失败状态
        assert round_instance.agent._status == "failed"


class TestObserverStateMachineIntegration:
    """测试Observer与状态机集成"""
    
    def setup_method(self):
        """测试设置"""
        self.agent = MockGalaxyWeaverAgent()
        self.context = Context()
        self.event_bus = get_event_bus()
        
        # 创建observer
        self.observer = ConstellationProgressObserver(
            agent=self.agent,
            context=self.context
        )
        
        # 订阅事件
        self.event_bus.subscribe(self.observer)
        
        # 创建测试constellation
        self.test_constellation = IntegrationTestHelper.create_test_constellation()
        self.agent._current_constellation = self.test_constellation
        self.agent._status = "monitoring"
    
    @pytest.mark.asyncio
    async def test_task_event_forwarding_to_state_machine(self):
        """测试任务事件转发到状态机"""
        # Mock状态机的队列方法
        self.agent.queue_task_update_to_current_state = AsyncMock()
        
        # 创建任务事件
        task_event = TaskEvent(
            event_type=EventType.TASK_STARTED,
            source_id="test_source",
            timestamp=time.time(),
            data={},
            task_id="task_1",
            status="running"
        )
        
        # 发布事件
        await self.event_bus.publish_event(task_event)
        
        # 等待事件处理
        await asyncio.sleep(0.1)
        
        # 验证事件被转发到状态机
        self.agent.queue_task_update_to_current_state.assert_called_once()
        call_args = self.agent.queue_task_update_to_current_state.call_args[0][0]
        assert call_args["task_id"] == "task_1"
        assert call_args["event_type"] == EventType.TASK_STARTED.value
    
    @pytest.mark.asyncio
    async def test_task_lifecycle_event_sequence(self):
        """测试任务生命周期事件序列"""
        # Mock状态机方法
        self.agent.queue_task_update_to_current_state = AsyncMock()
        
        # 创建任务生命周期事件序列
        events = [
            TaskEvent(
                event_type=EventType.TASK_STARTED,
                source_id="test_source",
                timestamp=time.time(),
                data={},
                task_id="task_1",
                status="running"
            ),
            TaskEvent(
                event_type=EventType.TASK_COMPLETED,
                source_id="test_source",
                timestamp=time.time() + 1,
                data={},
                task_id="task_1",
                status="completed",
                result={"output": "success"}
            )
        ]
        
        # 发布事件序列
        for event in events:
            await self.event_bus.publish_event(event)
            await asyncio.sleep(0.05)  # 短暂延迟确保顺序
        
        # 等待事件处理完成
        await asyncio.sleep(0.1)
        
        # 验证所有事件都被转发
        assert self.agent.queue_task_update_to_current_state.call_count == 2
    
    @pytest.mark.asyncio
    async def test_observer_error_handling(self):
        """测试observer错误处理"""
        # Mock状态机方法抛异常
        self.agent.queue_task_update_to_current_state = AsyncMock(
            side_effect=Exception("State machine error")
        )
        
        # 创建任务事件
        task_event = TaskEvent(
            event_type=EventType.TASK_STARTED,
            source_id="test_source",
            timestamp=time.time(),
            data={},
            task_id="task_1",
            status="running"
        )
        
        # 发布事件（应该不抛异常）
        await self.event_bus.publish_event(task_event)
        await asyncio.sleep(0.1)
        
        # 验证observer处理了错误但继续运行
        self.agent.queue_task_update_to_current_state.assert_called_once()


class TestEndToEndExecution:
    """端到端执行测试"""
    
    def setup_method(self):
        """测试设置"""
        self.agent = MockGalaxyWeaverAgent()
        self.client = IntegrationTestHelper.create_mock_client()
        self.event_bus = get_event_bus()
        
        # 创建session
        self.session = GalaxySession(
            task="test_task",
            should_evaluate=False,
            id="test_session",
            agent=self.agent,
            client=self.client
        )
    
    @pytest.mark.asyncio
    async def test_complete_execution_flow(self):
        """测试完整执行流程"""
        # 设置constellation
        test_constellation = IntegrationTestHelper.create_test_constellation()
        self.agent.process_initial_request = AsyncMock(return_value=test_constellation)
        
        # Mock orchestrator
        with patch.object(self.session._orchestrator, 'assign_devices_automatically') as mock_assign, \
             patch.object(self.session._orchestrator, 'orchestrate_constellation') as mock_orchestrate:
            
            mock_assign.return_value = asyncio.coroutine(lambda: None)()
            mock_orchestrate.return_value = asyncio.coroutine(lambda: None)()
            
            # 运行session
            await self.session.run()
            
            # 验证流程执行
            assert self.agent.current_constellation is not None
            mock_assign.assert_called_once()
            mock_orchestrate.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_race_condition_resolution(self):
        """测试竞态条件解决"""
        # 这个测试验证状态机是否正确处理异步任务完成
        
        # 创建真实的监控状态
        from galaxy.agents.galaxy_agent_state import MonitoringGalaxyAgentState
        
        monitoring_state = MonitoringGalaxyAgentState()
        self.agent._state = monitoring_state
        self.agent._status = "monitoring"
        
        # 设置constellation
        test_constellation = IntegrationTestHelper.create_test_constellation()
        test_constellation.is_complete = MagicMock(return_value=False)
        self.agent._current_constellation = test_constellation
        
        # 模拟任务事件序列（可能的竞态条件场景）
        task_events = [
            {"task_id": "task_1", "event_type": EventType.TASK_STARTED.value, "status": "running"},
            {"task_id": "task_2", "event_type": EventType.TASK_STARTED.value, "status": "running"},
            {"task_id": "task_1", "event_type": EventType.TASK_COMPLETED.value, "status": "completed"},
            {"task_id": "task_2", "event_type": EventType.TASK_COMPLETED.value, "status": "completed"},
        ]
        
        # 快速添加所有事件到队列
        for event in task_events:
            await monitoring_state.queue_task_update(event)
        
        # 模拟constellation在最后一个任务完成后变为完成状态
        def mock_is_complete():
            return monitoring_state._pending_task_updates.empty() and len(monitoring_state._running_tasks) == 0
        
        test_constellation.is_complete.side_effect = mock_is_complete
        self.agent.should_continue = AsyncMock(return_value=False)
        self.agent.update_constellation_with_lock = AsyncMock()
        
        # 处理所有更新
        await monitoring_state._process_pending_updates(self.agent, None)
        
        # 验证状态机正确处理了所有事件
        assert len(monitoring_state._running_tasks) == 0  # 所有任务都被正确跟踪和移除
        assert monitoring_state._pending_task_updates.empty()  # 所有更新都被处理
        
        # 检查完成状态
        is_complete = await monitoring_state._check_true_completion(self.agent, None)
        assert is_complete  # 应该正确识别为完成
    
    @pytest.mark.asyncio
    async def test_concurrent_task_updates(self):
        """测试并发任务更新"""
        from galaxy.agents.galaxy_agent_state import MonitoringGalaxyAgentState
        
        monitoring_state = MonitoringGalaxyAgentState()
        self.agent._state = monitoring_state
        self.agent.update_constellation_with_lock = AsyncMock()
        
        # 创建多个并发任务更新
        async def add_task_updates():
            for i in range(10):
                await monitoring_state.queue_task_update({
                    "task_id": f"task_{i}",
                    "event_type": EventType.TASK_STARTED.value,
                    "status": "running"
                })
                await asyncio.sleep(0.001)  # 微小延迟
        
        async def process_updates():
            await asyncio.sleep(0.05)  # 让一些更新先积累
            await monitoring_state._process_pending_updates(self.agent, None)
        
        # 并发执行
        await asyncio.gather(add_task_updates(), process_updates())
        
        # 验证所有任务都被正确跟踪
        assert len(monitoring_state._running_tasks) == 10


class TestErrorScenarios:
    """错误场景测试"""
    
    @pytest.mark.asyncio
    async def test_constellation_creation_failure_handling(self):
        """测试constellation创建失败处理"""
        agent = MockGalaxyWeaverAgent()
        agent.process_initial_request = AsyncMock(side_effect=Exception("Creation failed"))
        
        from galaxy.agents.galaxy_agent_state import CreatingGalaxyAgentState
        
        creating_state = CreatingGalaxyAgentState()
        context = Context()
        from ufo.module.context import ContextNames
        context.set(ContextNames.REQUEST, "test request")
        
        # 执行状态处理
        await creating_state.handle(agent, context)
        
        # 验证失败处理
        assert agent._status == "failed"
    
    @pytest.mark.asyncio
    async def test_monitoring_state_with_no_constellation(self):
        """测试监控状态但没有constellation"""
        agent = MockGalaxyWeaverAgent()
        agent._current_constellation = None
        
        from galaxy.agents.galaxy_agent_state import MonitoringGalaxyAgentState
        
        monitoring_state = MonitoringGalaxyAgentState()
        
        # 执行状态处理
        await monitoring_state.handle(agent, None)
        
        # 验证失败处理
        assert agent._status == "failed"
    
    @pytest.mark.asyncio
    async def test_invalid_task_update_handling(self):
        """测试无效任务更新处理"""
        from galaxy.agents.galaxy_agent_state import MonitoringGalaxyAgentState
        
        monitoring_state = MonitoringGalaxyAgentState()
        agent = MockGalaxyWeaverAgent()
        agent.update_constellation_with_lock = AsyncMock(side_effect=Exception("Update failed"))
        
        # 添加无效更新
        await monitoring_state.queue_task_update({
            "task_id": "invalid_task",
            "event_type": EventType.TASK_COMPLETED.value,
            "status": "completed"
        })
        
        # 处理更新（应该不抛异常）
        await monitoring_state._process_pending_updates(agent, None)
        
        # 验证错误被处理，系统继续运行
        assert monitoring_state._pending_task_updates.empty()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
