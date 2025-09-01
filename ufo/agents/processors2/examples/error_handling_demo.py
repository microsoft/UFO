"""
Example usage of the enhanced error handling system.
"""

import asyncio
import logging
from typing import Dict, Any

from ufo.agents.processors2.core.processor_framework import (
    ProcessorTemplate,
    ProcessingPhase,
)
from ufo.agents.processors2.strategies.data_collection_strategies import (
    HostDataCollectionStrategy,
    ScreenshotCollectionStrategy,
    CriticalDataCollectionStrategy,
)
from ufo.agents.processors2.middleware.enhanced_middleware import (
    EnhancedLoggingMiddleware,
    ErrorRecoveryMiddleware,
    ResourceCleanupMiddleware,
    MetricsCollectionMiddleware,
)


class ExampleProcessor(ProcessorTemplate):
    """
    Example processor demonstrating different error handling strategies.
    """

    def _setup_strategies(self) -> None:
        """Set up strategies with different error handling behaviors."""

        # 关键数据收集：快速失败，触发on_error中间件
        self.strategies[ProcessingPhase.SETUP] = CriticalDataCollectionStrategy()

        # 截图收集：优雅失败，不触发on_error中间件
        self.strategies[ProcessingPhase.DATA_COLLECTION] = ScreenshotCollectionStrategy(
            fail_fast=False
        )

        # Host数据收集：可配置的失败模式
        # 在生产环境中可能设置为fail_fast=True，在开发环境中设置为False
        fail_fast_mode = self.global_context.get("fail_fast_mode", True)
        host_strategy = HostDataCollectionStrategy(fail_fast=fail_fast_mode)
        self.strategies[ProcessingPhase.LLM_INTERACTION] = host_strategy

    def _setup_middleware(self) -> None:
        """Set up middleware chain with enhanced error handling."""
        self.middleware_chain = [
            MetricsCollectionMiddleware(),  # 收集性能指标
            ResourceCleanupMiddleware(),  # 资源清理
            ErrorRecoveryMiddleware(max_retries=3),  # 错误恢复
            EnhancedLoggingMiddleware(log_level=logging.INFO),  # 增强日志
        ]

    def _create_memory_item(self) -> None:
        """Create memory item - required by base class."""
        pass

    def _get_keys_to_promote(self) -> list:
        """Define keys to promote to global context."""
        return ["critical_data", "processing_metrics"]


async def demonstrate_error_handling():
    """
    Demonstrate different error handling scenarios.
    """
    print("=== Error Handling Demonstration ===\n")

    # 模拟上下文
    from ufo.module.context import Context
    from ufo.agents.agent.basic import BasicAgent

    # 创建模拟的全局上下文
    global_context = Context()
    global_context.set("session_step", 1)
    global_context.set("round_step", 1)
    global_context.set("round_num", 0)
    global_context.set("log_path", "/tmp/test/")

    # 创建模拟的Agent
    agent = BasicAgent("test_agent")

    # 场景1：正常处理（所有策略成功）
    print("1. Testing normal processing...")
    global_context.set("fail_fast_mode", False)
    global_context.set("simulate_error", False)

    processor = ExampleProcessor(agent, global_context)
    result = await processor.process()

    print(f"   Result: {'SUCCESS' if result.success else 'FAILED'}")
    print(f"   Execution time: {result.execution_time:.2f}s")
    if not result.success:
        print(f"   Error: {result.error}")
    print()

    # 场景2：优雅失败（截图失败，但不触发on_error）
    print("2. Testing graceful failure (screenshot fails, no on_error triggered)...")
    global_context.set("fail_fast_mode", False)
    global_context.set("simulate_screenshot_error", True)

    processor2 = ExampleProcessor(agent, global_context)
    result2 = await processor2.process()

    print(f"   Result: {'SUCCESS' if result2.success else 'FAILED'}")
    print(f"   Error: {result2.error if not result2.success else 'N/A'}")
    print()

    # 场景3：快速失败（关键数据收集失败，触发on_error）
    print(
        "3. Testing fail-fast behavior (critical data collection fails, triggers on_error)..."
    )
    global_context.set("fail_fast_mode", True)
    global_context.set("simulate_critical_error", True)

    processor3 = ExampleProcessor(agent, global_context)
    result3 = await processor3.process()

    print(f"   Result: {'SUCCESS' if result3.success else 'FAILED'}")
    print(f"   Error: {result3.error if not result3.success else 'N/A'}")
    if hasattr(result3, "phase") and result3.phase:
        print(f"   Failed at phase: {result3.phase.value}")
    print()

    # 获取指标摘要
    metrics_middleware = None
    for middleware in processor3.middleware_chain:
        if isinstance(middleware, MetricsCollectionMiddleware):
            metrics_middleware = middleware
            break

    if metrics_middleware:
        print("4. Metrics Summary:")
        metrics = metrics_middleware.get_metrics_summary()
        for key, value in metrics.items():
            print(f"   {key}: {value}")


class MockCommandDispatcher:
    """Mock command dispatcher for testing."""

    def __init__(self, context: Dict[str, Any]):
        self.context = context

    async def execute_commands(self, commands):
        """Mock command execution."""
        for command in commands:
            if command.tool_name == "capture_desktop_screenshot":
                if self.context.get("simulate_error"):
                    raise Exception("Simulated screenshot error")
                return [type("Result", (), {"result": "mock_screenshot_url"})()]

            elif command.tool_name == "get_desktop_app_info":
                if self.context.get("simulate_error"):
                    raise Exception("Simulated app info error")
                return [type("Result", (), {"result": []})()]

            elif command.tool_name == "capture_window_screenshot":
                if self.context.get("simulate_screenshot_error"):
                    raise Exception("Simulated window screenshot error")
                return [type("Result", (), {"result": "mock_window_screenshot_url"})()]

        return []


def setup_logging():
    """Set up logging for the demonstration."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler("error_handling_demo.log"),
        ],
    )


if __name__ == "__main__":
    setup_logging()
    asyncio.run(demonstrate_error_handling())
