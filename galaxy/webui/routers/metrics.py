# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Metrics router for Galaxy Web UI.

Exposes LLM cost and token-usage data accumulated during the active Galaxy
session.  All data originates from ``SessionMetricsObserver`` and is served
by ``MetricsService``.
"""

import logging
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import PlainTextResponse, Response

from galaxy.webui.dependencies import get_app_state, verify_api_key
from galaxy.webui.models.responses import SessionCostSummary
from galaxy.webui.services.metrics_service import MetricsService

router = APIRouter(prefix="/api/metrics", tags=["metrics"])
logger = logging.getLogger(__name__)


@router.get(
    "/cost",
    response_model=SessionCostSummary,
    dependencies=[Depends(verify_api_key)],
)
async def get_session_cost() -> SessionCostSummary:
    """
    Return aggregated LLM cost and token usage for the active session.

    Includes per-agent and per-model cost breakdowns plus the most recent
    call records (up to the last 500 stored by the observer).

    :return: ``SessionCostSummary`` for the active session.
    :raises HTTPException: 404 when no active session is available.
    """
    app_state = get_app_state()
    service = MetricsService(app_state)

    summary = service.get_cost_summary()
    if summary is None:
        raise HTTPException(status_code=404, detail="No active session")

    return SessionCostSummary(**summary)


@router.get(
    "/cost/export",
    dependencies=[Depends(verify_api_key)],
)
async def export_cost_log(
    format: Literal["json", "csv"] = "json",
) -> Response:
    """
    Download the full LLM call log for the active session.

    :param format: Output format — ``json`` (default) or ``csv``.
    :return: File download response.
    :raises HTTPException: 404 when no active session is available.
    """
    app_state = get_app_state()
    service = MetricsService(app_state)

    if service.get_cost_summary() is None:
        raise HTTPException(status_code=404, detail="No active session")

    if format == "csv":
        content = service.export_calls_csv()
        return PlainTextResponse(
            content=content,
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=llm_calls.csv"},
        )

    content = service.export_calls_json()
    return PlainTextResponse(
        content=content,
        media_type="application/json",
        headers={"Content-Disposition": "attachment; filename=llm_calls.json"},
    )
