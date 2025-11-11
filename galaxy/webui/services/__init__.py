# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Services for Galaxy Web UI.

This package contains business logic services that encapsulate
operations and interact with the Galaxy framework.
"""

from galaxy.webui.services.device_service import DeviceService
from galaxy.webui.services.galaxy_service import GalaxyService
from galaxy.webui.services.config_service import ConfigService

__all__ = [
    "DeviceService",
    "GalaxyService",
    "ConfigService",
]
