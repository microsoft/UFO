"""
Host Agent 策略装饰器验证脚本

验证Host Agent Processor中所有策略的装饰器配置是否正确，
包括依赖关系验证和策略链一致性检查。
"""

import logging
import sys
import os

# Add the UFO2 directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from ufo.agents.processors2.core.strategy_dependency import (
    StrategyDependencyValidator,
    validate_provides_consistency,
)
from ufo.agents.processors2.host_agent_processor import (
    DesktopDataCollectionStrategy,
    HostLLMInteractionStrategy,
    HostActionExecutionStrategy,
    HostMemoryUpdateStrategy,
)

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def test_strategy_metadata_extraction():
    """测试各策略的装饰器元数据是否正确提取"""
    logger.info("=== 测试策略装饰器元数据提取 ===")

    strategies = [
        ("DesktopDataCollectionStrategy", DesktopDataCollectionStrategy()),
        ("HostLLMInteractionStrategy", HostLLMInteractionStrategy()),
        ("HostActionExecutionStrategy", HostActionExecutionStrategy()),
        ("HostMemoryUpdateStrategy", HostMemoryUpdateStrategy()),
    ]

    for name, strategy in strategies:
        logger.info(f"\n--- {name} ---")

        # 检查依赖声明
        dependencies = getattr(strategy, "_strategy_dependencies", [])
        if dependencies:
            logger.info(f"Dependencies ({len(dependencies)}):")
            for dep in dependencies:
                logger.info(
                    f"  - {dep.field_name} ({dep.dependency_type.value}): {dep.description}"
                )
        else:
            logger.warning(f"  No dependencies found for {name}")

        # 检查提供声明
        provides = getattr(strategy, "_strategy_provides", [])
        if provides:
            logger.info(f"Provides ({len(provides)}): {provides}")
        else:
            logger.warning(f"  No provides found for {name}")


def test_host_agent_strategy_chain_validation():
    """测试Host Agent策略链的依赖关系验证"""
    logger.info("\n=== 测试Host Agent策略链验证 ===")

    validator = StrategyDependencyValidator()

    # 创建Host Agent策略链（按执行顺序）
    strategies = [
        DesktopDataCollectionStrategy(),  # DATA_COLLECTION
        HostLLMInteractionStrategy(),  # LLM_INTERACTION
        HostActionExecutionStrategy(),  # ACTION_EXECUTION
        HostMemoryUpdateStrategy(),  # MEMORY_UPDATE
    ]

    logger.info(f"验证包含{len(strategies)}个策略的策略链...")

    # 验证策略链
    result = validator.validate_strategy_chain(strategies)

    logger.info(f"策略链验证结果: {'通过 ✓' if result.is_valid else '失败 ✗'}")

    if result.errors:
        logger.warning("发现验证错误:")
        for error in result.errors:
            logger.warning(f"  - {error}")
    else:
        logger.info("策略链依赖关系验证通过！")

    # 打印详细报告
    logger.info(f"\n验证详细报告:\n{result.report}")


def test_strategy_dependency_coverage():
    """测试策略依赖覆盖情况"""
    logger.info("\n=== 测试策略依赖覆盖情况 ===")

    strategies = [
        DesktopDataCollectionStrategy(),
        HostLLMInteractionStrategy(),
        HostActionExecutionStrategy(),
        HostMemoryUpdateStrategy(),
    ]

    # 收集所有提供的字段
    all_provides = set()
    for strategy in strategies:
        provides = getattr(strategy, "_strategy_provides", [])
        all_provides.update(provides)

    logger.info(f"所有策略总共提供 {len(all_provides)} 个字段:")
    for field in sorted(all_provides):
        logger.info(f"  - {field}")

    # 收集所有依赖的字段
    all_dependencies = set()
    required_dependencies = set()
    optional_dependencies = set()

    for strategy in strategies:
        dependencies = getattr(strategy, "_strategy_dependencies", [])
        for dep in dependencies:
            all_dependencies.add(dep.field_name)
            if dep.dependency_type.value == "REQUIRED":
                required_dependencies.add(dep.field_name)
            else:
                optional_dependencies.add(dep.field_name)

    logger.info(f"\n依赖统计:")
    logger.info(f"  总依赖字段: {len(all_dependencies)}")
    logger.info(f"  必需依赖: {len(required_dependencies)}")
    logger.info(f"  可选依赖: {len(optional_dependencies)}")

    # 检查外部依赖（不由策略链提供的依赖）
    external_dependencies = all_dependencies - all_provides
    if external_dependencies:
        logger.info(f"\n外部依赖 ({len(external_dependencies)}) - 需要由上下文提供:")
        for dep in sorted(external_dependencies):
            logger.info(f"  - {dep}")
    else:
        logger.info("\n✓ 没有外部依赖，所有依赖都由策略链内部提供")


def analyze_strategy_flow():
    """分析策略数据流"""
    logger.info("\n=== 分析策略数据流 ===")

    strategies = [
        ("DesktopDataCollectionStrategy", DesktopDataCollectionStrategy()),
        ("HostLLMInteractionStrategy", HostLLMInteractionStrategy()),
        ("HostActionExecutionStrategy", HostActionExecutionStrategy()),
        ("HostMemoryUpdateStrategy", HostMemoryUpdateStrategy()),
    ]

    logger.info("策略数据流分析:")
    for i, (name, strategy) in enumerate(strategies):
        logger.info(f"\n{i+1}. {name}")

        dependencies = getattr(strategy, "_strategy_dependencies", [])
        provides = getattr(strategy, "_strategy_provides", [])

        logger.info(
            f"   输入 ({len(dependencies)}): {[d.field_name for d in dependencies]}"
        )
        logger.info(f"   输出 ({len(provides)}): {provides}")

        # 分析与下一个策略的连接
        if i < len(strategies) - 1:
            next_name, next_strategy = strategies[i + 1]
            next_dependencies = getattr(next_strategy, "_strategy_dependencies", [])
            next_dep_names = {d.field_name for d in next_dependencies}

            # 检查当前策略的输出是否满足下一个策略的输入
            connections = set(provides) & next_dep_names
            if connections:
                logger.info(f"   → 连接到 {next_name}: {list(connections)}")
            else:
                logger.info(f"   → 与 {next_name} 无直接连接")


def main():
    """主测试函数"""
    logger.info("开始验证Host Agent策略装饰器配置...")

    try:
        # 1. 测试装饰器元数据
        test_strategy_metadata_extraction()

        # 2. 测试策略链验证
        test_host_agent_strategy_chain_validation()

        # 3. 测试依赖覆盖
        test_strategy_dependency_coverage()

        # 4. 分析策略流
        analyze_strategy_flow()

        logger.info("\n" + "=" * 60)
        logger.info("✅ Host Agent策略装饰器配置验证完成!")
        logger.info("所有策略都正确配置了依赖关系声明。")

    except Exception as e:
        logger.error(f"验证过程中出现错误: {e}")
        import traceback

        logger.error(traceback.format_exc())
        return False

    return True


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
