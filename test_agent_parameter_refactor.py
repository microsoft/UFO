#!/usr/bin/env python3
"""
测试重构后的 agent 参数传递
"""

import sys
import os
import asyncio

# Add the UFO2 directory to the path
ufo_path = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ufo_path)


def test_strategy_interface():
    """测试策略接口的改进"""
    print("🔍 测试策略接口重构...")

    try:
        # 导入重构后的类
        from ufo.agents.processors2.strategies.processing_strategy import (
            BaseProcessingStrategy,
            ProcessingStrategy,
        )
        from ufo.agents.processors2.core.processing_context import (
            ProcessingContext,
            ProcessingResult,
            ProcessingPhase,
        )
        from ufo.agents.agent.basic import BasicAgent
        from ufo.module.context import Context
        import inspect

        # 检查 ProcessingStrategy 协议
        execute_signature = inspect.signature(ProcessingStrategy.execute)
        params = list(execute_signature.parameters.keys())

        print(f"   📋 ProcessingStrategy.execute 参数: {params}")

        # 验证参数是否包含 agent
        if "agent" in params:
            print("   ✅ ProcessingStrategy 协议已正确包含 agent 参数")
        else:
            print("   ❌ ProcessingStrategy 协议缺少 agent 参数")
            return False

        # 检查 BaseProcessingStrategy 抽象方法
        base_execute_signature = inspect.signature(BaseProcessingStrategy.execute)
        base_params = list(base_execute_signature.parameters.keys())

        print(f"   📋 BaseProcessingStrategy.execute 参数: {base_params}")

        if "agent" in base_params:
            print("   ✅ BaseProcessingStrategy 抽象方法已正确包含 agent 参数")
        else:
            print("   ❌ BaseProcessingStrategy 抽象方法缺少 agent 参数")
            return False

        return True

    except Exception as e:
        print(f"   ❌ 策略接口测试失败: {e}")
        return False


def test_host_processor_strategies():
    """测试 HostAgentProcessor 中的策略实现"""
    print("🔍 测试 HostAgentProcessor 策略实现...")

    try:
        from ufo.agents.processors2.host_agent_processor import (
            DesktopDataCollectionStrategy,
            HostLLMInteractionStrategy,
            HostActionExecutionStrategy,
            HostMemoryUpdateStrategy,
        )
        import inspect

        strategies = [
            ("DesktopDataCollectionStrategy", DesktopDataCollectionStrategy),
            ("HostLLMInteractionStrategy", HostLLMInteractionStrategy),
            ("HostActionExecutionStrategy", HostActionExecutionStrategy),
            ("HostMemoryUpdateStrategy", HostMemoryUpdateStrategy),
        ]

        for name, strategy_class in strategies:
            try:
                execute_signature = inspect.signature(strategy_class.execute)
                params = list(execute_signature.parameters.keys())

                print(f"   📋 {name}.execute 参数: {params}")

                if "agent" in params and "context" in params:
                    print(f"   ✅ {name} 已正确使用新的参数签名")
                else:
                    print(f"   ❌ {name} 参数签名不正确")
                    return False

            except Exception as e:
                print(f"   ❌ 检查 {name} 失败: {e}")
                return False

        return True

    except Exception as e:
        print(f"   ❌ HostAgentProcessor 策略测试失败: {e}")
        return False


def test_dependency_declarations():
    """测试依赖声明的更新"""
    print("🔍 测试依赖声明更新...")

    try:
        from ufo.agents.processors2.core.strategy_dependency import (
            StrategyMetadataRegistry,
        )
        from ufo.agents.processors2.host_agent_processor import (
            HostLLMInteractionStrategy,
            HostMemoryUpdateStrategy,
        )

        # 检查 HostLLMInteractionStrategy 的依赖
        llm_dependencies = StrategyMetadataRegistry.get_dependencies(
            HostLLMInteractionStrategy
        )
        if llm_dependencies:
            dep_names = [dep.field_name for dep in llm_dependencies]
            print(f"   📋 HostLLMInteractionStrategy 依赖: {dep_names}")

            if "host_agent" not in dep_names:
                print("   ✅ HostLLMInteractionStrategy 依赖中已移除 host_agent")
            else:
                print("   ❌ HostLLMInteractionStrategy 依赖中仍包含 host_agent")
                return False
        else:
            print("   📋 HostLLMInteractionStrategy 无依赖声明")

        # 检查 HostMemoryUpdateStrategy 的依赖
        memory_dependencies = StrategyMetadataRegistry.get_dependencies(
            HostMemoryUpdateStrategy
        )
        if memory_dependencies:
            dep_names = [dep.field_name for dep in memory_dependencies]
            print(f"   📋 HostMemoryUpdateStrategy 依赖: {dep_names}")

            if "host_agent" not in dep_names:
                print("   ✅ HostMemoryUpdateStrategy 依赖中已移除 host_agent")
            else:
                print("   ❌ HostMemoryUpdateStrategy 依赖中仍包含 host_agent")
                return False
        else:
            print("   📋 HostMemoryUpdateStrategy 无依赖声明")

        return True

    except Exception as e:
        print(f"   ❌ 依赖声明测试失败: {e}")
        return False


def test_framework_integration():
    """测试框架集成"""
    print("🔍 测试框架集成...")

    try:
        from ufo.agents.processors2.core.processor_framework import ProcessorTemplate
        import inspect

        # 检查 ProcessorTemplate.process 方法是否正确调用策略
        source = inspect.getsource(ProcessorTemplate.process)

        if "strategy.execute(self.agent, self.processing_context)" in source:
            print("   ✅ ProcessorTemplate 正确传递 agent 参数给策略")
        elif "await strategy.execute(self.agent, self.processing_context)" in source:
            print("   ✅ ProcessorTemplate 正确传递 agent 参数给策略 (async)")
        else:
            print("   ❌ ProcessorTemplate 未正确传递 agent 参数")
            return False

        return True

    except Exception as e:
        print(f"   ❌ 框架集成测试失败: {e}")
        return False


def run_refactor_tests():
    """运行重构测试"""
    print("🚀 Agent 参数重构测试")
    print("=" * 50)

    tests = [
        ("策略接口", test_strategy_interface),
        ("HostProcessor 策略", test_host_processor_strategies),
        ("依赖声明", test_dependency_declarations),
        ("框架集成", test_framework_integration),
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        print(f"\n📋 {test_name}:")
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ {test_name} 异常: {e}")
            failed += 1

    print("\n" + "=" * 50)
    print(f"🎯 测试结果:")
    print(f"   ✅ 通过: {passed}")
    print(f"   ❌ 失败: {failed}")
    print(f"   📊 成功率: {passed/(passed+failed)*100:.1f}%")

    if failed == 0:
        print("\n🎉 所有测试都通过了！Agent 参数重构成功。")
        print("\n💡 重构优势:")
        print("   🎯 直接访问 agent，无需从 context 获取")
        print("   🔧 更清晰的依赖关系")
        print("   🛡️  更好的类型检查支持")
        print("   📄 更简洁的策略实现")
        return True
    else:
        print(f"\n⚠️  有 {failed} 个测试失败。")
        return False


if __name__ == "__main__":
    success = run_refactor_tests()
    sys.exit(0 if success else 1)
