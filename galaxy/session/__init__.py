# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Galaxy Session Package

This package contains session implementations for the Galaxy framework,
including the GalaxySession for DAG-based task orchestration sessions
and event-driven observers for monitoring and visualization.
"""

from .galaxy_session import GalaxySession

# Import observers from the new modular structure
from .observers import (
    ConstellationProgressObserver,
    SessionMetricsObserver,
    DAGVisualizationObserver,
)

__all__ = [
    "GalaxySession",
    "ConstellationProgressObserver",
    "SessionMetricsObserver",
    "DAGVisualizationObserver",
]
