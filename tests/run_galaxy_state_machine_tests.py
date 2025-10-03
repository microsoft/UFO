# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Galaxy状态机系统测试运行器

此脚本运行所有相关测试并生成报告，验证重构的正确性
"""

import asyncio
import logging
import sys
import time
from pathlib import Path
from typing import Dict, Any, List

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from ufo.galaxy.agents.galaxy_agent import MockGalaxyWeaverAgent
from ufo.galaxy.agents.galaxy_agent_state import (
    GalaxyAgentStatus,
    CreatingGalaxyAgentState,
    MonitoringGalaxyAgentState,
    FinishedGalaxyAgentState,
    FailedGalaxyAgentState
)
from ufo.galaxy.agents.galaxy_agent_state_manager import GalaxyAgentStateManager
from ufo.galaxy.session.observers import ConstellationProgressObserver
from ufo.galaxy.core.events import EventType, TaskEvent, get_event_bus
from ufo.galaxy.constellation import create_simple_constellation
from ufo.module.context import Context


class GalaxyStateMachineTestRunner:
    """Galaxy状态机测试运行器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.results: Dict[str, Any] = {
            "tests_run": 0,
            "tests_passed": 0,
            "tests_failed": 0,
            "failures": [],
            "execution_time": 0
        }
    
    def setup_logging(self):
        """设置日志"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """运行所有测试"""
        self.setup_logging()
        start_time = time.time()
        
        print("🚀 开始运行Galaxy状态机系统测试...")
        print("=" * 60)
        
        # 基础功能测试
        await self.test_state_manager()
        await self.test_state_transitions()
        await self.test_monitoring_state_task_tracking()
        await self.test_observer_integration()
        
        # 集成测试
        await self.test_complete_workflow()
        await self.test_race_condition_resolution()
        await self.test_error_handling()
        
        # 性能测试
        await self.test_concurrent_operations()
        
        self.results["execution_time"] = time.time() - start_time
        
        # 生成报告
        self.generate_report()
        
        return self.results
    
    async def test_state_manager(self):
        """测试状态管理器"""
        print("📋 测试状态管理器...")
        
        try:
            manager = GalaxyAgentStateManager()
            
            # 测试状态获取
            creating_state = manager.get_state(GalaxyAgentStatus.CREATING.value)
            monitoring_state = manager.get_state(GalaxyAgentStatus.MONITORING.value)
            finished_state = manager.get_state(GalaxyAgentStatus.FINISHED.value)
            failed_state = manager.get_state(GalaxyAgentStatus.FAILED.value)
            
            # 验证状态类型
            assert isinstance(creating_state, CreatingGalaxyAgentState)
            assert isinstance(monitoring_state, MonitoringGalaxyAgentState)
            assert isinstance(finished_state, FinishedGalaxyAgentState)
            assert isinstance(failed_state, FailedGalaxyAgentState)
            
            # 测试状态缓存
            same_state = manager.get_state(GalaxyAgentStatus.CREATING.value)
            assert creating_state is same_state
            
            self._record_success("状态管理器基础功能")
            
        except Exception as e:
            self._record_failure("状态管理器基础功能", e)
    
    async def test_state_transitions(self):
        """测试状态转换"""
        print("🔄 测试状态转换...")
        
        try:
            agent = MockGalaxyWeaverAgent()
            context = Context()
            from ufo.module.context import ContextNames
            context.set(ContextNames.REQUEST, "test request")
            
            # 测试创建状态
            creating_state = CreatingGalaxyAgentState()
            await creating_state.handle(agent, context)
            
            assert agent._status == GalaxyAgentStatus.MONITORING.value
            assert agent.current_constellation is not None
            
            # 测试状态转换
            next_state = creating_state.next_state(agent)
            assert isinstance(next_state, MonitoringGalaxyAgentState)
            
            self._record_success("状态转换逻辑")
            
        except Exception as e:
            self._record_failure("状态转换逻辑", e)
    
    async def test_monitoring_state_task_tracking(self):
        """测试监控状态任务跟踪"""
        print("📊 测试监控状态任务跟踪...")
        
        try:
            monitoring_state = MonitoringGalaxyAgentState()
            agent = MockGalaxyWeaverAgent()
            
            # 创建constellation
            constellation = create_simple_constellation(
                task_descriptions=["Task 1", "Task 2"],
                constellation_name="test",
                sequential=True
            )
            constellation.is_complete = lambda: False
            agent._current_constellation = constellation
            agent.update_constellation_with_lock = lambda *args: asyncio.coroutine(lambda: constellation)()
            agent.should_continue = lambda *args: asyncio.coroutine(lambda: False)()
            
            # 测试任务开始跟踪
            await monitoring_state.queue_task_update({
                "task_id": "task_1",
                "event_type": EventType.TASK_STARTED.value,
                "status": "running"
            })
            
            await monitoring_state._process_pending_updates(agent, None)
            assert "task_1" in monitoring_state._running_tasks
            
            # 测试任务完成跟踪
            await monitoring_state.queue_task_update({
                "task_id": "task_1",
                "event_type": EventType.TASK_COMPLETED.value,
                "status": "completed"
            })
            
            await monitoring_state._process_pending_updates(agent, None)
            assert "task_1" not in monitoring_state._running_tasks
            
            self._record_success("监控状态任务跟踪")
            
        except Exception as e:
            self._record_failure("监控状态任务跟踪", e)
    
    async def test_observer_integration(self):
        """测试观察者集成"""
        print("👁️ 测试观察者集成...")
        
        try:
            agent = MockGalaxyWeaverAgent()
            context = Context()
            event_bus = get_event_bus()
            
            # 设置监控状态
            from ufo.galaxy.agents.galaxy_agent_state import MonitoringGalaxyAgentState
            monitoring_state = MonitoringGalaxyAgentState()
            agent._state = monitoring_state
            agent.queue_task_update_to_current_state = monitoring_state.queue_task_update
            
            # 创建观察者
            observer = ConstellationProgressObserver(agent, context)
            event_bus.subscribe(observer)
            
            # 发布任务事件
            task_event = TaskEvent(
                event_type=EventType.TASK_STARTED,
                source_id="test_source",
                timestamp=time.time(),
                data={},
                task_id="task_1",
                status="running"
            )
            
            await event_bus.publish_event(task_event)
            await asyncio.sleep(0.1)  # 等待事件处理
            
            # 处理pending updates
            await monitoring_state._process_pending_updates(agent, context)
            
            # 验证事件被转发到状态机
            assert "task_1" in monitoring_state._running_tasks
                
            self._record_success("观察者集成")
            
        except Exception as e:
            self._record_failure("观察者集成", e)
    
    async def test_complete_workflow(self):
        """测试完整工作流"""
        print("🔄 测试完整工作流...")
        
        try:
            agent = MockGalaxyWeaverAgent()
            context = Context()
            from ufo.module.context import ContextNames
            context.set(ContextNames.REQUEST, "complete workflow test")
            
            # 模拟完整状态机循环
            state_manager = GalaxyAgentStateManager()
            
            # 1. 创建状态
            agent._status = GalaxyAgentStatus.CREATING.value
            state = state_manager.get_state(agent._status)
            await state.handle(agent, context)
            
            assert agent._status == GalaxyAgentStatus.MONITORING.value
            
            # 2. 监控状态
            state = state_manager.get_state(agent._status)
            monitoring_state = state
            
            # 模拟任务执行
            await monitoring_state.queue_task_update({
                "task_id": "task_1",
                "event_type": EventType.TASK_STARTED.value,
            })
            
            await monitoring_state.queue_task_update({
                "task_id": "task_1",
                "event_type": EventType.TASK_COMPLETED.value,
            })
            
            # 设置constellation完成
            agent.current_constellation.is_complete = lambda: True
            agent.should_continue = lambda *args: asyncio.coroutine(lambda: False)()
            
            await state.handle(agent, context)
            
            assert agent._status == GalaxyAgentStatus.FINISHED.value
            
            self._record_success("完整工作流")
            
        except Exception as e:
            self._record_failure("完整工作流", e)
    
    async def test_race_condition_resolution(self):
        """测试竞态条件解决"""
        print("⚡ 测试竞态条件解决...")
        
        try:
            monitoring_state = MonitoringGalaxyAgentState()
            agent = MockGalaxyWeaverAgent()
            
            # 创建constellation
            constellation = create_simple_constellation(
                task_descriptions=["Task 1", "Task 2"],
                constellation_name="race_test",
                sequential=True
            )
            agent._current_constellation = constellation
            agent.update_constellation_with_lock = lambda *args: asyncio.coroutine(lambda: constellation)()
            
            # 模拟竞态条件：快速连续的任务完成
            tasks = [
                {"task_id": "task_1", "event_type": EventType.TASK_STARTED.value},
                {"task_id": "task_2", "event_type": EventType.TASK_STARTED.value},
                {"task_id": "task_1", "event_type": EventType.TASK_COMPLETED.value},
                {"task_id": "task_2", "event_type": EventType.TASK_COMPLETED.value},
            ]
            
            # 快速添加所有任务更新
            for task in tasks:
                await monitoring_state.queue_task_update(task)
            
            # 设置completion逻辑
            def mock_is_complete():
                return (monitoring_state._pending_task_updates.empty() and 
                       len(monitoring_state._running_tasks) == 0)
            
            constellation.is_complete = mock_is_complete
            agent.should_continue = lambda *args: asyncio.coroutine(lambda: False)()
            
            # 处理所有更新
            await monitoring_state._process_pending_updates(agent, None)
            
            # 验证所有任务被正确处理
            assert len(monitoring_state._running_tasks) == 0
            assert monitoring_state._pending_task_updates.empty()
            
            # 检查真正完成
            is_complete = await monitoring_state._check_true_completion(agent, None)
            assert is_complete
            
            self._record_success("竞态条件解决")
            
        except Exception as e:
            self._record_failure("竞态条件解决", e)
    
    async def test_error_handling(self):
        """测试错误处理"""
        print("🚨 测试错误处理...")
        
        try:
            # 测试创建状态错误处理
            agent = MockGalaxyWeaverAgent()
            agent.process_initial_request = lambda *args: asyncio.coroutine(
                lambda: exec('raise Exception("Test error")')
            )()
            
            creating_state = CreatingGalaxyAgentState()
            context = Context()
            from ufo.module.context import ContextNames
            context.set(ContextNames.REQUEST, "error test")
            
            await creating_state.handle(agent, context)
            
            assert agent._status == GalaxyAgentStatus.FAILED.value
            
            # 测试监控状态无constellation错误处理
            monitoring_state = MonitoringGalaxyAgentState()
            agent._current_constellation = None
            
            await monitoring_state.handle(agent, None)
            
            assert agent._status == GalaxyAgentStatus.FAILED.value
            
            self._record_success("错误处理")
            
        except Exception as e:
            self._record_failure("错误处理", e)
    
    async def test_concurrent_operations(self):
        """测试并发操作"""
        print("🏃‍♂️ 测试并发操作...")
        
        try:
            monitoring_state = MonitoringGalaxyAgentState()
            agent = MockGalaxyWeaverAgent()
            agent.update_constellation_with_lock = lambda *args: asyncio.coroutine(lambda: None)()
            
            # 并发添加任务更新
            async def add_updates(start_id: int, count: int):
                for i in range(count):
                    await monitoring_state.queue_task_update({
                        "task_id": f"task_{start_id + i}",
                        "event_type": EventType.TASK_STARTED.value,
                        "status": "running"
                    })
                    await asyncio.sleep(0.001)
            
            # 启动多个并发任务
            await asyncio.gather(
                add_updates(0, 10),
                add_updates(10, 10),
                add_updates(20, 10)
            )
            
            # 处理所有更新
            await monitoring_state._process_pending_updates(agent, None)
            
            # 验证所有任务都被正确跟踪
            assert len(monitoring_state._running_tasks) == 30
            
            self._record_success("并发操作")
            
        except Exception as e:
            self._record_failure("并发操作", e)
    
    def _record_success(self, test_name: str):
        """记录成功测试"""
        self.results["tests_run"] += 1
        self.results["tests_passed"] += 1
        print(f"✅ {test_name} - 通过")
    
    def _record_failure(self, test_name: str, error: Exception):
        """记录失败测试"""
        self.results["tests_run"] += 1
        self.results["tests_failed"] += 1
        self.results["failures"].append({
            "test": test_name,
            "error": str(error),
            "type": type(error).__name__
        })
        print(f"❌ {test_name} - 失败: {error}")
    
    def generate_report(self):
        """生成测试报告"""
        print("\n" + "=" * 60)
        print("📊 测试报告")
        print("=" * 60)
        
        print(f"总测试数: {self.results['tests_run']}")
        print(f"通过: {self.results['tests_passed']}")
        print(f"失败: {self.results['tests_failed']}")
        print(f"执行时间: {self.results['execution_time']:.2f}秒")
        
        if self.results["failures"]:
            print("\n❌ 失败测试详情:")
            for failure in self.results["failures"]:
                print(f"  - {failure['test']}: {failure['error']}")
        
        success_rate = (self.results['tests_passed'] / self.results['tests_run']) * 100 if self.results['tests_run'] > 0 else 0
        print(f"\n成功率: {success_rate:.1f}%")
        
        if success_rate == 100:
            print("🎉 所有测试通过！Galaxy状态机系统重构成功！")
        else:
            print("⚠️ 存在失败测试，需要进一步调试")


async def main():
    """主函数"""
    runner = GalaxyStateMachineTestRunner()
    results = await runner.run_all_tests()
    
    # 返回适当的退出代码
    exit_code = 0 if results["tests_failed"] == 0 else 1
    sys.exit(exit_code)


if __name__ == "__main__":
    asyncio.run(main())
