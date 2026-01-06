#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test for List/Dict compatibility in TaskConstellationSchema.

This test verifies that tasks and dependencies can be provided as either
List or Dict formats and are properly converted and validated.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from galaxy.agents.schema import (
    TaskStarSchema,
    TaskStarLineSchema,
    TaskConstellationSchema,
)
import json


def test_tasks_and_dependencies_as_lists():
    """测试使用 List 格式的 tasks 和 dependencies"""
    print("🧪 测试 List 格式的 tasks 和 dependencies")

    # 准备测试数据 - 使用 List 格式
    task_list = [
        {
            "task_id": "task_001",
            "name": "第一个任务",
            "description": "这是第一个任务的描述",
        },
        {
            "task_id": "task_002",
            "name": "第二个任务",
            "description": "这是第二个任务的描述",
        },
        {
            # 没有 task_id，应该自动生成
            "name": "第三个任务",
            "description": "这个任务没有预设 ID",
        },
    ]

    dependency_list = [
        {
            "line_id": "dep_001",
            "from_task_id": "task_001",
            "to_task_id": "task_002",
            "condition_description": "第一个依赖关系",
        },
        {
            # 没有 line_id，应该自动生成
            "from_task_id": "task_002",
            "to_task_id": "task_003",
            "condition_description": "第二个依赖关系，没有预设 ID",
        },
    ]

    # 创建 constellation，使用 List 格式
    constellation_data = {
        "name": "List格式测试星座",
        "tasks": task_list,
        "dependencies": dependency_list,
    }

    constellation = TaskConstellationSchema(**constellation_data)

    print(f"✅ 星座创建成功: {constellation.name}")
    print(f"   - 星座 ID: {constellation.constellation_id}")
    print(f"   - 任务数量: {len(constellation.tasks)}")
    print(f"   - 依赖数量: {len(constellation.dependencies)}")

    # 验证 tasks 被转换为 Dict 格式
    assert isinstance(constellation.tasks, dict), "Tasks 应该被转换为 Dict 格式"

    # 验证 dependencies 被转换为 Dict 格式
    assert isinstance(
        constellation.dependencies, dict
    ), "Dependencies 应该被转换为 Dict 格式"

    # 检查任务 ID
    task_ids = list(constellation.tasks.keys())
    print(f"   - 任务 IDs: {task_ids}")

    # 检查依赖 ID
    dep_ids = list(constellation.dependencies.keys())
    print(f"   - 依赖 IDs: {dep_ids}")

    # 验证自动生成的 ID
    auto_generated_tasks = [
        task for task in constellation.tasks.values() if task.name == "第三个任务"
    ]
    assert len(auto_generated_tasks) == 1, "应该有一个自动生成 ID 的任务"
    print(f"   - 自动生成的任务 ID: {auto_generated_tasks[0].task_id}")

    return constellation


def test_tasks_and_dependencies_as_dicts():
    """测试使用 Dict 格式的 tasks 和 dependencies（传统格式）"""
    print("\n🧪 测试 Dict 格式的 tasks 和 dependencies")

    # 准备测试数据 - 使用 Dict 格式
    task_dict = {
        "task_001": TaskStarSchema(
            task_id="task_001",
            name="Dict格式任务1",
            description="使用Dict格式的第一个任务",
        ),
        "task_002": TaskStarSchema(
            task_id="task_002",
            name="Dict格式任务2",
            description="使用Dict格式的第二个任务",
        ),
    }

    dependency_dict = {
        "dep_001": TaskStarLineSchema(
            line_id="dep_001",
            from_task_id="task_001",
            to_task_id="task_002",
            condition_description="Dict格式的依赖关系",
        )
    }

    # 创建 constellation，使用 Dict 格式
    constellation = TaskConstellationSchema(
        name="Dict格式测试星座", tasks=task_dict, dependencies=dependency_dict
    )

    print(f"✅ 星座创建成功: {constellation.name}")
    print(f"   - 星座 ID: {constellation.constellation_id}")
    print(f"   - 任务数量: {len(constellation.tasks)}")
    print(f"   - 依赖数量: {len(constellation.dependencies)}")

    # 验证格式保持为 Dict
    assert isinstance(constellation.tasks, dict), "Tasks 应该保持 Dict 格式"
    assert isinstance(
        constellation.dependencies, dict
    ), "Dependencies 应该保持 Dict 格式"

    return constellation


def test_mixed_format_compatibility():
    """测试混合格式兼容性"""
    print("\n🧪 测试混合格式兼容性")

    # List 格式的 tasks，Dict 格式的 dependencies
    constellation1 = TaskConstellationSchema(
        name="混合格式星座1",
        tasks=[
            {"name": "List任务1", "description": "来自List"},
            {"name": "List任务2", "description": "来自List"},
        ],
        dependencies={
            "manual_dep": TaskStarLineSchema(
                line_id="manual_dep", from_task_id="task_001", to_task_id="task_002"
            )
        },
    )

    print(
        f"✅ 混合格式1创建成功: tasks={type(constellation1.tasks).__name__}, dependencies={type(constellation1.dependencies).__name__}"
    )

    # Dict 格式的 tasks，List 格式的 dependencies
    constellation2 = TaskConstellationSchema(
        name="混合格式星座2",
        tasks={
            "manual_task": TaskStarSchema(
                task_id="manual_task", name="Dict任务", description="来自Dict"
            )
        },
        dependencies=[
            {
                "from_task_id": "manual_task",
                "to_task_id": "some_other_task",
                "condition_description": "来自List的依赖",
            }
        ],
    )

    print(
        f"✅ 混合格式2创建成功: tasks={type(constellation2.tasks).__name__}, dependencies={type(constellation2.dependencies).__name__}"
    )

    return constellation1, constellation2


