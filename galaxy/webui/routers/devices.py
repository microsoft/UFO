# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Device management router for Galaxy Web UI.

This module defines API endpoints for managing devices in the Galaxy framework.
"""

import logging
from typing import Dict, Any

from fastapi import APIRouter, HTTPException

from galaxy.webui.dependencies import get_app_state
from galaxy.webui.models.requests import DeviceAddRequest
from galaxy.webui.models.responses import DeviceAddResponse
from galaxy.webui.services import ConfigService, DeviceService

router = APIRouter(prefix="/api", tags=["devices"])
logger = logging.getLogger(__name__)


@router.post("/devices", response_model=DeviceAddResponse)
async def add_device(device: DeviceAddRequest) -> Dict[str, Any]:
    """
    Add a new device to the Galaxy configuration.

    This endpoint:
    1. Validates the device configuration data
    2. Checks for device ID conflicts
    3. Saves the device to devices.yaml configuration file
    4. Registers the device with the device manager
    5. Optionally initiates connection to the device

    :param device: Device configuration data validated against DeviceAddRequest model
    :return: Success response with device details
    :raises HTTPException: 404 if devices.yaml not found
    :raises HTTPException: 409 if device ID already exists
    :raises HTTPException: 500 if device addition fails
    """
    logger.info(f"Received request to add device: {device.device_id}")

    # Initialize services
    config_service = ConfigService()
    app_state = get_app_state()
    device_service = DeviceService(app_state)

    try:
        # Check if devices.yaml exists
        try:
            config_service.load_devices_config()
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail="devices.yaml not found")

        # Check for device_id conflict
        if config_service.device_id_exists(device.device_id):
            raise HTTPException(
                status_code=409,
                detail=f"Device ID '{device.device_id}' already exists",
            )

        # Add device to configuration file
        new_device = config_service.add_device_to_config(
            device_id=device.device_id,
            server_url=device.server_url,
            os=device.os,
            capabilities=device.capabilities,
            metadata=device.metadata,
            auto_connect=(
                device.auto_connect if device.auto_connect is not None else True
            ),
            max_retries=device.max_retries if device.max_retries is not None else 5,
        )

        # Attempt to register and connect the device via device manager
        await device_service.register_and_connect_device(
            device_id=device.device_id,
            server_url=device.server_url,
            os=device.os,
            capabilities=device.capabilities,
            metadata=device.metadata,
            max_retries=device.max_retries if device.max_retries is not None else 5,
            auto_connect=(
                device.auto_connect if device.auto_connect is not None else True
            ),
        )

        return {
            "status": "success",
            "message": f"Device '{device.device_id}' added successfully",
            "device": new_device,
        }

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except ValueError as e:
        # Handle validation errors from services
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        # Handle unexpected errors
        logger.error(f"❌ Error adding device: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to add device: {str(e)}")
