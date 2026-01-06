#!/usr/bin/env python3
"""
Comprehensive example demonstrating all the updated features of the
Constellation Editor with:

1. Serializable command parameters (可序列化参数)
2. Command registry with decorators (命令注册器和装饰器)
3. Automatic validation with rollback (自动验证和撤回)
"""

import sys
import os

# Add the UFO2 directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
ufo_path = os.path.dirname(current_dir)
sys.path.insert(0, ufo_path)

from galaxy.constellation.editor.constellation_editor import ConstellationEditor
from galaxy.constellation.editor.command_registry import command_registry
from galaxy.constellation.task_constellation import TaskConstellation


def demo_serializable_parameters():
    """演示可序列化参数功能"""
    print("=== 1. 可序列化参数 (Serializable Parameters) ===")

    constellation = TaskConstellation()
    editor = ConstellationEditor(constellation)

    # 使用字典参数添加任务 (Using dict parameters to add tasks)
    print("\n使用字典参数添加任务:")

    task1_data = {
        "task_id": "serialize_task1",
        "name": "可序列化任务1",
        "description": "这是用字典参数创建的任务",
        "priority": 3,  # HIGH priority
    }

    task2_data = {
        "task_id": "serialize_task2",
        "name": "可序列化任务2",
        "description": "另一个用字典参数创建的任务",
    }

    task1 = editor.add_task(task1_data)
    task2 = editor.add_task(task2_data)

    print(f"   ✓ 添加任务1: {task1.task_id} - {task1.name}")
    print(f"   ✓ 添加任务2: {task2.task_id} - {task2.name}")

    # 使用字典参数添加依赖关系 (Using dict parameters to add dependencies)
    print("\n使用字典参数添加依赖关系:")

    dependency_data = {
        "from_task_id": "serialize_task1",
        "to_task_id": "serialize_task2",
        "dependency_type": "unconditional",
    }

    dependency = editor.add_dependency(dependency_data)
    print(f"   ✓ 添加依赖: {dependency.from_task_id} -> {dependency.to_task_id}")

    return editor


def demo_command_registry():
    """演示命令注册器功能"""
    print("\n=== 2. 命令注册器和装饰器 (Command Registry & Decorators) ===")

    constellation = TaskConstellation()
    editor = ConstellationEditor(constellation)

    # 列出所有注册的命令 (List all registered commands)
    print("\n所有注册的命令:")
    commands = editor.list_available_commands()
    for name, metadata in commands.items():
        print(f"   • {name}: {metadata['description']}")
        print(f"     类别: {metadata['category']}, 可撤销: {metadata['is_undoable']}")

    # 按类别列出命令 (List commands by category)
    print("\n按类别分组:")
    for category in editor.get_command_categories():
        category_commands = editor.list_available_commands(category)
        print(f"   {category}:")
        for name in category_commands.keys():
            print(f"     - {name}")

    # 通过注册器执行命令 (Execute commands via registry)
    print("\n通过注册器执行命令:")

    task_data = {
        "task_id": "registry_demo_task",
        "name": "注册器演示任务",
        "description": "通过命令注册器创建的任务",
    }

    # 使用 execute_command_by_name 方法
    result = editor.execute_command_by_name("add_task", task_data)
    print(f"   ✓ 通过注册器创建任务: {result.task_id}")

    # 获取命令元数据 (Get command metadata)
    metadata = editor.get_command_metadata("add_task")
    print(f"   add_task 元数据: {metadata}")

    return editor


