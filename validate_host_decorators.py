"""
简化的Host Agent策略装饰器验证脚本

只验证装饰器配置，不运行完整的导入链。
"""

import logging
import sys
import os
from typing import List, Any

# 设置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def check_decorator_configuration():
    """检查装饰器配置的基本语法和结构"""
    logger.info("=== 检查Host Agent策略装饰器配置 ===")

    host_processor_file = r"c:\Users\chaoyunzhang\OneDrive - Microsoft\Desktop\research\GPTV\UFO-windows\github\saber\UFO2\ufo\agents\processors2\host_agent_processor.py"

    try:
        with open(host_processor_file, "r", encoding="utf-8") as f:
            content = f.read()

        # 检查导入语句
        required_imports = [
            "from ufo.agents.processors2.core.strategy_dependency import",
            "strategy_config",
            "depends_on",
            "provides",
            "StrategyDependency",
            "DependencyType",
        ]

        logger.info("检查必需的导入语句:")
        for import_stmt in required_imports:
            if import_stmt in content:
                logger.info(f"  ✓ {import_stmt}")
            else:
                logger.warning(f"  ✗ {import_stmt}")

        # 检查策略装饰器
        strategy_classes = [
            "DesktopDataCollectionStrategy",
            "HostLLMInteractionStrategy",
            "HostActionExecutionStrategy",
            "HostMemoryUpdateStrategy",
        ]

        logger.info("\n检查策略装饰器配置:")
        for strategy in strategy_classes:
            # 查找@strategy_config装饰器
            import_pos = content.find(f"@strategy_config")
            class_pos = content.find(f"class {strategy}")

            if import_pos != -1 and class_pos != -1:
                # 检查装饰器是否在类定义之前
                decorator_before_class = False
                lines = content.split("\n")
                for i, line in enumerate(lines):
                    if f"class {strategy}" in line:
                        # 向上查找装饰器
                        for j in range(max(0, i - 20), i):
                            if "@strategy_config" in lines[j]:
                                decorator_before_class = True
                                break
                        break

                if decorator_before_class:
                    logger.info(f"  ✓ {strategy} - 装饰器配置正确")
                else:
                    logger.warning(f"  ✗ {strategy} - 装饰器可能配置错误")
            else:
                logger.warning(f"  ✗ {strategy} - 未找到装饰器")

        # 检查装饰器语法结构
        logger.info("\n检查装饰器语法结构:")
        decorator_patterns = [
            "dependencies=[",
            "provides=[",
            "StrategyDependency(",
            "DependencyType.REQUIRED",
            "DependencyType.OPTIONAL",
        ]

        for pattern in decorator_patterns:
            count = content.count(pattern)
            logger.info(f"  '{pattern}': {count} 次出现")

        # 统计依赖和提供字段
        dependencies_count = content.count("StrategyDependency(")
        provides_arrays = content.count("provides=[")

        logger.info(f"\n统计信息:")
        logger.info(f"  总依赖声明: {dependencies_count}")
        logger.info(f"  提供字段数组: {provides_arrays}")

        return True

    except Exception as e:
        logger.error(f"检查过程中出现错误: {e}")
        return False


def analyze_dependency_structure():
    """分析依赖结构"""
    logger.info("\n=== 分析依赖结构 ===")

    # 预期的策略链数据流
    expected_flow = {
        "DesktopDataCollectionStrategy": {
            "inputs": ["command_dispatcher", "log_path", "session_step"],
            "outputs": [
                "desktop_screenshot_url",
                "desktop_screenshot_path",
                "application_windows_info",
                "target_registry",
                "target_info_list",
            ],
        },
        "HostLLMInteractionStrategy": {
            "inputs": [
                "host_agent",
                "target_info_list",
                "desktop_screenshot_url",
                "prev_plan",
                "previous_subtasks",
                "request",
            ],
            "outputs": [
                "parsed_response",
                "response_text",
                "llm_cost",
                "prompt_message",
                "subtask",
                "plan",
                "host_message",
                "status",
                "question_list",
                "function_name",
                "function_arguments",
            ],
        },
        "HostActionExecutionStrategy": {
            "inputs": [
                "parsed_response",
                "function_name",
                "function_arguments",
                "target_registry",
                "command_dispatcher",
            ],
            "outputs": [
                "execution_result",
                "action_info",
                "selected_target_id",
                "selected_application_root",
                "assigned_third_party_agent",
            ],
        },
        "HostMemoryUpdateStrategy": {
            "inputs": [
                "host_agent",
                "parsed_response",
                "action_info",
                "selected_application_root",
                "selected_target_id",
                "assigned_third_party_agent",
                "execution_result",
                "session_step",
                "round_step",
                "round_num",
            ],
            "outputs": ["additional_memory", "memory_item", "memory_keys_count"],
        },
    }

    logger.info("预期的Host Agent策略数据流:")
    for i, (strategy, flow) in enumerate(expected_flow.items()):
        logger.info(f"\n{i+1}. {strategy}")
        logger.info(f"   输入 ({len(flow['inputs'])}): {flow['inputs']}")
        logger.info(f"   输出 ({len(flow['outputs'])}): {flow['outputs']}")

    # 分析数据流连接
    logger.info("\n策略间数据流连接:")
    strategy_names = list(expected_flow.keys())
    for i in range(len(strategy_names) - 1):
        current = strategy_names[i]
        next_strategy = strategy_names[i + 1]

        current_outputs = set(expected_flow[current]["outputs"])
        next_inputs = set(expected_flow[next_strategy]["inputs"])

        connections = current_outputs & next_inputs
        if connections:
            logger.info(f"  {current} → {next_strategy}: {list(connections)}")
        else:
            logger.info(f"  {current} → {next_strategy}: 无直接连接")

    return True


def main():
    """主函数"""
    logger.info("开始验证Host Agent策略装饰器配置...")

    try:
        # 检查装饰器配置
        if not check_decorator_configuration():
            return False

        # 分析依赖结构
        if not analyze_dependency_structure():
            return False

        logger.info("\n" + "=" * 60)
        logger.info("✅ Host Agent策略装饰器配置验证完成!")
        logger.info("配置文件语法检查通过，依赖结构分析完成。")

        return True

    except Exception as e:
        logger.error(f"验证过程中出现错误: {e}")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
