#!/usr/bin/env python3
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
TaskConstellation Editor 使用示例

展示基于命令模式的星座编辑器的核心功能。
"""

import sys
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from galaxy.constellation.editor import ConstellationEditor
from galaxy.constellation.enums import TaskPriority, DependencyType


def example_basic_operations():
    """基本操作示例"""
    print("🌟 基本操作示例")
    print("=" * 50)

    # 创建编辑器
    editor = ConstellationEditor()

    # 创建任务
    print("📝 创建任务...")
    task1 = editor.create_and_add_task("login", "用户登录", priority=TaskPriority.HIGH)
    task2 = editor.create_and_add_task(
        "fetch_data", "获取数据", priority=TaskPriority.MEDIUM
    )
    task3 = editor.create_and_add_task(
        "process_data", "处理数据", priority=TaskPriority.MEDIUM
    )
    task4 = editor.create_and_add_task(
        "display_result", "显示结果", priority=TaskPriority.LOW
    )

    print(f"✅ 创建了 {len(editor.list_tasks())} 个任务")

    # 添加依赖关系
    print("\n🔗 添加依赖关系...")
    dep1 = editor.create_and_add_dependency("login", "fetch_data", "UNCONDITIONAL")
    dep2 = editor.create_and_add_dependency(
        "fetch_data", "process_data", "SUCCESS_ONLY"
    )
    dep3 = editor.create_and_add_dependency(
        "process_data", "display_result", "UNCONDITIONAL"
    )

    print(f"✅ 创建了 {len(editor.list_dependencies())} 个依赖关系")

    # 验证星座结构
    print("\n🔍 验证星座结构...")
    is_valid, errors = editor.validate_constellation()
    if is_valid:
        print("✅ 星座结构有效")
        topo_order = editor.get_topological_order()
        print(f"📋 执行顺序: {' -> '.join(topo_order)}")
    else:
        print(f"❌ 星座结构无效: {errors}")

    return editor


def example_undo_redo():
    """撤销/重做示例"""
    print("\n🔄 撤销/重做示例")
    print("=" * 50)

    editor = ConstellationEditor()

    # 执行一系列操作
    print("📝 执行操作...")
    editor.create_and_add_task("task1", "任务1")
    editor.create_and_add_task("task2", "任务2")
    editor.create_and_add_dependency("task1", "task2")

    print(f"当前任务数: {len(editor.list_tasks())}")
    print(f"当前依赖数: {len(editor.list_dependencies())}")

    # 撤销操作
    print("\n⏪ 撤销操作...")
    while editor.can_undo():
        undo_desc = editor.get_undo_description()
        print(f"撤销: {undo_desc}")
        editor.undo()
        print(
            f"  -> 任务数: {len(editor.list_tasks())}, 依赖数: {len(editor.list_dependencies())}"
        )

    # 重做操作
    print("\n⏩ 重做操作...")
    while editor.can_redo():
        redo_desc = editor.get_redo_description()
        print(f"重做: {redo_desc}")
        editor.redo()
        print(
            f"  -> 任务数: {len(editor.list_tasks())}, 依赖数: {len(editor.list_dependencies())}"
        )


def example_bulk_operations():
    """批量操作示例"""
    print("\n📦 批量操作示例")
    print("=" * 50)

    editor = ConstellationEditor()

    # 准备批量数据
    tasks = [
        {
            "task_id": "init",
            "description": "系统初始化",
            "priority": TaskPriority.CRITICAL.value,
        },
        {
            "task_id": "load_config",
            "description": "加载配置",
            "priority": TaskPriority.HIGH.value,
        },
        {
            "task_id": "start_services",
            "description": "启动服务",
            "priority": TaskPriority.HIGH.value,
        },
        {
            "task_id": "health_check",
            "description": "健康检查",
            "priority": TaskPriority.MEDIUM.value,
        },
        {
            "task_id": "ready",
            "description": "系统就绪",
            "priority": TaskPriority.LOW.value,
        },
    ]

    dependencies = [
        {
            "from_task_id": "init",
            "to_task_id": "load_config",
            "dependency_type": DependencyType.UNCONDITIONAL.value,
        },
        {
            "from_task_id": "load_config",
            "to_task_id": "start_services",
            "dependency_type": DependencyType.SUCCESS_ONLY.value,
        },
        {
            "from_task_id": "start_services",
            "to_task_id": "health_check",
            "dependency_type": DependencyType.UNCONDITIONAL.value,
        },
        {
            "from_task_id": "health_check",
            "to_task_id": "ready",
            "dependency_type": DependencyType.SUCCESS_ONLY.value,
        },
    ]

    # 批量构建
    print("🏗️ 批量构建星座...")
    editor.build_from_tasks_and_dependencies(
        tasks, dependencies, metadata={"purpose": "system_startup", "version": "1.0"}
    )

    print(
        f"✅ 批量创建: {len(editor.list_tasks())} 个任务, {len(editor.list_dependencies())} 个依赖"
    )

    # 获取统计信息
    stats = editor.get_statistics()
    print(f"📊 统计信息:")
    print(f"  - 总任务数: {stats['total_tasks']}")
    print(f"  - 总依赖数: {stats['total_dependencies']}")
    print(f"  - 编辑器执行次数: {stats['editor_execution_count']}")

    return editor


def example_file_operations():
    """文件操作示例"""
    print("\n💾 文件操作示例")
    print("=" * 50)

    # 创建并保存星座
    editor1 = ConstellationEditor()
    editor1.create_and_add_task("web_request", "发送网络请求")
    editor1.create_and_add_task("parse_response", "解析响应")
    editor1.create_and_add_dependency("web_request", "parse_response")

    # 保存到文件
    filename = "example_constellation.json"
    print(f"💾 保存星座到 {filename}...")
    editor1.save_constellation(filename)
    print("✅ 保存成功")

    # 从文件加载
    print(f"📂 从 {filename} 加载星座...")
    editor2 = ConstellationEditor()
    editor2.load_constellation(filename)
    print(
        f"✅ 加载成功: {len(editor2.list_tasks())} 个任务, {len(editor2.list_dependencies())} 个依赖"
    )

    # 验证内容一致性
    original_stats = editor1.get_statistics()
    loaded_stats = editor2.get_statistics()

    if (
        original_stats["total_tasks"] == loaded_stats["total_tasks"]
        and original_stats["total_dependencies"] == loaded_stats["total_dependencies"]
    ):
        print("✅ 文件操作验证通过")
    else:
        print("❌ 文件操作验证失败")

    # 清理文件
    import os

    if os.path.exists(filename):
        os.remove(filename)
        print(f"🗑️ 清理临时文件 {filename}")


def example_advanced_features():
    """高级功能示例"""
    print("\n🚀 高级功能示例")
    print("=" * 50)

    # 创建复杂星座
    editor = ConstellationEditor()

    # 观察者模式
    def operation_observer(editor, command, result):
        print(f"  📢 操作通知: {command}")

    print("👁️ 添加观察者...")
    editor.add_observer(operation_observer)

    # 创建任务（会触发观察者）
    print("📝 创建任务（带观察者）...")
    editor.create_and_add_task("observed_task", "被观察的任务")

    # 移除观察者
    editor.remove_observer(operation_observer)
    print("👁️ 移除观察者")

    # 子图创建
    print("\n📊 创建复杂星座...")
    tasks = ["A", "B", "C", "D", "E"]
    for task_id in tasks:
        editor.create_and_add_task(task_id, f"任务 {task_id}")

    # 创建复杂依赖结构
    dependencies = [("A", "B"), ("A", "C"), ("B", "D"), ("C", "D"), ("D", "E")]
    for from_task, to_task in dependencies:
        editor.create_and_add_dependency(from_task, to_task)

    print(f"✅ 创建了包含 {len(editor.list_tasks())} 个任务的复杂星座")

    # 创建子图
    print("\n🎯 提取子图...")
    subgraph = editor.create_subgraph(["A", "B", "D"])
    print(
        f"✅ 子图包含 {len(subgraph.list_tasks())} 个任务, {len(subgraph.list_dependencies())} 个依赖"
    )

    # 获取就绪任务
    ready_tasks = editor.get_ready_tasks()
    print(f"🚦 就绪任务: {[t.task_id for t in ready_tasks]}")


def main():
    """主函数"""
    print("🌟 TaskConstellation Editor 命令模式示例")
    print("=" * 80)

    try:
        # 运行各个示例
        example_basic_operations()
        example_undo_redo()
        example_bulk_operations()
        example_file_operations()
        example_advanced_features()

        print("\n🎉 所有示例运行完成！")
        print("✅ TaskConstellation Editor 命令模式功能验证成功")

    except Exception as e:
        print(f"\n❌ 示例运行失败: {e}")
        import traceback

        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
