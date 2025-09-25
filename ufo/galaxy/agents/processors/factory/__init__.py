# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Constellation Agent factory package.

This package contains factory classes for creating constellation-specific
strategies and prompters based on weaving modes.
"""

from .constellation_factory import (
    ConstellationStrategyFactory,
    create_constellation_strategies_for_mode,
)

__all__ = [
    "ConstellationStrategyFactory",
    "create_constellation_strategies_for_mode",
]
