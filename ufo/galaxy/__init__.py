# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
UFO Galaxy Framework

A comprehensive framework for DAG-based task orchestration and device management.

This package provides:
- Constellation: DAG management and execution
- Agents: Task orchestration agents (WeaverAgent)
- Session: Galaxy session management
- Client: Device management and coordination
"""

# Core constellation components
from .constellation import (
    TaskOrchestration,
    TaskConstellation,
    TaskStar,
    TaskStarLine,
    LLMParser,
    ConstellationExecutor,
    TaskStatus,
    DependencyType,
    ConstellationState,
    DeviceType,
    TaskPriority,
    create_and_orchestrate_from_llm,
    create_simple_constellation,
)

# Agent components
from .agents import WeaverAgent

# Session components
from .session import GalaxySession

# Client entry points
from .galaxy_client import GalaxyClient

__all__ = [
    # Constellation
    "TaskOrchestration",
    "TaskConstellation",
    "TaskStar",
    "TaskStarLine",
    "LLMParser",
    "ConstellationExecutor",
    "TaskStatus",
    "DependencyType",
    "ConstellationState",
    "DeviceType",
    "TaskPriority",
    "create_and_orchestrate_from_llm",
    "create_simple_constellation",
    # Agents
    "WeaverAgent",
    # Session
    "GalaxySession",
    # Client
    "GalaxyClient",
]
