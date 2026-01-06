# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
AIP Resilience Mechanisms

Provides connection resilience, reconnection strategies, heartbeat management,
and timeout handling for reliable agent communication.
"""

from .heartbeat_manager import HeartbeatManager
from .reconnection import ReconnectionPolicy, ReconnectionStrategy
from .timeout import TimeoutManager

__all__ = [
    "ReconnectionStrategy",
    "ReconnectionPolicy",
    "HeartbeatManager",
    "TimeoutManager",
]
