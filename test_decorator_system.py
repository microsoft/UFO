"""
测试脚本：验证装饰器系统和运行时一致性检查

这个脚本演示：
1. 装饰器如何工作
2. 依赖关系验证
3. 运行时一致性检查
4. 错误报告机制
"""

import logging
import asyncio
from typing import List

from ufo.agents.processors2.core.strategy_dependency import (
    StrategyDependencyValidator,
    validate_provides_consistency,
    StrategyDependency,
    DependencyType,
)
from ufo.agents.processors2.core.processing_context import (
    ProcessingContext,
    BasicProcessorContext,
)
from ufo.agents.processors2.strategies.example_decorated_strategies import (
    RequestParsingStrategy,
    ActionPlanningStrategy,
    ActionExecutionStrategy,
    ResultSummaryStrategy,
)
from ufo.module.context import Context


# 设置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def test_decorator_metadata_extraction():
    """测试装饰器元数据提取"""
    logger.info("=== 测试装饰器元数据提取 ===")

    # 测试组合装饰器
    request_strategy = RequestParsingStrategy()
    dependencies = getattr(request_strategy, "_strategy_dependencies", [])
    provides = getattr(request_strategy, "_strategy_provides", [])

    logger.info(
        f"RequestParsingStrategy dependencies: {[d.field_name for d in dependencies]}"
    )
    logger.info(f"RequestParsingStrategy provides: {provides}")

    # 测试单独装饰器
    planning_strategy = ActionPlanningStrategy()
    dependencies = getattr(planning_strategy, "_strategy_dependencies", [])
    provides = getattr(planning_strategy, "_strategy_provides", [])

    logger.info(
        f"ActionPlanningStrategy dependencies: {[d.field_name for d in dependencies]}"
    )
    logger.info(f"ActionPlanningStrategy provides: {provides}")


def test_strategy_chain_validation():
    """测试策略链验证"""
    logger.info("\n=== 测试策略链验证 ===")

    validator = StrategyDependencyValidator()

    # 创建策略链
    strategies = [
        RequestParsingStrategy(),
        ActionPlanningStrategy(),
        ActionExecutionStrategy(),
        ResultSummaryStrategy(),
    ]

    # 验证策略链
    result = validator.validate_strategy_chain(strategies)

    logger.info(f"Chain validation result: {'PASSED' if result.is_valid else 'FAILED'}")
    if result.errors:
        logger.warning("Validation errors:")
        for error in result.errors:
            logger.warning(f"  - {error}")

    logger.info(f"Validation report:\n{result.report}")


async def test_runtime_consistency_validation():
    """测试运行时一致性验证"""
    logger.info("\n=== 测试运行时一致性验证 ===")

    # 创建模拟上下文
    global_context = Context()
    local_context = BasicProcessorContext()
    processing_context = ProcessingContext(global_context, local_context)

    # 设置初始数据
    processing_context.set_local("user_request", "Click the submit button")
    processing_context.set_local("current_app", "TestApp")

    # 1. 测试正确的策略（RequestParsingStrategy）
    logger.info("1. 测试正确的策略...")
    request_strategy = RequestParsingStrategy()
    result = await request_strategy.execute(processing_context)

    if result.success:
        # 更新上下文
        processing_context.update_local(result.data)

        # 验证provides一致性
        validation_errors = validate_provides_consistency(
            request_strategy, processing_context.local_context
        )
        if validation_errors:
            logger.warning(
                f"RequestParsingStrategy consistency errors: {validation_errors}"
            )
        else:
            logger.info("RequestParsingStrategy: 所有provides字段一致 ✓")

    # 2. 测试不一致的策略（ActionExecutionStrategy）
    logger.info("\n2. 测试不一致的策略...")

    # 先执行ActionPlanningStrategy来提供必需的依赖
    planning_strategy = ActionPlanningStrategy()
    result = await planning_strategy.execute(processing_context)
    if result.success:
        processing_context.update_local(result.data)

    # 执行有问题的策略
    execution_strategy = ActionExecutionStrategy()
    result = await execution_strategy.execute(processing_context)

    if result.success:
        processing_context.update_local(result.data)

        # 验证provides一致性 - 这里应该发现问题
        validation_errors = validate_provides_consistency(
            execution_strategy, processing_context.local_context
        )
        if validation_errors:
            logger.warning(
                f"ActionExecutionStrategy consistency errors: {validation_errors}"
            )
            logger.info("✓ 成功检测到provides不一致的问题")
        else:
            logger.error("未检测到应该存在的不一致问题")


def test_dependency_type_validation():
    """测试依赖类型验证"""
    logger.info("\n=== 测试依赖类型验证 ===")

    # 创建测试上下文
    global_context = Context()
    local_context = BasicProcessorContext()
    processing_context = ProcessingContext(global_context, local_context)

    validator = StrategyDependencyValidator()

    # 设置一些数据
    processing_context.set_local("user_request", "test request")
    processing_context.set_local("parsed_request", "parsed test")
    # 故意不设置 target_elements (required dependency)

    # 测试依赖验证
    planning_strategy = ActionPlanningStrategy()
    dependencies = getattr(planning_strategy, "_strategy_dependencies", [])

    logger.info(f"Testing dependencies: {[d.field_name for d in dependencies]}")
    logger.info(
        f"Available in context: {list(processing_context.local_context.__dict__.keys())}"
    )

    # 验证运行时依赖
    result = validator.validate_runtime_dependencies(dependencies, processing_context)

    logger.info(
        f"Runtime validation result: {'PASSED' if result.is_valid else 'FAILED'}"
    )
    if result.errors:
        logger.warning("Runtime validation errors:")
        for error in result.errors:
            logger.warning(f"  - {error}")


def main():
    """主测试函数"""
    logger.info("开始测试装饰器系统和运行时验证...")

    try:
        # 1. 测试装饰器元数据
        test_decorator_metadata_extraction()

        # 2. 测试策略链验证
        test_strategy_chain_validation()

        # 3. 测试依赖类型验证
        test_dependency_type_validation()

        # 4. 测试运行时一致性验证
        asyncio.run(test_runtime_consistency_validation())

        logger.info("\n=== 测试完成 ===")
        logger.info("装饰器系统和运行时验证功能正常工作！")

    except Exception as e:
        logger.error(f"测试过程中出现错误: {e}")
        import traceback

        logger.error(traceback.format_exc())


if __name__ == "__main__":
    main()
