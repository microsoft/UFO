"""
测试改进的constellation continuation机制
"""
import asyncio
import pytest
from unittest.mock import MagicMock, AsyncMock
from ufo.galaxy.agents.galaxy_agent_state import MonitoringGalaxyAgentState, GalaxyAgentStatus
from ufo.galaxy.core.events import EventType
from ufo.module.context import Context


class EnhancedMockGalaxyWeaverAgent:
    """Enhanced Mock GalaxyWeaverAgent for testing continuation with handle_continuation"""
    
    def __init__(self):
        self._status = GalaxyAgentStatus.MONITORING.value
        self._current_constellation = None
        self.continue_call_count = 0
        self.continuation_call_count = 0
        self.new_tasks_added = False
        self.task_updates_sent = []
        
    @property
    def current_constellation(self):
        return self._current_constellation
        
    @current_constellation.setter 
    def current_constellation(self, value):
        self._current_constellation = value
        
    async def update_constellation_with_lock(self, task_result, context=None):
        return self._current_constellation
        
    async def should_continue(self, constellation, context=None):
        """模拟agent决定是否继续"""
        self.continue_call_count += 1
        
        # 第一次调用返回True（表示要继续）
        if self.continue_call_count == 1:
            return True
        else:
            return False
    
    async def handle_continuation(self, context=None):
        """处理continuation - 这里是agent添加新任务的地方"""
        self.continuation_call_count += 1
        self.new_tasks_added = True
        
        # 模拟添加新任务事件到状态机
        if hasattr(self, 'queue_task_update_to_current_state'):
            task_update = {
                "task_id": f"continuation_task_{self.continuation_call_count}",
                "event_type": EventType.TASK_STARTED.value,
                "status": "running"
            }
            await self.queue_task_update_to_current_state(task_update)
            self.task_updates_sent.append(task_update)


class TestEnhancedConstellationContinuation:
    """测试增强的constellation continuation机制"""
    
    @pytest.mark.asyncio
    async def test_continuation_with_handle_continuation(self):
        """测试使用handle_continuation的完整continuation流程"""
        monitoring_state = MonitoringGalaxyAgentState()
        agent = EnhancedMockGalaxyWeaverAgent()
        context = Context()
        
        # 设置mock constellation
        mock_constellation = MagicMock()
        mock_constellation.is_complete.return_value = True
        agent.current_constellation = mock_constellation
        
        # 设置队列方法
        agent.queue_task_update_to_current_state = monitoring_state.queue_task_update
        
        # 启动监控任务，加上超时保护
        try:
            await asyncio.wait_for(
                monitoring_state.handle(agent, context), 
                timeout=10.0  # 10秒超时
            )
        except asyncio.TimeoutError:
            print("⚠️ Test timed out - this indicates either infinite loop or very slow processing")
            # 即使超时，我们也检查是否有一些预期的调用发生了
        
        # 验证continuation被调用
        print(f"should_continue calls: {agent.continue_call_count}")
        print(f"handle_continuation calls: {agent.continuation_call_count}")
        print(f"Task updates sent: {len(agent.task_updates_sent)}")
        print(f"Final agent status: {agent._status}")
        
        # 基本验证
        assert agent.continue_call_count > 0, "should_continue should be called"
        
        # 如果系统设计正确，continuation应该被调用
        if agent.continue_call_count > 0:
            assert agent.continuation_call_count > 0, "handle_continuation should be called when agent wants to continue"
        
        # 如果agent添加了任务，应该在task_updates_sent中体现
        if agent.new_tasks_added:
            assert len(agent.task_updates_sent) > 0, "New tasks should be queued during continuation"
    
    @pytest.mark.asyncio
    async def test_multiple_continuation_cycles(self):
        """测试多轮continuation"""
        monitoring_state = MonitoringGalaxyAgentState()
        agent = EnhancedMockGalaxyWeaverAgent()
        context = Context()
        
        # 设置mock constellation
        mock_constellation = MagicMock()
        mock_constellation.is_complete.return_value = True
        agent.current_constellation = mock_constellation
        
        # 修改should_continue为支持多轮
        original_should_continue = agent.should_continue
        async def multi_round_should_continue(constellation, context=None):
            result = await original_should_continue(constellation, context)
            # 前两次返回True，第三次返回False
            return agent.continue_call_count <= 2
        
        agent.should_continue = multi_round_should_continue
        agent.queue_task_update_to_current_state = monitoring_state.queue_task_update
        
        # 启动监控（限时）
        async def run_with_timeout():
            try:
                await asyncio.wait_for(monitoring_state.handle(agent, context), timeout=3.0)
            except asyncio.TimeoutError:
                print("Monitoring timed out - this may be expected in multi-round scenarios")
        
        await run_with_timeout()
        
        # 验证多轮continuation
        print(f"Total continuation calls: {agent.continuation_call_count}")
        print(f"Total should_continue calls: {agent.continue_call_count}")
        
        assert agent.continuation_call_count > 1, "Multiple continuation rounds should occur"


if __name__ == "__main__":
    async def run_tests():
        test_case = TestEnhancedConstellationContinuation()
        
        print("🧪 Testing enhanced constellation continuation...")
        
        try:
            await test_case.test_continuation_with_handle_continuation()
            print("✅ Enhanced continuation test completed")
        except Exception as e:
            print(f"❌ Enhanced continuation test failed: {e}")
            import traceback
            traceback.print_exc()
        
        try:
            await test_case.test_multiple_continuation_cycles()
            print("✅ Multiple continuation cycles test completed")
        except Exception as e:
            print(f"❌ Multiple continuation cycles test failed: {e}")
            import traceback
            traceback.print_exc()
    
    asyncio.run(run_tests())
