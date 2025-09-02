#!/usr/bin/env python3
"""
Detailed Dependency Chain Validation Demo

This script demonstrates the detailed strategy chain validation functionality
that analyzes the complete dependency graph and provides comprehensive reports.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from typing import Dict, List
from ufo.agents.processors2.core.processing_context import ProcessingPhase
from ufo.agents.processors2.core.strategy_dependency import (
    StrategyDependency,
    StrategyDependencyValidator,
)
from ufo.agents.processors2.strategies.processing_strategy import BaseProcessingStrategy


# Mock strategies for demonstration
class MockSetupStrategy(BaseProcessingStrategy):
    """Setup strategy that provides initial configuration"""

    def __init__(self):
        super().__init__("setup_strategy")

    def get_dependencies(self) -> List[StrategyDependency]:
        return [
            StrategyDependency(
                field_name="global_config",
                required=False,
                description="Global configuration (from global context)",
            )
        ]

    def get_provides(self) -> List[str]:
        return ["initial_config", "system_state"]

    async def execute(self, context):
        from ufo.agents.processors2.core.processing_context import ProcessingResult

        return ProcessingResult(
            success=True, data={"initial_config": {}, "system_state": "ready"}
        )


class MockDataCollectionStrategy(BaseProcessingStrategy):
    """Data collection strategy that needs setup data"""

    def __init__(self):
        super().__init__("data_collection_strategy")

    def get_dependencies(self) -> List[StrategyDependency]:
        return [
            StrategyDependency(
                field_name="command_dispatcher",
                required=True,
                description="Command dispatcher (from global context)",
            ),
            StrategyDependency(
                field_name="initial_config",
                required=True,
                expected_type=dict,
                description="Configuration from setup strategy",
            ),
            StrategyDependency(
                field_name="log_path",
                required=False,
                default_value="/tmp/",
                description="Optional log path",
            ),
        ]

    def get_provides(self) -> List[str]:
        return ["screenshot_data", "control_info", "collected_items"]

    async def execute(self, context):
        from ufo.agents.processors2.core.processing_context import ProcessingResult

        return ProcessingResult(
            success=True,
            data={
                "screenshot_data": {"url": "mock_screenshot"},
                "control_info": [{"id": 1, "type": "button"}],
                "collected_items": ["item1", "item2"],
            },
        )


class MockProcessingStrategy(BaseProcessingStrategy):
    """Processing strategy that depends on collected data"""

    def __init__(self):
        super().__init__("processing_strategy")

    def get_dependencies(self) -> List[StrategyDependency]:
        return [
            StrategyDependency(
                field_name="screenshot_data",
                required=True,
                expected_type=dict,
                description="Screenshot data from data collection",
            ),
            StrategyDependency(
                field_name="control_info",
                required=True,
                expected_type=list,
                description="Control info from data collection",
            ),
            StrategyDependency(
                field_name="system_state",
                required=False,
                description="System state from setup (optional for processing)",
            ),
        ]

    def get_provides(self) -> List[str]:
        return ["parsed_response", "action_plan", "processing_summary"]

    async def execute(self, context):
        from ufo.agents.processors2.core.processing_context import ProcessingResult

        return ProcessingResult(
            success=True,
            data={
                "parsed_response": {"intent": "click", "target": "button"},
                "action_plan": {"steps": ["locate", "click"]},
                "processing_summary": "Processed successfully",
            },
        )


class MockActionStrategy(BaseProcessingStrategy):
    """Action strategy that executes based on processed data"""

    def __init__(self):
        super().__init__("action_strategy")

    def get_dependencies(self) -> List[StrategyDependency]:
        return [
            StrategyDependency(
                field_name="action_plan",
                required=True,
                expected_type=dict,
                description="Action plan from processing strategy",
            ),
            StrategyDependency(
                field_name="control_info",
                required=True,
                expected_type=list,
                description="Control info (passed through from data collection)",
            ),
            StrategyDependency(
                field_name="command_dispatcher",
                required=True,
                description="Command dispatcher for action execution",
            ),
        ]

    def get_provides(self) -> List[str]:
        return ["execution_result", "action_summary"]

    async def execute(self, context):
        from ufo.agents.processors2.core.processing_context import ProcessingResult

        return ProcessingResult(
            success=True,
            data={
                "execution_result": {"success": True},
                "action_summary": "Action executed successfully",
            },
        )


class MockBrokenStrategy(BaseProcessingStrategy):
    """Broken strategy that depends on non-existent data"""

    def __init__(self):
        super().__init__("broken_strategy")

    def get_dependencies(self) -> List[StrategyDependency]:
        return [
            StrategyDependency(
                field_name="nonexistent_data",
                required=True,
                description="Data that no previous strategy provides",
            )
        ]

    def get_provides(self) -> List[str]:
        return ["broken_output"]

    async def execute(self, context):
        from ufo.agents.processors2.core.processing_context import ProcessingResult

        return ProcessingResult(success=False, error="Broken strategy")


def demo_detailed_validation():
    """Demonstrate detailed strategy chain validation"""
    print("=" * 70)
    print("详细策略链依赖验证演示")
    print("=" * 70)

    validator = StrategyDependencyValidator()

    # Test 1: Valid strategy chain
    print("\n🧪 测试 1: 有效的策略链")
    print("-" * 50)

    valid_strategies = {
        ProcessingPhase.SETUP: MockSetupStrategy(),
        ProcessingPhase.DATA_COLLECTION: MockDataCollectionStrategy(),
        ProcessingPhase.LLM_INTERACTION: MockProcessingStrategy(),
        ProcessingPhase.ACTION_EXECUTION: MockActionStrategy(),
    }

    report = validator.validate_strategy_chain_detailed(valid_strategies)
    validator.print_dependency_report(report)

    # Test 2: Strategy chain with missing dependencies
    print("\n\n🧪 测试 2: 有依赖问题的策略链")
    print("-" * 50)

    broken_strategies = {
        ProcessingPhase.SETUP: MockSetupStrategy(),
        ProcessingPhase.DATA_COLLECTION: MockDataCollectionStrategy(),
        ProcessingPhase.LLM_INTERACTION: MockBrokenStrategy(),  # This one has missing deps
        ProcessingPhase.ACTION_EXECUTION: MockActionStrategy(),
    }

    report = validator.validate_strategy_chain_detailed(broken_strategies)
    validator.print_dependency_report(report)

    # Test 3: Analyze field flow patterns
    print("\n\n🧪 测试 3: 字段流分析")
    print("-" * 50)

    analyze_field_flow(report)


def analyze_field_flow(report: Dict):
    """Analyze and highlight interesting patterns in field flow"""

    field_flow = report["field_flow"]

    print("字段使用模式分析:")

    # Find fields that are provided but never consumed
    unused_fields = []
    # Find fields that are consumed but never provided
    missing_providers = []
    # Find fields that flow through multiple strategies
    multi_consumer_fields = []

    for field, flow in field_flow.items():
        if len(flow["providers"]) == 0:
            missing_providers.append(field)
        elif len(flow["consumers"]) == 0:
            unused_fields.append(field)
        elif len(flow["consumers"]) > 1:
            multi_consumer_fields.append((field, len(flow["consumers"])))

    if unused_fields:
        print(f"\n🔶 未被使用的字段 ({len(unused_fields)}):")
        for field in unused_fields:
            providers = [
                f"{p['phase']}({p['strategy']})" for p in field_flow[field]["providers"]
            ]
            print(f"  - {field}: 由 {', '.join(providers)} 提供但未被消费")

    if missing_providers:
        print(f"\n🔴 缺少提供者的字段 ({len(missing_providers)}):")
        for field in missing_providers:
            consumers = [
                f"{c['phase']}({c['strategy']})" for c in field_flow[field]["consumers"]
            ]
            print(f"  - {field}: 被 {', '.join(consumers)} 需要但无提供者")

    if multi_consumer_fields:
        print(f"\n🔄 被多个策略使用的字段 ({len(multi_consumer_fields)}):")
        for field, count in multi_consumer_fields:
            providers = [
                f"{p['phase']}({p['strategy']})" for p in field_flow[field]["providers"]
            ]
            consumers = [
                f"{c['phase']}({c['strategy']})" for c in field_flow[field]["consumers"]
            ]
            print(
                f"  - {field}: {', '.join(providers)} -> {', '.join(consumers)} ({count}个消费者)"
            )


def demo_optimization_suggestions():
    """Demonstrate optimization suggestions based on dependency analysis"""
    print("\n\n🛠️  优化建议")
    print("-" * 50)

    suggestions = [
        "✅ 通过依赖声明，可以自动检测策略配置错误",
        "✅ 可以识别不必要的数据传递，优化内存使用",
        "✅ 可以并行执行没有依赖关系的策略",
        "✅ 可以提前验证数据类型，避免运行时错误",
        "✅ 可以生成策略执行的最优顺序",
        "✅ 可以自动生成策略文档和依赖图",
    ]

    for suggestion in suggestions:
        print(f"  {suggestion}")


if __name__ == "__main__":
    demo_detailed_validation()
    demo_optimization_suggestions()

    print("\n" + "=" * 70)
    print("演示完成！")
    print("=" * 70)
    print("\n📋 功能总结:")
    print("1. 完整的策略链依赖分析")
    print("2. 字段流向可视化")
    print("3. 依赖问题早期检测")
    print("4. 优化建议和模式识别")
    print("5. 中文本地化的报告输出")
