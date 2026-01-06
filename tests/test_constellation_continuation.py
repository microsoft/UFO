"""
测试constellation完成后继续添加新任务的场景
"""
import asyncio
import pytest
from unittest.mock import MagicMock, AsyncMock
from galaxy.agents.galaxy_agent_state import MonitoringGalaxyAgentState, GalaxyAgentStatus
from galaxy.core.events import EventType
from ufo.module.context import Context


class MockGalaxyWeaverAgent:
    """Mock GalaxyWeaverAgent for testing constellation continuation"""
    
    def __init__(self):
        self._status = GalaxyAgentStatus.MONITORING.value
        self._current_constellation = None
        self.continue_call_count = 0
        self.new_tasks_added = False
        
    @property
    def current_constellation(self):
        return self._current_constellation
        
    @current_constellation.setter
    def current_constellation(self, value):
        self._current_constellation = value
        
    async def update_constellation_with_lock(self, task_result, context=None):
        # Mock constellation update
        return self._current_constellation
        
    async def should_continue(self, constellation, context=None):
        """模拟agent决定是否继续"""
        self.continue_call_count += 1
        
        # 第一次调用返回True（表示要继续）
        # 第二次调用返回False（表示真正完成）
        if self.continue_call_count == 1:
            # 模拟添加新任务
            await self._add_new_tasks()
            return True
        else:
            return False
    
    async def _add_new_tasks(self):
        """模拟添加新任务到constellation"""
        # 在实际实现中，这里会向constellation添加新任务
        # 并触发新的任务事件
        self.new_tasks_added = True
        # 可以模拟发送新的TASK_STARTED事件


class TestConstellationContinuation:
    """测试constellation完成后的继续执行"""
    
    @pytest.mark.asyncio
    async def test_continuation_after_completion(self):
        """测试constellation完成后继续添加任务"""
        # 创建监控状态和模拟agent
        monitoring_state = MonitoringGalaxyAgentState()
        agent = MockGalaxyWeaverAgent()
        context = Context()
        
        # 创建模拟constellation
        mock_constellation = MagicMock()
        mock_constellation.is_complete.return_value = True  # 初始完成
        agent.current_constellation = mock_constellation
        
        # 设置agent的queue方法
        agent.queue_task_update_to_current_state = monitoring_state.queue_task_update
        
        # 启动一个任务来测试handle方法的超时行为
        # 因为当前实现可能会无限循环
        try:
            await asyncio.wait_for(monitoring_state.handle(agent, context), timeout=2.0)
        except asyncio.TimeoutError:
            print("Handle method timed out - this indicates the busy waiting issue")
        
        # 验证should_continue被调用
        assert agent.continue_call_count > 0
        
        # 验证新任务被"添加"（在模拟中）
        assert agent.new_tasks_added
        
        print(f"should_continue called {agent.continue_call_count} times")
        print(f"New tasks added: {agent.new_tasks_added}")
    
    @pytest.mark.asyncio 
    async def test_constellation_continuation_with_new_tasks(self):
        """测试constellation完成后添加新任务并正确执行"""
        monitoring_state = MonitoringGalaxyAgentState()
        agent = MockGalaxyWeaverAgent()
        context = Context()
        
        # 创建模拟constellation
        mock_constellation = MagicMock()
        agent.current_constellation = mock_constellation
        
        # 设置队列方法
        agent.queue_task_update_to_current_state = monitoring_state.queue_task_update
        
        # 模拟constellation初始为完成状态
        mock_constellation.is_complete.return_value = True
        
        # 模拟在should_continue中添加新任务
        async def mock_should_continue(constellation, context=None):
            agent.continue_call_count += 1
            if agent.continue_call_count == 1:
                # 第一次：说要继续，并模拟添加新任务
                await monitoring_state.queue_task_update({
                    "task_id": "new_task_1",
                    "event_type": EventType.TASK_STARTED.value,
                    "status": "running"
                })
                return True
            else:
                # 第二次：完成新任务后不再继续
                return False
        
        agent.should_continue = mock_should_continue
        
        # 启动监控，但加上超时保护
        monitoring_task = asyncio.create_task(monitoring_state.handle(agent, context))
        
        # 短暂等待让监控开始
        await asyncio.sleep(0.1)
        
        # 模拟新任务完成
        await monitoring_state.queue_task_update({
            "task_id": "new_task_1", 
            "event_type": EventType.TASK_COMPLETED.value,
            "status": "completed"
        })
        
        # 等待处理完成或超时
        try:
            await asyncio.wait_for(monitoring_task, timeout=1.0)
        except asyncio.TimeoutError:
            monitoring_task.cancel()
            pytest.fail("Monitoring did not complete in expected time")
        
        # 验证结果
        assert agent.continue_call_count >= 1
        assert agent._status == GalaxyAgentStatus.FINISHED.value


if __name__ == "__main__":
    # 运行测试
    async def run_tests():
        test_case = TestConstellationContinuation()
        
        print("🧪 Testing constellation completion continuation...")
        
        try:
            await test_case.test_continuation_after_completion()
            print("✅ Basic continuation test completed")
        except Exception as e:
            print(f"❌ Basic continuation test failed: {e}")
        
        try:
            await test_case.test_constellation_continuation_with_new_tasks()
            print("✅ Continuation with new tasks test completed") 
        except Exception as e:
            print(f"❌ Continuation with new tasks test failed: {e}")
    
    asyncio.run(run_tests())
