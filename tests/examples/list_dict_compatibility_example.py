#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
List/Dict 兼容性示例

展示 TaskConstellationSchema 如何支持 tasks 和 dependencies 的 List 和 Dict 格式。
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from ufo.galaxy.agents.schema import (
    TaskStarSchema,
    TaskStarLineSchema,
    TaskConstellationSchema,
)
import json


def example_list_format():
    """示例：使用 List 格式创建星座"""
    print("🎯 使用 List 格式创建星座")
    print("=" * 50)

    # 创建任务列表
    tasks = [
        {"name": "数据收集", "description": "收集训练数据", "priority": "HIGH"},
        {"name": "数据预处理", "description": "清理和转换数据"},
        {"name": "模型训练", "description": "训练机器学习模型", "priority": "CRITICAL"},
    ]

    # 创建依赖关系列表
    dependencies = [
        {
            "from_task_id": "task_001",  # 数据收集
            "to_task_id": "task_002",  # 数据预处理
            "condition_description": "数据收集完成后开始预处理",
        },
        {
            "from_task_id": "task_002",  # 数据预处理
            "to_task_id": "task_003",  # 模型训练
            "condition_description": "预处理完成后开始训练",
        },
    ]

    # 使用 List 格式创建星座
    constellation = TaskConstellationSchema(
        name="机器学习流水线", tasks=tasks, dependencies=dependencies
    )

    print(f"✅ 星座创建成功: {constellation.name}")
    print(f"   - 星座 ID: {constellation.constellation_id}")
    print(f"   - 任务数量: {len(constellation.tasks)}")
    print(f"   - 依赖数量: {len(constellation.dependencies)}")

    # 显示自动生成的 ID
    print("\n📝 自动生成的任务 ID:")
    for task_id, task in constellation.tasks.items():
        print(f"   - {task.name}: {task.task_id}")

    print("\n🔗 自动生成的依赖 ID:")
    for dep_id, dep in constellation.dependencies.items():
        print(f"   - {dep_id}: {dep.from_task_id} → {dep.to_task_id}")

    return constellation


def example_dict_format():
    """示例：使用传统的 Dict 格式创建星座"""
    print("\n🎯 使用 Dict 格式创建星座")
    print("=" * 50)

    # 手动创建任务
    task1 = TaskStarSchema(
        task_id="collect_data", name="数据收集", description="从各种来源收集数据"
    )

    task2 = TaskStarSchema(
        task_id="analyze_data", name="数据分析", description="分析收集到的数据"
    )

    # 创建任务字典
    tasks = {"collect_data": task1, "analyze_data": task2}

    # 创建依赖关系
    dependency = TaskStarLineSchema(
        line_id="data_flow",
        from_task_id="collect_data",
        to_task_id="analyze_data",
        condition_description="数据收集完成",
    )

    dependencies = {"data_flow": dependency}

    # 创建星座
    constellation = TaskConstellationSchema(
        name="数据分析项目", tasks=tasks, dependencies=dependencies
    )

    print(f"✅ 星座创建成功: {constellation.name}")
    print(f"   - 星座 ID: {constellation.constellation_id}")
    print(f"   - 任务 IDs: {list(constellation.tasks.keys())}")
    print(f"   - 依赖 IDs: {list(constellation.dependencies.keys())}")

    return constellation


def example_mixed_format():
    """示例：混合使用 List 和 Dict 格式"""
    print("\n🎯 混合格式示例")
    print("=" * 50)

    # List 格式的任务，Dict 格式的依赖
    constellation = TaskConstellationSchema(
        name="混合格式星座",
        tasks=[
            {"name": "任务A", "description": "来自 List"},
            {"name": "任务B", "description": "来自 List"},
        ],
        dependencies={
            "manual_dep": TaskStarLineSchema(
                line_id="manual_dep",
                from_task_id="task_001",
                to_task_id="task_002",
                condition_description="手动创建的依赖",
            )
        },
    )

    print(f"✅ 混合格式星座: {constellation.name}")
    print(f"   - Tasks 类型: {type(constellation.tasks).__name__}")
    print(f"   - Dependencies 类型: {type(constellation.dependencies).__name__}")

    return constellation


