#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Example demonstrating automatic ID assignment in BaseModel schemas.

This example shows how constellation_id, task_id, and line_id are automatically
generated when not provided, and how uniqueness is enforced within constellation contexts.
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


def example_basic_auto_id():
    """示例：基本自动 ID 分配"""
    print("🚀 基本自动 ID 分配示例")
    print("=" * 60)

    # 创建任务时不提供 task_id，系统自动分配
    task1 = TaskStarSchema(name="数据提取任务", description="从数据库中提取用户数据")

    task2 = TaskStarSchema(name="数据处理任务", description="清洗和格式化提取的数据")

    task3 = TaskStarSchema(
        name="数据分析任务", description="分析处理后的数据并生成报告"
    )

    print(f"✅ 自动生成的任务 ID:")
    print(f"   - 任务1: {task1.task_id}")
    print(f"   - 任务2: {task2.task_id}")
    print(f"   - 任务3: {task3.task_id}")

    # 创建依赖关系时不提供 line_id，系统自动分配
    dep1 = TaskStarLineSchema(
        from_task_id=task1.task_id,
        to_task_id=task2.task_id,
        dependency_type="SUCCESS_ONLY",
    )

    dep2 = TaskStarLineSchema(
        from_task_id=task2.task_id,
        to_task_id=task3.task_id,
        dependency_type="UNCONDITIONAL",
    )

    print(f"\n✅ 自动生成的依赖 ID:")
    print(f"   - 依赖1: {dep1.line_id}")
    print(f"   - 依赖2: {dep2.line_id}")

    # 创建星座时不提供 constellation_id，系统自动分配
    constellation = TaskConstellationSchema(
        name="数据处理流水线",
        tasks={task1.task_id: task1, task2.task_id: task2, task3.task_id: task3},
        dependencies={dep1.line_id: dep1, dep2.line_id: dep2},
    )

    print(f"\n✅ 自动生成的星座 ID: {constellation.constellation_id}")

    return constellation


def example_mixed_ids():
    """示例：混合 ID 模式（部分手动，部分自动）"""
    print("\n🎯 混合 ID 分配示例")
    print("=" * 60)

    # 手动指定一些 ID，自动生成其他 ID
    manual_task = TaskStarSchema(
        task_id="manual_extraction_task",  # 手动指定
        name="手动指定 ID 的任务",
        description="这个任务使用手动指定的 ID",
    )

    auto_task = TaskStarSchema(
        # 不指定 task_id，系统自动生成
        name="自动生成 ID 的任务",
        description="这个任务使用自动生成的 ID",
    )

    print(f"✅ 混合 ID 模式:")
    print(f"   - 手动任务 ID: {manual_task.task_id}")
    print(f"   - 自动任务 ID: {auto_task.task_id}")

    # 依赖关系也可以混合
    manual_dep = TaskStarLineSchema(
        line_id="manual_dependency_001",  # 手动指定
        from_task_id=manual_task.task_id,
        to_task_id=auto_task.task_id,
    )

    auto_dep = TaskStarLineSchema(
        # 不指定 line_id，系统自动生成
        from_task_id=auto_task.task_id,
        to_task_id=manual_task.task_id,
        dependency_type="COMPLETION_ONLY",
    )

    print(f"   - 手动依赖 ID: {manual_dep.line_id}")
    print(f"   - 自动依赖 ID: {auto_dep.line_id}")

    # 创建星座
    constellation = TaskConstellationSchema(
        constellation_id="mixed_mode_constellation",  # 手动指定
        name="混合模式星座",
        tasks={manual_task.task_id: manual_task, auto_task.task_id: auto_task},
        dependencies={manual_dep.line_id: manual_dep, auto_dep.line_id: auto_dep},
    )

    print(f"   - 手动星座 ID: {constellation.constellation_id}")

    return constellation


def example_sequential_generation():
    """示例：序列化 ID 生成"""
    print("\n🔢 序列化 ID 生成示例")
    print("=" * 60)

    from ufo.galaxy.agents.schema import IDManager

    # 获取 ID 管理器实例
    id_manager = IDManager()
    constellation_id = "sequential_test"

    # 在同一个星座上下文中生成多个 ID
    task_ids = []
    for i in range(5):
        task_id = id_manager.generate_task_id(constellation_id)
        task_ids.append(task_id)

    line_ids = []
    for i in range(3):
        line_id = id_manager.generate_line_id(constellation_id)
        line_ids.append(line_id)

    print(f"✅ 序列化任务 ID: {task_ids}")
    print(f"✅ 序列化依赖 ID: {line_ids}")

    # 创建任务
    tasks = {}
    for i, task_id in enumerate(task_ids):
        task = TaskStarSchema(
            task_id=task_id,  # 使用预生成的 ID
            name=f"序列任务 {i+1}",
            description=f"这是第 {i+1} 个序列任务",
        )
        tasks[task_id] = task

    # 创建依赖关系
    dependencies = {}
    for i, line_id in enumerate(line_ids):
        from_task = task_ids[i]
        to_task = task_ids[i + 1]

        dep = TaskStarLineSchema(
            line_id=line_id, from_task_id=from_task, to_task_id=to_task
        )
        dependencies[line_id] = dep

    # 创建星座
    constellation = TaskConstellationSchema(
        constellation_id=constellation_id,
        name="序列化测试星座",
        tasks=tasks,
        dependencies=dependencies,
    )

    print(f"✅ 创建了包含 {len(tasks)} 个任务和 {len(dependencies)} 个依赖的星座")

    return constellation