def demo_validation_rollback():
    """演示自动验证和撤回功能"""
    print("\n=== 3. 自动验证和撤回 (Automatic Validation & Rollback) ===")

    constellation = TaskConstellation()
    editor = ConstellationEditor(constellation)

    # 添加一些有效的任务 (Add some valid tasks)
    print("\n添加有效任务:")

    valid_tasks = [
        {
            "task_id": "valid_task_A",
            "name": "有效任务A",
            "description": "这是一个有效的任务",
        },
        {
            "task_id": "valid_task_B",
            "name": "有效任务B",
            "description": "这是另一个有效的任务",
        },
    ]

    for task_data in valid_tasks:
        task = editor.add_task(task_data)
        print(f"   ✓ 添加: {task.task_id}")

    print(
        f"\n当前状态: {len(constellation.tasks)} 个任务, {len(constellation.dependencies)} 个依赖"
    )
    is_valid, errors = constellation.validate_dag()
    print(f"   状态: {'有效' if is_valid else '无效'}")

    # 尝试添加无效依赖 (Try to add invalid dependency)
    print("\n尝试添加无效依赖 (指向不存在的任务):")
    try:
        invalid_dependency = {
            "from_task_id": "valid_task_A",
            "to_task_id": "nonexistent_task",  # 不存在的任务
            "dependency_type": "unconditional",
        }

        editor.add_dependency(invalid_dependency)
        print("   ✗ 意外成功")
    except Exception as e:
        print(f"   ✓ 预期失败: {e}")

    print(
        f"\n失败操作后: {len(constellation.tasks)} 个任务, {len(constellation.dependencies)} 个依赖"
    )
    is_valid, errors = constellation.validate_dag()
    print(f"   状态: {'仍然有效' if is_valid else '已损坏'}")

    # 添加有效依赖 (Add valid dependency)
    print("\n添加有效依赖:")
    try:
        valid_dependency = {
            "from_task_id": "valid_task_A",
            "to_task_id": "valid_task_B",
            "dependency_type": "unconditional",
        }

        dependency = editor.add_dependency(valid_dependency)
        print(f"   ✓ 成功添加: {dependency.from_task_id} -> {dependency.to_task_id}")
    except Exception as e:
        print(f"   ✗ 意外失败: {e}")

    print(
        f"\n最终状态: {len(constellation.tasks)} 个任务, {len(constellation.dependencies)} 个依赖"
    )
    is_valid, errors = constellation.validate_dag()
    print(f"   状态: {'有效' if is_valid else '无效'}")

    return editor


def demo_advanced_features():
    """演示高级功能组合使用"""
    print("\n=== 4. 高级功能组合演示 (Advanced Features Combination) ===")

    constellation = TaskConstellation()
    editor = ConstellationEditor(constellation)

    # 使用批量构建命令 (Using bulk build command)
    print("\n使用批量构建命令:")

    constellation_config = {
        "tasks": [
            {
                "task_id": "advanced_task1",
                "name": "高级任务1",
                "description": "批量构建的任务1",
                "priority": 2,
            },
            {
                "task_id": "advanced_task2",
                "name": "高级任务2",
                "description": "批量构建的任务2",
                "priority": 3,
            },
            {
                "task_id": "advanced_task3",
                "name": "高级任务3",
                "description": "批量构建的任务3",
                "priority": 1,
            },
        ],
        "dependencies": [
            {
                "from_task_id": "advanced_task1",
                "to_task_id": "advanced_task2",
                "dependency_type": "unconditional",
            },
            {
                "from_task_id": "advanced_task2",
                "to_task_id": "advanced_task3",
                "dependency_type": "success_only",
            },
        ],
    }

    # 通过注册器执行批量构建
    try:
        result = editor.execute_command_by_name(
            "build_constellation", constellation_config
        )
        print(
            f"   ✓ 批量构建成功: {len(result.tasks)} 个任务, {len(result.dependencies)} 个依赖"
        )

        # 验证构建结果
        is_valid, errors = constellation.validate_dag()
        print(f"   ✓ 构建结果: {'有效' if is_valid else '无效'}")

    except Exception as e:
        print(f"   ✗ 批量构建失败: {e}")

    # 测试撤销/重做 (Test undo/redo)
    print("\n测试撤销/重做:")
    print(f"   执行前: {len(constellation.tasks)} 个任务")
    print(f"   可撤销: {editor.can_undo()}")

    if editor.can_undo():
        editor.undo()
        print(f"   撤销后: {len(constellation.tasks)} 个任务")
        print(f"   可重做: {editor.can_redo()}")

        if editor.can_redo():
            editor.redo()
            print(f"   重做后: {len(constellation.tasks)} 个任务")

    return editor


def main():
    """主程序演示所有功能"""
    print("UFO Constellation Editor 更新功能演示")
    print("=" * 60)

    try:
        # 演示所有功能
        editor1 = demo_serializable_parameters()
        editor2 = demo_command_registry()
        editor3 = demo_validation_rollback()
        editor4 = demo_advanced_features()

        print("\n" + "=" * 60)
        print("✓ 所有演示完成! 主要更新包括:")
        print("  1. ✓ 命令参数支持可序列化 (dict 格式)")
        print("  2. ✓ 命令注册器和装饰器系统")
        print("  3. ✓ 自动验证和撤回机制")
        print("  4. ✓ 完整的撤销/重做支持")
        print("  5. ✓ 批量操作和文件操作")

        # 显示注册器统计信息
        print(f"\n注册器统计:")
        print(f"  - 注册命令数: {len(command_registry.list_commands())}")
        print(f"  - 命令类别数: {len(command_registry.get_categories())}")

        return 0

    except Exception as e:
        print(f"\n✗ 演示失败: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
