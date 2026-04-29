# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Authentication router for Galaxy Web UI.

Provides a secure endpoint for the frontend to authenticate using the
API key (displayed in the server console) and receive a session token,
without exposing the API key in HTML responses.
"""

import secrets
from typing import Dict, Any

from fastapi import APIRouter, Depends

from galaxy.webui.dependencies import verify_api_key

router = APIRouter(tags=["auth"])


@router.post(
    "/api/authenticate",
    dependencies=[Depends(verify_api_key)],
)
async def authenticate() -> Dict[str, Any]:
    """
    Authenticate with the API key and receive a confirmation.

    The client must provide the API key via the X-API-Key header.
    The key is displayed in the server console on startup.

    :return: Dictionary confirming successful authentication
    """
    return {"authenticated": True}
