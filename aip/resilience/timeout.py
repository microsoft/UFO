# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Timeout Manager

Handles timeout enforcement for asynchronous operations in AIP.
"""

import asyncio
import logging
from typing import Any, Awaitable, Optional, TypeVar

T = TypeVar("T")


class TimeoutManager:
    """
    Manages timeouts for asynchronous operations.

    Features:
    - Configurable default timeout
    - Per-operation timeout override
    - Timeout exception wrapping
    - Detailed logging
    """

    def __init__(self, default_timeout: float = 120.0):
        """
        Initialize timeout manager.

        :param default_timeout: Default timeout for operations (seconds)
        """
        self.default_timeout = default_timeout
        self.logger = logging.getLogger(f"{__name__}.TimeoutManager")

    async def with_timeout(
        self,
        coro: Awaitable[T],
        timeout: Optional[float] = None,
        operation_name: str = "operation",
    ) -> T:
        """
        Execute a coroutine with timeout.

        :param coro: Coroutine to execute
        :param timeout: Timeout in seconds (default: use default_timeout)
        :param operation_name: Name of operation for logging
        :return: Result of coroutine
        :raises: asyncio.TimeoutError if operation times out
        """
        timeout = timeout or self.default_timeout

        try:
            self.logger.debug(f"Starting {operation_name} with timeout {timeout}s")
            result = await asyncio.wait_for(coro, timeout=timeout)
            self.logger.debug(f"Completed {operation_name}")
            return result

        except asyncio.TimeoutError:
            self.logger.error(f"Timeout ({timeout}s) exceeded for {operation_name}")
            raise asyncio.TimeoutError(f"{operation_name} timed out after {timeout}s")
        except Exception as e:
            self.logger.error(f"Error in {operation_name}: {e}", exc_info=True)
            raise

    async def with_timeout_or_none(
        self,
        coro: Awaitable[T],
        timeout: Optional[float] = None,
        operation_name: str = "operation",
    ) -> Optional[T]:
        """
        Execute a coroutine with timeout, returning None on timeout.

        :param coro: Coroutine to execute
        :param timeout: Timeout in seconds (default: use default_timeout)
        :param operation_name: Name of operation for logging
        :return: Result of coroutine or None if timeout
        """
        try:
            return await self.with_timeout(coro, timeout, operation_name)
        except asyncio.TimeoutError:
            self.logger.warning(f"{operation_name} timed out, returning None")
            return None
