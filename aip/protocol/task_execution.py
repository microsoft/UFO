# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Task Execution Protocol

Handles task assignment, execution coordination, and result reporting.
"""

import datetime
import logging
from typing import Any, List, Optional
from uuid import uuid4

from aip.messages import (
    ClientMessage,
    ClientMessageType,
    ClientType,
    Command,
    Result,
    ServerMessage,
    ServerMessageType,
    TaskStatus,
)
from aip.protocol.base import AIPProtocol


class TaskExecutionProtocol(AIPProtocol):
    """
    Task execution protocol for AIP.

    Handles:
    - Task assignment from constellation to device
    - Task status updates
    - Command execution
    - Result reporting
    """

    def __init__(self, *args, **kwargs):
        """Initialize task execution protocol."""
        super().__init__(*args, **kwargs)
        self.logger = logging.getLogger(f"{__name__}.TaskExecutionProtocol")

    async def send_task_request(
        self,
        request: str,
        task_name: str,
        session_id: str,
        client_id: str,
        target_id: Optional[str] = None,
        client_type: ClientType = ClientType.DEVICE,
        metadata: Optional[dict] = None,
    ) -> None:
        """
        Send a task request.

        :param request: Task request text
        :param task_name: Task name
        :param session_id: Session ID
        :param client_id: Client ID
        :param target_id: Target device ID (for constellation)
        :param client_type: Type of client
        :param metadata: Optional metadata
        """
        task_msg = ClientMessage(
            type=ClientMessageType.TASK,
            request=request,
            task_name=task_name,
            session_id=session_id,
            client_id=client_id,
            target_id=target_id,
            client_type=client_type,
            status=TaskStatus.CONTINUE,
            timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),
            request_id=str(uuid4()),
            metadata=metadata,
        )
        await self.send_message(task_msg)
        self.logger.info(f"Sent task request: {task_name}")

    async def send_task_assignment(
        self,
        user_request: str,
        task_name: str,
        session_id: str,
        response_id: str,
        agent_name: Optional[str] = None,
        process_name: Optional[str] = None,
    ) -> None:
        """
        Send task assignment to device (server-side).

        :param user_request: User request text
        :param task_name: Task name
        :param session_id: Session ID
        :param response_id: Response ID
        :param agent_name: Agent name
        :param process_name: Process name
        """
        task_msg = ServerMessage(
            type=ServerMessageType.TASK,
            status=TaskStatus.CONTINUE,
            user_request=user_request,
            task_name=task_name,
            session_id=session_id,
            response_id=response_id,
            agent_name=agent_name,
            process_name=process_name,
            timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        )
        await self.send_message(task_msg)
        self.logger.info(f"Sent task assignment: {task_name}")

    async def send_command(self, server_message: ServerMessage) -> None:
        """
        Send command(s) to execute (server-side).
        Accepts a ServerMessage object directly for backward compatibility.

        :param server_message: ServerMessage with commands to execute
        """
        await self.send_message(server_message)
        actions_count = len(server_message.actions) if server_message.actions else 0
        self.logger.info(
            f"Sent {actions_count} command(s) for session {server_message.session_id}"
        )

    async def send_commands(
        self,
        actions: List[Command],
        session_id: str,
        response_id: str,
        status: TaskStatus = TaskStatus.CONTINUE,
        agent_name: Optional[str] = None,
        process_name: Optional[str] = None,
        root_name: Optional[str] = None,
        task_name: Optional[str] = None,
    ) -> None:
        """
        Send command(s) to execute (server-side).
        Creates ServerMessage from parameters.

        :param actions: List of commands to execute
        :param session_id: Session ID
        :param response_id: Response ID
        :param status: Task status
        :param agent_name: Agent name
        :param process_name: Process name
        :param root_name: Root name
        :param task_name: Task name
        """
        cmd_msg = ServerMessage(
            type=ServerMessageType.COMMAND,
            status=status,
            actions=actions,
            session_id=session_id,
            response_id=response_id,
            agent_name=agent_name,
            process_name=process_name,
            root_name=root_name,
            task_name=task_name,
            timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        )
        await self.send_message(cmd_msg)
        self.logger.info(f"Sent {len(actions)} command(s) for session {session_id}")

    async def send_command_results(
        self,
        action_results: List[Result],
        session_id: str,
        client_id: str,
        prev_response_id: str,
        status: TaskStatus = TaskStatus.CONTINUE,
    ) -> None:
        """
        Send command execution results (client-side).

        :param action_results: Results of executed commands
        :param session_id: Session ID
        :param client_id: Client ID
        :param prev_response_id: Previous response ID
        :param status: Task status
        """
        result_msg = ClientMessage(
            type=ClientMessageType.COMMAND_RESULTS,
            action_results=action_results,
            session_id=session_id,
            client_id=client_id,
            prev_response_id=prev_response_id,
            status=status,
            timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),
            request_id=str(uuid4()),
        )
        await self.send_message(result_msg)
        self.logger.info(
            f"Sent {len(action_results)} result(s) for session {session_id}"
        )

    async def send_task_result(
        self,
        session_id: str,
        prev_response_id: str,
        action_results: List[Result],
        status: TaskStatus = TaskStatus.CONTINUE,
        client_id: Optional[str] = None,
    ) -> None:
        """
        Convenience method to send task results (client-side).
        Alias for send_command_results with automatic client_id handling.

        :param session_id: Session ID
        :param prev_response_id: Previous response ID
        :param action_results: Results of executed commands
        :param status: Task status
        :param client_id: Client ID (optional, will be extracted from context if available)
        """
        # If client_id not provided, try to extract from transport or use a default
        if not client_id:
            client_id = "unknown_client"  # Fallback

        await self.send_command_results(
            action_results=action_results,
            session_id=session_id,
            client_id=client_id,
            prev_response_id=prev_response_id,
            status=status,
        )

    async def send_task_end(
        self,
        session_id: str,
        status: TaskStatus,
        result: Optional[Any] = None,
        error: Optional[str] = None,
        response_id: Optional[str] = None,
    ) -> None:
        """
        Send task completion notification (server-side).

        :param session_id: Session ID
        :param status: Final task status (COMPLETED or FAILED)
        :param result: Task result if successful
        :param error: Error message if failed
        :param response_id: Response ID
        """
        task_end_msg = ServerMessage(
            type=ServerMessageType.TASK_END,
            status=status,
            session_id=session_id,
            result=result,
            error=error,
            response_id=response_id or str(uuid4()),
            timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        )
        await self.send_message(task_end_msg)
        self.logger.info(f"Sent task end for session {session_id}, status: {status}")

    async def send_task_end_ack(
        self,
        session_id: str,
        client_id: str,
        status: TaskStatus,
        error: Optional[str] = None,
    ) -> None:
        """
        Send task end acknowledgment (client-side).

        :param session_id: Session ID
        :param client_id: Client ID
        :param status: Task status
        :param error: Error message if failed
        """
        task_end_msg = ClientMessage(
            type=ClientMessageType.TASK_END,
            session_id=session_id,
            client_id=client_id,
            status=status,
            error=error,
            timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        )
        await self.send_message(task_end_msg)
        self.logger.info(f"Sent task end ack for session {session_id}")
