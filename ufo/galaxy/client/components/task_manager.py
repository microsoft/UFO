# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Task Execution Manager

Manages task assignment and result handling.
Single responsibility: Task execution coordination.
"""

import asyncio
import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any

from ufo.contracts.contracts import (
    ClientMessage,
    ClientMessageType,
    TaskStatus,
)
from .connection_manager import WebSocketConnectionManager


class TaskExecutionManager:
    """
    Manages task assignment and result handling.
    Single responsibility: Task execution coordination.
    """

    def __init__(self, connection_manager: WebSocketConnectionManager):
        self.connection_manager = connection_manager
        self._pending_tasks: Dict[str, asyncio.Future] = {}
        self._active_sessions: Dict[str, str] = {}  # session_id -> device_id
        self.logger = logging.getLogger(f"{__name__}.TaskExecutionManager")

    async def assign_task_to_device(
        self,
        task_id: str,
        device_id: str,
        target_client_id: Optional[str],
        task_description: str,
        task_data: Dict[str, Any],
        timeout: float = 300.0,
    ) -> Dict[str, Any]:
        """
        Assign a task to a specific device.

        :param task_id: Unique task identifier
        :param device_id: Target device ID
        :param target_client_id: Specific local client ID (optional)
        :param task_description: Task description
        :param task_data: Task data and metadata
        :param timeout: Task timeout in seconds
        :return: Task execution result
        """
        websocket = self.connection_manager.get_connection(device_id)
        if not websocket:
            raise ValueError(f"Device {device_id} is not connected")

        # Create task future
        future = asyncio.Future()
        self._pending_tasks[task_id] = future

        try:
            # Send task assignment
            session_id = str(uuid.uuid4())
            self._active_sessions[session_id] = device_id

            task_message = ClientMessage(
                type=ClientMessageType.REQUEST,
                client_id=f"constellation@{device_id}",
                session_id=session_id,
                target_id=target_client_id,  # Route to specific local client if specified
                task_name=f"constellation_task_{task_id}",
                request=task_description,
                timestamp=datetime.now(timezone.utc).isoformat(),
                status=TaskStatus.CONTINUE,
                metadata={
                    "task_id": task_id,
                    "constellation_task": True,
                    **task_data,
                },
            )

            await websocket.send(task_message.model_dump_json())
            self.logger.info(f"📤 Assigned task {task_id} to device {device_id}")

            # Wait for completion with timeout
            result = await asyncio.wait_for(future, timeout=timeout)
            return result

        except asyncio.TimeoutError:
            self.logger.error(f"⏱️ Task {task_id} timed out on device {device_id}")
            raise
        except Exception as e:
            self.logger.error(f"❌ Task {task_id} failed on device {device_id}: {e}")
            raise
        finally:
            # Clean up
            self._pending_tasks.pop(task_id, None)
            # Note: session cleanup handled in message processing

    def complete_task(self, session_id: str, result: Dict[str, Any]) -> None:
        """Complete a pending task with results"""
        device_id = self._active_sessions.get(session_id)
        if not device_id:
            return

        # Find corresponding task
        task_id = None
        for tid, future in self._pending_tasks.items():
            if not future.done():
                # Additional matching logic could be added here
                task_id = tid
                break

        if task_id and task_id in self._pending_tasks:
            future = self._pending_tasks[task_id]
            if not future.done():
                future.set_result(result)
                self.logger.info(f"✅ Task {task_id} completed on device {device_id}")

        # Clean up session
        self._active_sessions.pop(session_id, None)

    def fail_task(self, session_id: str, error: str) -> None:
        """Fail a pending task with error"""
        device_id = self._active_sessions.get(session_id)
        if not device_id:
            return

        # Find and fail corresponding task
        for task_id, future in self._pending_tasks.items():
            if not future.done():
                future.set_exception(Exception(f"Task failed: {error}"))
                self.logger.error(
                    f"❌ Task {task_id} failed on device {device_id}: {error}"
                )
                break

        # Clean up session
        self._active_sessions.pop(session_id, None)

    def get_pending_tasks(self) -> List[str]:
        """Get list of pending task IDs"""
        return [tid for tid, future in self._pending_tasks.items() if not future.done()]

    def cancel_all_tasks(self) -> None:
        """Cancel all pending tasks"""
        for task_id, future in self._pending_tasks.items():
            if not future.done():
                future.cancel()
        self._pending_tasks.clear()
        self._active_sessions.clear()
