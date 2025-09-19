# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Galaxy Agents Package

This package contains agent implementations for the Galaxy framework,
including the WeaverAgent for DAG-based task orchestration.
"""

from .weaver_agent import WeaverAgent

__all__ = ["WeaverAgent"]
