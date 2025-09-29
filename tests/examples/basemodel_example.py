#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
BaseModel Integration Example for TaskStar, TaskStarLine, and TaskConstellation.

This example demonstrates how to use the Pydantic BaseModel schemas for
serialization, deserialization, and data validation with the constellation classes.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import json
from datetime import datetime

from ufo.galaxy.constellation.task_star import TaskStar
from ufo.galaxy.constellation.task_star_line import TaskStarLine
from ufo.galaxy.constellation.task_constellation import TaskConstellation
from ufo.galaxy.constellation.enums import (
    TaskStatus,
    TaskPriority,
    DeviceType,
    DependencyType,
)
from ufo.galaxy.agents.schema import (
    TaskStarSchema,
    TaskStarLineSchema,
    TaskConstellationSchema,
)


def example_basic_usage():
    """示例：基本用法"""
    print("📚 基本用法示例")
    print("=" * 50)

    # 创建 TaskStar 实例
    task = TaskStar(
        task_id="example_task",
        name="示例任务",
        description="这是一个示例任务，展示 BaseModel 集成",
        priority=TaskPriority.HIGH,
        device_type=DeviceType.WINDOWS,
    )

    # 转换为 BaseModel
    schema = task.to_basemodel()
    print(f"✅ TaskStar -> BaseModel: {schema.name}")

    # 从 BaseModel 恢复
    task_restored = TaskStar.from_basemodel(schema)
    print(f"✅ BaseModel -> TaskStar: {task_restored.name}")

    # JSON 序列化
    json_str = schema.model_dump_json(indent=2)
    print(f"✅ JSON 序列化长度: {len(json_str)} 字符")


def example_json_persistence():
    """示例：JSON 持久化"""
    print("\n💾 JSON 持久化示例")
    print("=" * 50)

    # 创建复杂的星座
    constellation = TaskConstellation(
        constellation_id="example_constellation", name="示例任务星座"
    )

    # 添加任务
    tasks_data = [
        ("数据提取", "从源系统提取数据", TaskPriority.HIGH),
        ("数据处理", "处理提取的数据", TaskPriority.MEDIUM),
        ("结果验证", "验证处理结果", TaskPriority.LOW),
    ]

    task_ids = []
    for i, (name, desc, priority) in enumerate(tasks_data, 1):
        task_id = f"task_{i:03d}"
        task = TaskStar(
            task_id=task_id,
            name=name,
            description=desc,
            priority=priority,
            device_type=DeviceType.LINUX,
        )
        constellation.add_task(task)
        task_ids.append(task_id)

    # 添加依赖关系
    deps = [
        (task_ids[0], task_ids[1], DependencyType.SUCCESS_ONLY),
        (task_ids[1], task_ids[2], DependencyType.UNCONDITIONAL),
    ]

    for from_id, to_id, dep_type in deps:
        dep = TaskStarLine(from_id, to_id, dep_type)
        constellation.add_dependency(dep)

    # 转换为 BaseModel 并序列化
    schema = constellation.to_basemodel()
    json_data = schema.model_dump_json(indent=2)

    # 保存到文件
    filename = "example_constellation.json"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(json_data)
    print(f"✅ 星座已保存到: {filename}")

    # 从文件加载
    with open(filename, "r", encoding="utf-8") as f:
        loaded_json = f.read()

    loaded_schema = TaskConstellationSchema.model_validate_json(loaded_json)
    loaded_constellation = TaskConstellation.from_basemodel(loaded_schema)

    print(f"✅ 从文件加载星座: {loaded_constellation.name}")
    print(f"   - 任务数量: {len(loaded_constellation.tasks)}")
    print(f"   - 依赖关系数量: {len(loaded_constellation.dependencies)}")


def example_data_validation():
    """示例：数据验证"""
    print("\n🔍 数据验证示例")
    print("=" * 50)

    # 创建有效的 schema 数据
    valid_data = {
        "task_id": "validation_task",
        "name": "验证任务",
        "description": "用于测试数据验证的任务",
        "priority": "HIGH",
        "status": "PENDING",
        "device_type": "WINDOWS",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "task_data": {"param1": "value1"},
        "dependencies": [],
        "dependents": [],
    }

    try:
        # 验证并创建 schema
        schema = TaskStarSchema(**valid_data)
        print("✅ 有效数据验证成功")

        # 转换为 TaskStar
        task = TaskStar.from_basemodel(schema)
        print(f"✅ 成功创建任务: {task.name}")

    except Exception as e:
        print(f"❌ 数据验证失败: {e}")

    # 测试无效数据
    invalid_data = valid_data.copy()
    invalid_data["task_id"] = ""  # 空的 task_id

    try:
        schema = TaskStarSchema(**invalid_data)
        task = TaskStar.from_basemodel(schema)
        print("⚠️ 空 task_id 被接受了")
    except Exception as e:
        print(f"✅ 正确捕获无效数据: {type(e).__name__}")


def example_api_integration():
    """示例：API 集成"""
    print("\n🌐 API 集成示例")
    print("=" * 50)

    # 模拟 API 响应数据
    api_response = {
        "constellation_id": "api_constellation",
        "name": "来自API的星座",
        "state": "READY",
        "tasks": {
            "api_task_1": {
                "task_id": "api_task_1",
                "name": "API任务1",
                "description": "通过API创建的任务",
                "priority": 3,  # 整数形式的优先级
                "status": "pending",  # 小写状态
                "device_type": "windows",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "task_data": {},
                "dependencies": [],
                "dependents": [],
            }
        },
        "dependencies": {},
        "metadata": {"source": "api", "version": "1.0"},
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "enable_visualization": True,
    }

    try:
        # 从 API 数据创建 schema
        schema = TaskConstellationSchema(**api_response)
        print("✅ API 数据验证成功")

        # 转换为 TaskConstellation
        constellation = TaskConstellation.from_basemodel(schema)
        print(f"✅ 成功创建星座: {constellation.name}")
        print(f"   - 状态: {constellation.state.value}")
        print(f"   - 任务数: {len(constellation.tasks)}")

        # 获取任务并检查属性
        task = list(constellation.tasks.values())[0]
        print(f"   - 任务优先级: {task.priority.value} ({task.priority.name})")
        print(f"   - 任务状态: {task.status.value}")

    except Exception as e:
        print(f"❌ API 集成失败: {e}")


def main():
    """运行所有示例"""
    print("🚀 BaseModel 集成示例")
    print("这些示例展示了如何在实际应用中使用 BaseModel 功能\n")

    example_basic_usage()
    example_json_persistence()
    example_data_validation()
    example_api_integration()

    print("\n🎉 所有示例执行完成！")
    print("\n💡 主要特性:")
    print("   • 自动类型转换（枚举 ↔ 字符串）")
    print("   • JSON 序列化/反序列化")
    print("   • 数据验证和错误处理")
    print("   • API 集成支持")
    print("   • 向后兼容性")


if __name__ == "__main__":
    main()
