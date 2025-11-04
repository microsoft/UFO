# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
AIP Extension Middleware

Provides ready-to-use extensions for common use cases.
"""

import logging
import time
from typing import Any, Dict

from aip.extensions.base import AIPExtension


class LoggingExtension(AIPExtension):
    """
    Extension that logs all protocol events.
    """

    def __init__(self, log_level: int = logging.INFO):
        """
        Initialize logging extension.

        :param log_level: Log level for events
        """
        self.logger = logging.getLogger(f"{__name__}.LoggingExtension")
        self.log_level = log_level

    async def on_message_sent(self, msg: Any) -> None:
        """Log sent message."""
        msg_type = getattr(msg, "type", "unknown")
        self.logger.log(self.log_level, f"[SENT] {msg_type}")

    async def on_message_received(self, msg: Any) -> None:
        """Log received message."""
        msg_type = getattr(msg, "type", "unknown")
        self.logger.log(self.log_level, f"[RECV] {msg_type}")

    async def on_connection_established(self, endpoint_id: str) -> None:
        """Log connection establishment."""
        self.logger.log(self.log_level, f"[CONN] Connection established: {endpoint_id}")

    async def on_connection_closed(self, endpoint_id: str) -> None:
        """Log connection closure."""
        self.logger.log(self.log_level, f"[DISC] Connection closed: {endpoint_id}")

    async def on_error(self, error: Exception, context: str) -> None:
        """Log error."""
        self.logger.error(f"[ERROR] {context}: {error}", exc_info=True)


class MetricsExtension(AIPExtension):
    """
    Extension that collects protocol metrics.
    """

    def __init__(self):
        """Initialize metrics extension."""
        self.logger = logging.getLogger(f"{__name__}.MetricsExtension")
        self.metrics: Dict[str, Any] = {
            "messages_sent": 0,
            "messages_received": 0,
            "connections_established": 0,
            "connections_closed": 0,
            "errors": 0,
            "message_types": {},
            "latencies": [],
        }
        self._message_timestamps: Dict[str, float] = {}

    async def on_message_sent(self, msg: Any) -> None:
        """Track sent message."""
        self.metrics["messages_sent"] += 1
        msg_type = str(getattr(msg, "type", "unknown"))
        self.metrics["message_types"][msg_type] = (
            self.metrics["message_types"].get(msg_type, 0) + 1
        )

        # Track timestamp for latency calculation
        msg_id = getattr(msg, "request_id", None) or getattr(msg, "response_id", None)
        if msg_id:
            self._message_timestamps[msg_id] = time.time()

    async def on_message_received(self, msg: Any) -> None:
        """Track received message."""
        self.metrics["messages_received"] += 1

        # Calculate latency if we have a matching sent message
        msg_id = getattr(msg, "request_id", None) or getattr(msg, "response_id", None)
        if msg_id and msg_id in self._message_timestamps:
            latency = time.time() - self._message_timestamps[msg_id]
            self.metrics["latencies"].append(latency)
            del self._message_timestamps[msg_id]

    async def on_connection_established(self, endpoint_id: str) -> None:
        """Track connection establishment."""
        self.metrics["connections_established"] += 1

    async def on_connection_closed(self, endpoint_id: str) -> None:
        """Track connection closure."""
        self.metrics["connections_closed"] += 1

    async def on_error(self, error: Exception, context: str) -> None:
        """Track error."""
        self.metrics["errors"] += 1

    def get_metrics(self) -> Dict[str, Any]:
        """
        Get collected metrics.

        :return: Metrics dictionary
        """
        metrics = self.metrics.copy()
        if metrics["latencies"]:
            metrics["avg_latency"] = sum(metrics["latencies"]) / len(
                metrics["latencies"]
            )
            metrics["max_latency"] = max(metrics["latencies"])
            metrics["min_latency"] = min(metrics["latencies"])
        return metrics

    def reset_metrics(self) -> None:
        """Reset all metrics."""
        self.metrics = {
            "messages_sent": 0,
            "messages_received": 0,
            "connections_established": 0,
            "connections_closed": 0,
            "errors": 0,
            "message_types": {},
            "latencies": [],
        }
        self._message_timestamps.clear()
