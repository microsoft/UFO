# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Enumerations for the Task System in Constellation V2.

This module defines the core enums used throughout the task orchestration system
for task management, dependency handling, and execution coordination.
"""

from enum import Enum


class TaskStatus(Enum):
    """
    Represents the status of a task in the constellation.
    """

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    WAITING_DEPENDENCY = "waiting_dependency"


class DependencyType(Enum):
    """
    Types of dependencies between tasks.
    """

    UNCONDITIONAL = "unconditional"  # 无条件依赖，前置任务完成即可
    CONDITIONAL = "conditional"  # 条件依赖，需要满足特定条件
    SUCCESS_ONLY = "success_only"  # 仅在前置任务成功时执行
    COMPLETION_ONLY = "completion_only"  # 无论成功失败，前置任务完成即可


class ConstellationState(Enum):
    """
    State of the entire task constellation.
    """

    CREATED = "created"
    READY = "ready"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIALLY_FAILED = "partially_failed"


class TaskPriority(Enum):
    """
    Priority levels for task execution.
    """

    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


class DeviceType(Enum):
    """
    Supported device types in the constellation.
    """

    WINDOWS = "windows"
    MACOS = "macos"
    LINUX = "linux"
    ANDROID = "android"
    IOS = "ios"
    WEB = "web"
    API = "api"
