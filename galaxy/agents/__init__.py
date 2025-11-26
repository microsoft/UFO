# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Galaxy Agents Package

This package contains agent implementations for the Galaxy framework,
including the Constellation for DAG-based task orchestration.
"""

from .constellation_agent import ConstellationAgent

__all__ = ["ConstellationAgent"]
