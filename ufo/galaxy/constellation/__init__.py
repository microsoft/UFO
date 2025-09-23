# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Task System for Constellation V2 - Modular task orchestration system.

This module provides a comprehensive task management system for multi-device
orchestration with LLM integration, dynamic task creation, and async execution.
"""

from .enums import (
    TaskStatus,
    DependencyType,
    ConstellationState,
    TaskPriority,
    DeviceType,
)
from .task_star import TaskStar
from .task_star_line import TaskStarLine
from .task_constellation import TaskConstellation
from .parsers.parser import LLMParser
from .orchestrator.orchestrator import TaskConstellationOrchestrator
from .orchestrator.constellation_manager import ConstellationManager

__all__ = [
    "TaskStatus",
    "DependencyType",
    "ConstellationState",
    "TaskPriority",
    "DeviceType",
    "TaskStar",
    "TaskStarLine",
    "TaskConstellation",
    "LLMParser",
    "TaskConstellationOrchestrator",
    "create_and_orchestrate_from_llm",
    "create_simple_constellation_standalone",
    "ConstellationManager",
]
