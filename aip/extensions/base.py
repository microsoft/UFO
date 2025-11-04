# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Base Extension Interface

Defines the interface for AIP extensions.
"""

from abc import ABC, abstractmethod
from typing import Any


class AIPExtension(ABC):
    """
    Abstract base class for AIP extensions.

    Extensions can customize protocol behavior, add logging,
    collect metrics, or implement custom business logic.
    """

    @abstractmethod
    async def on_message_sent(self, msg: Any) -> None:
        """
        Called when a message is sent.

        :param msg: Message that was sent
        """
        pass

    @abstractmethod
    async def on_message_received(self, msg: Any) -> None:
        """
        Called when a message is received.

        :param msg: Message that was received
        """
        pass

    @abstractmethod
    async def on_connection_established(self, endpoint_id: str) -> None:
        """
        Called when a connection is established.

        :param endpoint_id: Endpoint identifier
        """
        pass

    @abstractmethod
    async def on_connection_closed(self, endpoint_id: str) -> None:
        """
        Called when a connection is closed.

        :param endpoint_id: Endpoint identifier
        """
        pass

    @abstractmethod
    async def on_error(self, error: Exception, context: str) -> None:
        """
        Called when an error occurs.

        :param error: Exception that occurred
        :param context: Context where error occurred
        """
        pass
