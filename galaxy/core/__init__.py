# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Galaxy Framework Core Package

This package contains the core types, interfaces, and utilities for the Galaxy framework.
"""

from .types import (
    # Type aliases
    TaskId,
    ConstellationId,
    DeviceId,
    SessionId,
    AgentId,
    ProgressCallback,
    AsyncProgressCallback,
    ErrorCallback,
    AsyncErrorCallback,
    # Result types
    ExecutionResult,
    ConstellationResult,
    # Configuration types
    TaskConfiguration,
    ConstellationConfiguration,
    DeviceConfiguration,
    # Context types
    ProcessingContext,
    # Exception hierarchy
    GalaxyFrameworkError,
    TaskExecutionError,
    ConstellationError,
    DeviceError,
    ConfigurationError,
    ValidationError,
    # Utility types
    Statistics,
)

from .interfaces import (
    # Task interfaces
    ITask,
    ITaskFactory,
    # Dependency interfaces
    IDependency,
    IDependencyResolver,
    # Constellation interfaces
    IConstellation,
    IConstellationBuilder,
    # Execution interfaces
    ITaskExecutor,
    IConstellationExecutor,
    # Device interfaces
    IDevice,
    IDeviceRegistry,
    IDeviceSelector,
    # Agent interfaces
    IRequestProcessor,
    IResultProcessor,
    IConstellationUpdater,
    # Session interfaces
    ISessionManager,
    ISession,
    # Monitoring interfaces
    IMetricsCollector,
    IEventLogger,
)

__all__ = [
    # Types
    "TaskId",
    "ConstellationId",
    "DeviceId",
    "SessionId",
    "AgentId",
    "ProgressCallback",
    "AsyncProgressCallback",
    "ErrorCallback",
    "AsyncErrorCallback",
    "ExecutionResult",
    "ConstellationResult",
    "TaskConfiguration",
    "ConstellationConfiguration",
    "DeviceConfiguration",
    "ProcessingContext",
    "Statistics",
    # Exceptions
    "GalaxyFrameworkError",
    "TaskExecutionError",
    "ConstellationError",
    "DeviceError",
    "ConfigurationError",
    "ValidationError",
    # Interfaces
    "ITask",
    "ITaskFactory",
    "IDependency",
    "IDependencyResolver",
    "IConstellation",
    "IConstellationBuilder",
    "ITaskExecutor",
    "IConstellationExecutor",
    "IDevice",
    "IDeviceRegistry",
    "IDeviceSelector",
    "IRequestProcessor",
    "IResultProcessor",
    "IConstellationUpdater",
    "ISessionManager",
    "ISession",
    "IMetricsCollector",
    "IEventLogger",
]
