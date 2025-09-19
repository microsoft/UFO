# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Galaxy Session Package

This package contains session implementations for the Galaxy framework,
including the GalaxySession for DAG-based task orchestration sessions.
"""

from .galaxy_session import GalaxySession

__all__ = ["GalaxySession"]
