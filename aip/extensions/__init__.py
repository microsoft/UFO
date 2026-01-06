# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
AIP Extension Support

Provides extension points for customizing AIP behavior.
"""

from .base import AIPExtension
from .middleware import LoggingExtension, MetricsExtension

__all__ = ["AIPExtension", "LoggingExtension", "MetricsExtension"]
