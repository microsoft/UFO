# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Metrics service for Galaxy Web UI.

Reads LLM cost and token metrics accumulated by SessionMetricsObserver
and exposes them in a form suitable for the API layer.
"""

import csv
import io
import json
import logging
from typing import TYPE_CHECKING, Any, Dict, List, Optional

if TYPE_CHECKING:
    from galaxy.webui.dependencies import AppState


class MetricsService:
    """
    Thin service layer over the SessionMetricsObserver metrics dict.

    All data originates from ``SessionMetricsObserver.metrics["llm_metrics"]``
    which is updated in real time as LLM calls complete.
    """

    def __init__(self, app_state: "AppState") -> None:
        """
        Initialise MetricsService.

        :param app_state: Application state providing access to the Galaxy session.
        """
        self._app_state = app_state
        self._logger = logging.getLogger(__name__)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_llm_metrics(self) -> Optional[Dict[str, Any]]:
        """
        Return the ``llm_metrics`` dict from the active session observer, or
        ``None`` when no session / observer is available.
        """
        session = self._app_state.galaxy_session
        if session is None:
            return None

        observer = getattr(session, "_metrics_observer", None)
        if observer is None:
            return None

        return observer.metrics.get("llm_metrics")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_cost_summary(self) -> Optional[Dict[str, Any]]:
        """
        Return a dict matching the ``SessionCostSummary`` response model.

        Returns ``None`` when no active session exists.

        :return: Cost summary dict or None.
        """
        llm = self._get_llm_metrics()
        if llm is None:
            return None

        session = self._app_state.galaxy_session
        session_id: str = observer.metrics.get("session_id", "unknown")

        raw_calls: List[Dict[str, Any]] = llm.get("calls", [])
        recent_calls = [
            {
                "agent_type": c.get("agent_type", ""),
                "model": c.get("model", ""),
                "prompt_tokens": c.get("prompt_tokens", 0),
                "completion_tokens": c.get("completion_tokens", 0),
                "cost": c.get("cost", 0.0),
                "duration_ms": c.get("duration_ms", 0.0),
                "timestamp": c.get("timestamp", 0.0),
            }
            for c in raw_calls
        ]

        return {
            "session_id": session_id,
            "total_cost": llm.get("total_cost", 0.0),
            "total_prompt_tokens": llm.get("total_prompt_tokens", 0),
            "total_completion_tokens": llm.get("total_completion_tokens", 0),
            "total_api_calls": llm.get("total_api_calls", 0),
            "cost_by_agent": llm.get("cost_by_agent", {}),
            "cost_by_model": llm.get("cost_by_model", {}),
            "recent_calls": recent_calls,
        }

    def export_calls_json(self) -> str:
        """
        Serialise the full LLM call log as a JSON string.

        :return: JSON string of call records.
        """
        llm = self._get_llm_metrics()
        calls = llm.get("calls", []) if llm else []
        return json.dumps(calls, indent=2)

    def export_calls_csv(self) -> str:
        """
        Serialise the full LLM call log as a CSV string.

        :return: CSV string with headers.
        """
        llm = self._get_llm_metrics()
        calls: List[Dict[str, Any]] = llm.get("calls", []) if llm else []

        output = io.StringIO()
        fieldnames = [
            "timestamp",
            "agent_type",
            "model",
            "prompt_tokens",
            "completion_tokens",
            "cost",
            "duration_ms",
        ]
        writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(calls)
        return output.getvalue()