def test_conversion_methods():
    """测试转换方法"""
    print("\n🧪 测试转换方法")

    # 创建一个星座
    constellation = TaskConstellationSchema(
        name="转换测试星座",
        tasks=[
            {"name": "任务A", "description": "描述A"},
            {"name": "任务B", "description": "描述B"},
            {"name": "任务C", "description": "描述C"},
        ],
        dependencies=[
            {"from_task_id": "task_001", "to_task_id": "task_002"},
            {"from_task_id": "task_002", "to_task_id": "task_003"},
        ],
    )

    # 测试 get_tasks_as_list
    tasks_list = constellation.get_tasks_as_list()
    print(f"✅ 获取任务列表: {len(tasks_list)} 个任务")
    assert len(tasks_list) == 3, "应该有3个任务"
    assert all(
        isinstance(task, TaskStarSchema) for task in tasks_list
    ), "所有项都应该是TaskStarSchema"

    # 测试 get_dependencies_as_list
    deps_list = constellation.get_dependencies_as_list()
    print(f"✅ 获取依赖列表: {len(deps_list)} 个依赖")
    assert len(deps_list) == 2, "应该有2个依赖"
    assert all(
        isinstance(dep, TaskStarLineSchema) for dep in deps_list
    ), "所有项都应该是TaskStarLineSchema"

    # 测试 to_dict_with_lists
    data_with_lists = constellation.to_dict_with_lists()
    print(
        f"✅ 导出为列表格式: tasks={type(data_with_lists['tasks']).__name__}, dependencies={type(data_with_lists['dependencies']).__name__}"
    )
    assert isinstance(data_with_lists["tasks"], list), "导出的tasks应该是list"
    assert isinstance(
        data_with_lists["dependencies"], list
    ), "导出的dependencies应该是list"

    return constellation


def test_json_serialization():
    """测试 JSON 序列化兼容性"""
    print("\n🧪 测试 JSON 序列化兼容性")

    # 创建星座（使用List格式输入）
    constellation = TaskConstellationSchema(
        name="JSON测试星座",
        tasks=[
            {"name": "JSON任务1", "description": "JSON描述1"},
            {"name": "JSON任务2", "description": "JSON描述2"},
        ],
        dependencies=[
            {
                "from_task_id": "task_001",
                "to_task_id": "task_002",
                "condition_description": "JSON依赖",
            }
        ],
    )

    # 序列化为 JSON（默认Dict格式）
    json_dict_format = constellation.model_dump_json(indent=2)
    print(f"✅ Dict格式JSON长度: {len(json_dict_format)} 字符")

    # 序列化为 JSON（List格式）
    json_list_format = json.dumps(constellation.to_dict_with_lists(), indent=2)
    print(f"✅ List格式JSON长度: {len(json_list_format)} 字符")

    # 验证两种格式都能正确反序列化
    # Dict格式反序列化
    restored_from_dict = TaskConstellationSchema.model_validate_json(json_dict_format)
    print(f"✅ 从Dict格式JSON恢复: {restored_from_dict.name}")

    # List格式反序列化
    list_data = json.loads(json_list_format)
    restored_from_list = TaskConstellationSchema(**list_data)
    print(f"✅ 从List格式JSON恢复: {restored_from_list.name}")

    # 验证内容一致性
    assert restored_from_dict.name == restored_from_list.name, "名称应该一致"
    assert len(restored_from_dict.tasks) == len(
        restored_from_list.tasks
    ), "任务数量应该一致"
    assert len(restored_from_dict.dependencies) == len(
        restored_from_list.dependencies
    ), "依赖数量应该一致"

    return constellation


def main():
    """运行所有测试"""
    print("🎯 TaskConstellationSchema List/Dict 兼容性测试")
    print("=" * 60)

    try:
        # 运行各项测试
        constellation1 = test_tasks_and_dependencies_as_lists()
        constellation2 = test_tasks_and_dependencies_as_dicts()
        mixed1, mixed2 = test_mixed_format_compatibility()
        constellation3 = test_conversion_methods()
        constellation4 = test_json_serialization()

        print("\n" + "=" * 60)
        print("🎉 所有测试通过！")

        print("\n💡 主要特性验证:")
        print("   ✅ List 格式的 tasks 和 dependencies 自动转换为 Dict")
        print("   ✅ Dict 格式保持不变")
        print("   ✅ 混合格式正确处理")
        print("   ✅ 自动 ID 生成在 List 格式中正常工作")
        print("   ✅ 转换方法正确工作")
        print("   ✅ JSON 序列化/反序列化兼容")

        print("\n📊 测试统计:")
        print(
            f"   • 创建了 {len([constellation1, constellation2, mixed1, mixed2, constellation3, constellation4])} 个测试星座"
        )
        print("   • 验证了 List ↔ Dict 转换")
        print("   • 测试了混合格式兼容性")
        print("   • 验证了 JSON 序列化兼容性")

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback

        traceback.print_exc()
        return False

    return True


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