def example_error_handling():
    """示例：错误处理和重复检测"""
    print("\n⚠️ 错误处理示例")
    print("=" * 60)

    # 创建有重复 ID 的任务
    task1 = TaskStarSchema(
        task_id="duplicate_task", name="任务1", description="第一个任务"
    )

    task2 = TaskStarSchema(
        task_id="duplicate_task",  # 重复的 ID
        name="任务2",
        description="第二个任务（重复ID）",
    )

    print(f"✅ 创建了两个任务:")
    print(f"   - 任务1 ID: {task1.task_id}")
    print(f"   - 任务2 ID: {task2.task_id}")

    # 尝试创建包含重复 ID 的星座
    try:
        bad_constellation = TaskConstellationSchema(
            name="错误测试星座",
            tasks={"task1": task1, "task2": task2},  # 这会触发重复 ID 验证错误
        )
        print("❌ 错误：重复 ID 检测失败")
    except ValueError as e:
        print(f"✅ 正确捕获重复 ID 错误: {str(e)[:50]}...")

    # 正确的做法：让系统自动生成唯一 ID
    correct_task1 = TaskStarSchema(
        name="正确任务1", description="使用自动生成 ID 的任务1"
    )

    correct_task2 = TaskStarSchema(
        name="正确任务2", description="使用自动生成 ID 的任务2"
    )

    correct_constellation = TaskConstellationSchema(
        name="正确的星座",
        tasks={
            correct_task1.task_id: correct_task1,
            correct_task2.task_id: correct_task2,
        },
    )

    print(f"✅ 正确创建星座，任务 ID:")
    print(f"   - 任务1: {correct_task1.task_id}")
    print(f"   - 任务2: {correct_task2.task_id}")

    return correct_constellation


def example_json_serialization():
    """示例：JSON 序列化带自动 ID"""
    print("\n💾 JSON 序列化示例")
    print("=" * 60)

    # 创建包含自动生成 ID 的星座
    constellation = TaskConstellationSchema(name="JSON 测试星座")

    # 添加一些任务（自动生成 ID）
    for i in range(3):
        task = TaskStarSchema(
            name=f"JSON 任务 {i+1}", description=f"用于 JSON 序列化测试的任务 {i+1}"
        )
        constellation.tasks[task.task_id] = task

    # 序列化为 JSON
    json_data = constellation.model_dump_json(indent=2)

    print(f"✅ 序列化为 JSON:")
    print(f"   - 星座 ID: {constellation.constellation_id}")
    print(f"   - 任务数量: {len(constellation.tasks)}")
    print(f"   - JSON 大小: {len(json_data)} 字符")

    # 从 JSON 恢复
    loaded_constellation = TaskConstellationSchema.model_validate_json(json_data)

    print(f"✅ 从 JSON 恢复:")
    print(f"   - 星座 ID: {loaded_constellation.constellation_id}")
    print(f"   - 任务数量: {len(loaded_constellation.tasks)}")

    # 保存到文件
    filename = "auto_id_constellation.json"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(json_data)
    print(f"✅ 已保存到: {filename}")

    return loaded_constellation


def main():
    """运行所有示例"""
    print("🎯 自动 ID 分配功能演示")
    print("本演示展示了系统如何自动分配 constellation_id、task_id 和 line_id\n")

    # 运行各种示例
    constellation1 = example_basic_auto_id()
    constellation2 = example_mixed_ids()
    constellation3 = example_sequential_generation()
    constellation4 = example_error_handling()
    constellation5 = example_json_serialization()

    print("\n🎉 所有示例执行完成！")
    print("\n💡 主要特性:")
    print("   • 自动生成唯一 ID（constellation_id, task_id, line_id）")
    print("   • 支持手动指定和自动生成的混合模式")
    print("   • 在星座上下文中保证 ID 唯一性")
    print("   • 序列化 ID 生成（task_001, task_002, ...）")
    print("   • 重复 ID 检测和错误处理")
    print("   • 完全兼容 JSON 序列化/反序列化")

    print(f"\n📊 统计信息:")
    print(f"   • 总共创建了 5 个示例星座")
    print(f"   • 演示了自动 ID 分配的各种场景")
    print(f"   • 验证了错误处理和唯一性检查")


if __name__ == "__main__":
    main()
