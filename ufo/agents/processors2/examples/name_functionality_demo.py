"""
演示Middleware和Strategy的name属性功能

展示如何使用简洁的name而不是冗长的class.__name__来进行日志记录
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from collections import OrderedDict
from enum import Enum
from dataclasses import dataclass
from abc import ABC, abstractmethod

# 配置日志
logging.basicConfig(level=logging.INFO, format="%(name)s - %(levelname)s - %(message)s")


# 模拟的枚举和数据类
class ProcessingPhase(Enum):
    DATA_COLLECTION = "data_collection"
    LLM_INTERACTION = "llm_interaction"
    ACTION_EXECUTION = "action_execution"
    MEMORY_UPDATE = "memory_update"


@dataclass
class ProcessingResult:
    success: bool
    data: Dict[str, Any]
    phase: Optional[ProcessingPhase] = None
    execution_time: float = 0.0
    error: Optional[str] = None


class ProcessingContext:
    def __init__(self):
        self.local_data: Dict[str, Any] = {}
        self.phase_results: OrderedDict[ProcessingPhase, ProcessingResult] = (
            OrderedDict()
        )


# 模拟的中间件基类
class ProcessorMiddleware(ABC):
    def __init__(self, name: Optional[str] = None):
        self.name = name or self.__class__.__name__
        self.logger = logging.getLogger(f"Middleware.{self.name}")

    @abstractmethod
    async def before_process(self, processor, context: ProcessingContext) -> None:
        pass

    @abstractmethod
    async def after_process(self, processor, result: ProcessingResult) -> None:
        pass

    @abstractmethod
    async def on_error(self, processor, error: Exception) -> None:
        pass


# 模拟的策略基类
class BaseProcessingStrategy(ABC):
    def __init__(self, name: Optional[str] = None, fail_fast: bool = True):
        self.name = name or self.__class__.__name__
        self.fail_fast = fail_fast
        self.logger = logging.getLogger(f"Strategy.{self.name}")

    @abstractmethod
    async def execute(self, context: ProcessingContext) -> ProcessingResult:
        pass


# 示例中间件实现
class TimingMiddleware(ProcessorMiddleware):
    """计时中间件 - 使用自定义名称"""

    def __init__(self, name: Optional[str] = None):
        super().__init__(name or "timer")  # 使用简短的名称
        self._context = None

    async def before_process(self, processor, context: ProcessingContext) -> None:
        self.logger.info("⏰ Starting timing")
        self._context = context
        context.local_data["start_time"] = asyncio.get_event_loop().time()

    async def after_process(self, processor, result: ProcessingResult) -> None:
        elapsed = asyncio.get_event_loop().time() - self._context.local_data.get(
            "start_time", 0
        )
        self.logger.info(f"✅ Processing completed in {elapsed:.2f}s")

    async def on_error(self, processor, error: Exception) -> None:
        elapsed = asyncio.get_event_loop().time() - self._context.local_data.get(
            "start_time", 0
        )
        self.logger.error(f"❌ Processing failed after {elapsed:.2f}s: {error}")


class ValidationMiddleware(ProcessorMiddleware):
    """验证中间件 - 使用默认类名"""

    async def before_process(self, processor, context: ProcessingContext) -> None:
        self.logger.info("🔍 Starting validation")

    async def after_process(self, processor, result: ProcessingResult) -> None:
        self.logger.info(f"✅ Validation passed: {result.success}")

    async def on_error(self, processor, error: Exception) -> None:
        self.logger.error(f"❌ Validation failed: {error}")


# 示例策略实现
class DataCollectionStrategy(BaseProcessingStrategy):
    """数据收集策略 - 使用自定义名称"""

    def __init__(self, name: Optional[str] = None):
        super().__init__(name or "data_collector")

    async def execute(self, context: ProcessingContext) -> ProcessingResult:
        self.logger.info("📊 Collecting data")
        await asyncio.sleep(0.1)  # 模拟工作

        return ProcessingResult(
            success=True,
            data={"collected_items": 5, "timestamp": "2025-09-02T10:30:00"},
            phase=ProcessingPhase.DATA_COLLECTION,
            execution_time=0.1,
        )


class LLMStrategy(BaseProcessingStrategy):
    """LLM策略 - 使用默认类名但展示长类名问题"""

    async def execute(self, context: ProcessingContext) -> ProcessingResult:
        self.logger.info("🤖 Processing with LLM")
        await asyncio.sleep(0.2)  # 模拟工作

        return ProcessingResult(
            success=True,
            data={"llm_response": "open_calculator", "confidence": 0.95},
            phase=ProcessingPhase.LLM_INTERACTION,
            execution_time=0.2,
        )


class SmartActionStrategy(BaseProcessingStrategy):
    """智能动作策略 - 使用自定义名称"""

    def __init__(self):
        super().__init__(name="smart_action")  # 比类名更简洁

    async def execute(self, context: ProcessingContext) -> ProcessingResult:
        self.logger.info("🎯 Executing smart action")
        await asyncio.sleep(0.15)  # 模拟工作

        return ProcessingResult(
            success=True,
            data={"action": "click", "target": "Calculator", "status": "success"},
            phase=ProcessingPhase.ACTION_EXECUTION,
            execution_time=0.15,
        )


# 模拟的处理器
class DemoProcessor:
    def __init__(self):
        self.logger = logging.getLogger("Processor.demo")
        self.middleware_chain = [
            TimingMiddleware(),  # 使用自定义名称 "timer"
            ValidationMiddleware(),  # 使用默认类名 "ValidationMiddleware"
            TimingMiddleware(name="custom_timer"),  # 使用完全自定义的名称
        ]

        self.strategies = {
            ProcessingPhase.DATA_COLLECTION: DataCollectionStrategy(),  # 使用 "data_collector"
            ProcessingPhase.LLM_INTERACTION: LLMStrategy(),  # 使用默认类名 "LLMStrategy"
            ProcessingPhase.ACTION_EXECUTION: SmartActionStrategy(),  # 使用 "smart_action"
        }

    async def process(self) -> ProcessingResult:
        context = ProcessingContext()

        try:
            self.logger.info("🚀 Starting processing workflow")

            # 执行前置中间件
            for middleware in self.middleware_chain:
                self.logger.info(
                    f"⬇️  Executing middleware before_process: {middleware.name}"
                )
                await middleware.before_process(self, context)

            # 执行各个阶段的策略
            combined_result = ProcessingResult(success=True, data={})

            for phase, strategy in self.strategies.items():
                self.logger.info(
                    f"📋 Starting phase: {phase.value}, with strategy: {strategy.name}"
                )

                result = await strategy.execute(context)
                context.phase_results[phase] = result
                combined_result.data.update(result.data)

                if not result.success:
                    combined_result = result
                    break

            # 执行后置中间件
            for middleware in reversed(self.middleware_chain):
                self.logger.info(
                    f"⬆️  Executing middleware after_process: {middleware.name}"
                )
                await middleware.after_process(self, combined_result)

            return combined_result

        except Exception as e:
            # 执行错误处理中间件
            for middleware in self.middleware_chain:
                self.logger.info(f"🚨 Executing middleware on_error: {middleware.name}")
                await middleware.on_error(self, e)

            raise


async def demonstrate_name_functionality():
    """演示name功能的改进"""

    print("🎭 Middleware和Strategy Name功能演示")
    print("=" * 60)

    print("\n📝 1. 对比日志输出:")
    print("   使用name属性后，日志更简洁易读")

    processor = DemoProcessor()

    print("\n🔄 2. 执行处理流程:")
    result = await processor.process()

    print(f"\n📊 3. 处理结果:")
    print(f"   成功: {result.success}")
    print(f"   数据项: {len(result.data)}")

    print(f"\n💡 4. Name功能优势:")
    print(f"   • 简洁的日志输出")
    print(f"   • 自定义友好名称")
    print(f"   • 更好的调试体验")
    print(f"   • 灵活的命名策略")


async def compare_old_vs_new():
    """对比旧的__class__.__name__和新的name属性"""

    print("\n" + "=" * 60)
    print("📊 新旧日志对比")
    print("=" * 60)

    # 模拟旧的方式（使用__class__.__name__）
    print("\n🔴 旧的方式 (使用 __class__.__name__):")
    print("   INFO - Executing middleware before_process: TimingMiddleware")
    print("   INFO - Executing middleware before_process: ValidationMiddleware")
    print(
        "   INFO - Starting phase: data_collection, with strategy: DataCollectionStrategy"
    )
    print("   INFO - Starting phase: llm_interaction, with strategy: LLMStrategy")
    print(
        "   INFO - Starting phase: action_execution, with strategy: SmartActionStrategy"
    )

    print("\n🟢 新的方式 (使用 name 属性):")
    print("   INFO - Executing middleware before_process: timer")
    print("   INFO - Executing middleware before_process: ValidationMiddleware")
    print("   INFO - Starting phase: data_collection, with strategy: data_collector")
    print("   INFO - Starting phase: llm_interaction, with strategy: LLMStrategy")
    print("   INFO - Starting phase: action_execution, with strategy: smart_action")

    print(f"\n✨ 改进点:")
    print(f"   • 中间件名称更简洁: 'timer' vs 'TimingMiddleware'")
    print(f"   • 策略名称更语义化: 'data_collector' vs 'DataCollectionStrategy'")
    print(f"   • 保持向后兼容: 没有name时使用类名")
    print(f"   • 支持完全自定义名称")


async def demonstrate_custom_names():
    """演示完全自定义的名称"""

    print("\n" + "=" * 60)
    print("🎨 自定义名称示例")
    print("=" * 60)

    # 创建带有中文名称的中间件和策略
    class ChineseTimerMiddleware(ProcessorMiddleware):
        def __init__(self):
            super().__init__(name="计时器")

        async def before_process(self, processor, context):
            self.logger.info("开始计时")

        async def after_process(self, processor, result):
            self.logger.info("计时完成")

        async def on_error(self, processor, error):
            self.logger.error(f"计时错误: {error}")

    class NumberedStrategy(BaseProcessingStrategy):
        def __init__(self, number: int):
            super().__init__(name=f"strategy_{number:02d}")

        async def execute(self, context):
            self.logger.info(f"执行第{self.name.split('_')[1]}号策略")
            return ProcessingResult(success=True, data={})

    # 展示自定义名称
    chinese_timer = ChineseTimerMiddleware()
    strategy_01 = NumberedStrategy(1)
    strategy_02 = NumberedStrategy(2)

    print(f"   中文中间件名称: {chinese_timer.name}")
    print(f"   编号策略名称1: {strategy_01.name}")
    print(f"   编号策略名称2: {strategy_02.name}")

    print(f"\n🌟 这展示了name属性的灵活性:")
    print(f"   • 支持多语言名称")
    print(f"   • 支持编号或版本化命名")
    print(f"   • 支持任何自定义格式")


async def main():
    """运行所有演示"""

    await demonstrate_name_functionality()
    await compare_old_vs_new()
    await demonstrate_custom_names()

    print("\n" + "=" * 60)
    print("🎉 Name功能演示完成!")
    print()
    print("核心改进:")
    print("• ✅ 添加了name属性到ProcessorMiddleware和ProcessingStrategy")
    print("• 🔧 更新了所有日志打印使用name而不是__class__.__name__")
    print("• 🎯 保持向后兼容，没有name时自动使用类名")
    print("• 🎨 支持完全自定义的友好名称")
    print("• 📝 日志输出更简洁易读")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