def example_format_conversion():
    """示例：格式转换方法"""
    print("\n🎯 格式转换方法示例")
    print("=" * 50)

    # 使用 List 格式创建
    constellation = TaskConstellationSchema(
        name="转换示例星座",
        tasks=[
            {"name": "Web开发", "description": "前端开发"},
            {"name": "API开发", "description": "后端API"},
            {"name": "测试", "description": "质量保证"},
        ],
        dependencies=[
            {"from_task_id": "task_001", "to_task_id": "task_002"},
            {"from_task_id": "task_002", "to_task_id": "task_003"},
        ],
    )

    print(f"✅ 原始格式（内部存储为 Dict）:")
    print(f"   - 任务数: {len(constellation.tasks)}")
    print(f"   - 依赖数: {len(constellation.dependencies)}")

    # 转换为 List 格式
    tasks_as_list = constellation.get_tasks_as_list()
    deps_as_list = constellation.get_dependencies_as_list()

    print(f"\n📋 转换为 List 格式:")
    print(f"   - 任务列表长度: {len(tasks_as_list)}")
    print(f"   - 依赖列表长度: {len(deps_as_list)}")

    # 导出为包含 List 的字典
    dict_with_lists = constellation.to_dict_with_lists()

    print(f"\n📤 导出为 List 格式字典:")
    print(f"   - Tasks 类型: {type(dict_with_lists['tasks']).__name__}")
    print(f"   - Dependencies 类型: {type(dict_with_lists['dependencies']).__name__}")

    return constellation, dict_with_lists


def example_json_compatibility():
    """示例：JSON 序列化兼容性"""
    print("\n🎯 JSON 序列化兼容性")
    print("=" * 50)

    # 创建星座
    constellation = TaskConstellationSchema(
        name="JSON兼容性测试",
        tasks=[
            {"name": "前期准备", "description": "项目准备工作"},
            {"name": "执行阶段", "description": "主要工作"},
            {"name": "收尾阶段", "description": "完成和总结"},
        ],
        dependencies=[
            {"from_task_id": "task_001", "to_task_id": "task_002"},
            {"from_task_id": "task_002", "to_task_id": "task_003"},
        ],
    )

    # 方式1: 默认 Dict 格式 JSON
    dict_json = constellation.model_dump_json(indent=2)
    print(f"✅ Dict 格式 JSON 长度: {len(dict_json)} 字符")

    # 方式2: List 格式 JSON
    list_format = constellation.to_dict_with_lists()
    list_json = json.dumps(list_format, indent=2)
    print(f"✅ List 格式 JSON 长度: {len(list_json)} 字符")

    # 验证两种格式都能正确加载
    restored_from_dict = TaskConstellationSchema.model_validate_json(dict_json)
    restored_from_list = TaskConstellationSchema(**json.loads(list_json))

    print(f"\n🔄 恢复验证:")
    print(f"   - 从 Dict JSON 恢复: ✅ {restored_from_dict.name}")
    print(f"   - 从 List JSON 恢复: ✅ {restored_from_list.name}")
    print(
        f"   - 任务数量一致: ✅ {len(restored_from_dict.tasks) == len(restored_from_list.tasks)}"
    )

    # 保存示例 JSON 文件
    with open("list_format_example.json", "w", encoding="utf-8") as f:
        f.write(list_json)

    with open("dict_format_example.json", "w", encoding="utf-8") as f:
        f.write(dict_json)

    print(f"\n💾 已保存示例文件:")
    print(f"   - list_format_example.json")
    print(f"   - dict_format_example.json")

    return constellation


def main():
    """运行所有示例"""
    print("🎯 TaskConstellationSchema List/Dict 兼容性演示")
    print("=" * 60)

    try:
        # 运行各种示例
        constellation1 = example_list_format()
        constellation2 = example_dict_format()
        constellation3 = example_mixed_format()
        constellation4, dict_with_lists = example_format_conversion()
        constellation5 = example_json_compatibility()

        print("\n" + "=" * 60)
        print("🎉 所有示例运行完成！")

        print("\n💡 主要特性:")
        print("   📋 支持 List 格式输入，自动转换为 Dict 存储")
        print("   📚 保持传统 Dict 格式的完全兼容性")
        print("   🔄 提供 List ↔ Dict 格式转换方法")
        print("   🌐 支持两种格式的 JSON 序列化/反序列化")
        print("   🆔 在 List 格式中自动生成缺失的 ID")

        print("\n📊 演示统计:")
        print(f"   • 创建了 5 个不同类型的星座")
        print("   • 展示了 List、Dict 和混合格式")
        print("   • 验证了格式转换和 JSON 兼容性")
        print("   • 生成了示例 JSON 文件")

        return True

    except Exception as e:
        print(f"\n❌ 示例运行失败: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
