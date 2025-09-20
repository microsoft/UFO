# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Galaxy Agents Package

This package contains agent implementations for the Galaxy framework,
including the GalaxyWeaverAgent for DAG-based task orchestration.
"""

from .galaxy_agent import GalaxyWeaverAgent

__all__ = ["GalaxyWeaverAgent"]
