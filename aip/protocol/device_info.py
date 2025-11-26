# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Device Info Protocol

Handles device information requests and responses.
"""

import datetime
import logging
from typing import Any, Dict, Optional
from uuid import uuid4

from aip.messages import (
    ClientMessage,
    ClientMessageType,
    ClientType,
    ServerMessage,
    ServerMessageType,
    TaskStatus,
)
from aip.protocol.base import AIPProtocol


class DeviceInfoProtocol(AIPProtocol):
    """
    Device information protocol for AIP.

    Handles:
    - Device info requests from constellation
    - Device info responses from device
    - System information exchange
    """

    def __init__(self, *args, **kwargs):
        """Initialize device info protocol."""
        super().__init__(*args, **kwargs)
        self.logger = logging.getLogger(f"{__name__}.DeviceInfoProtocol")

    async def request_device_info(
        self,
        constellation_id: str,
        target_device: str,
        request_id: Optional[str] = None,
    ) -> None:
        """
        Request device information (constellation-side).

        :param constellation_id: Constellation client ID
        :param target_device: Target device ID
        :param request_id: Optional request ID for correlation
        """
        req_msg = ClientMessage(
            type=ClientMessageType.DEVICE_INFO_REQUEST,
            client_type=ClientType.CONSTELLATION,
            client_id=constellation_id,
            target_id=target_device,
            request_id=request_id or str(uuid4()),
            timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),
            status=TaskStatus.OK,
        )
        await self.send_message(req_msg)
        self.logger.info(
            f"Sent device info request: {constellation_id} → {target_device}"
        )

    async def send_device_info_response(
        self,
        device_info: Optional[Dict[str, Any]],
        request_id: str,
        error: Optional[str] = None,
    ) -> None:
        """
        Send device information response (server-side).

        :param device_info: Device information dictionary
        :param request_id: Request ID for correlation
        :param error: Optional error message
        """
        status = TaskStatus.OK if error is None else TaskStatus.ERROR
        resp_msg = ServerMessage(
            type=ServerMessageType.DEVICE_INFO_RESPONSE,
            status=status,
            result=device_info,
            error=error,
            timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),
            response_id=request_id,
        )
        await self.send_message(resp_msg)
        self.logger.info(f"Sent device info response (request_id: {request_id})")

    async def send_device_info_push(
        self,
        device_id: str,
        device_info: Dict[str, Any],
    ) -> None:
        """
        Push device information proactively (device-side, future use).

        :param device_id: Device ID
        :param device_info: Device information dictionary
        """
        push_msg = ClientMessage(
            type=ClientMessageType.DEVICE_INFO_RESPONSE,
            client_id=device_id,
            client_type=ClientType.DEVICE,
            metadata=device_info,
            status=TaskStatus.OK,
            timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        )
        await self.send_message(push_msg)
        self.logger.info(f"Pushed device info from {device_id}")
