import asyncio
import datetime
import logging
import platform
import threading
import uuid
from typing import Any, Callable, Dict, Optional, TYPE_CHECKING

from config.config_loader import get_ufo_config
from aip.messages import ServerMessage, ServerMessageType, TaskStatus
from ufo.module.basic import BaseSession
from ufo.module.session_pool import SessionFactory

if TYPE_CHECKING:
    from aip.protocol.task_execution import TaskExecutionProtocol

ufo_config = get_ufo_config()


class SessionManager:
    """
    This class manages active sessions for the UFO service.
    Supports Windows, Linux, and Mobile (Android) platforms using SessionFactory.
    """

    def __init__(self, platform_override: Optional[str] = None):
        """
        Initialize the SessionManager.
        This class manages active sessions for the UFO service.
        :param platform_override: Override platform detection ('windows', 'linux', or 'mobile').
                                  If None, platform is auto-detected.
        """
        self.sessions: Dict[str, BaseSession] = {}

        # Mapping of task names to session IDs
        self.session_id_dict: Dict[str, str] = {}
        self.lock = threading.Lock()
        self.logger = logging.getLogger(__name__)
        self.results: Dict[str, Dict[str, Any]] = {}

        # Track running background tasks
        self._running_tasks: Dict[str, asyncio.Task] = {}

        # Track cancellation reasons (session_id -> reason)
        self._cancellation_reasons: Dict[str, str] = {}

        # Platform configuration
        self.platform = platform_override or platform.system().lower()
        self.session_factory = SessionFactory()

        self.logger.info(f"SessionManager initialized for platform: {self.platform}")

    def get_or_create_session(
        self,
        session_id: str,
        task_name: Optional[str] = "test_task",
        request: Optional[str] = None,
        task_protocol: Optional["TaskExecutionProtocol"] = None,
        platform_override: Optional[str] = None,
        local: bool = False,
    ) -> BaseSession:
        """
        Get an existing session or create a new one if it doesn't exist.
        Uses SessionFactory to create platform-specific service sessions.

        :param session_id: The ID of the session to retrieve or create.
        :param task_name: The name of the task.
        :param request: Optional request text to initialize the session.
        :param task_protocol: Optional AIP TaskExecutionProtocol instance.
        :param platform_override: Override platform detection ('windows', 'linux', or 'mobile').
        :param local: Whether the session is running in local mode with the client.
        :return: The BaseSession object for the session (Windows, Linux, or Mobile).
        """
        with self.lock:
            if session_id not in self.sessions:
                # Use platform override if provided, otherwise use instance platform
                target_platform = platform_override or self.platform

                if local:
                    session = self.session_factory.create_session(
                        task=task_name,
                        should_evaluate=ufo_config.system.eva_session,
                        mode="normal",
                        request=request or "",
                        id=session_id,
                    )

                else:
                    # Create session using SessionFactory
                    session = self.session_factory.create_service_session(
                        task=task_name,
                        should_evaluate=ufo_config.system.eva_session,
                        id=session_id,
                        request=request or "",
                        task_protocol=task_protocol,
                        platform_override=target_platform,
                    )

                self.session_id_dict[task_name] = session_id
                self.sessions[session_id] = session

                session_type = session.__class__.__name__
                self.logger.info(
                    f"Created new {target_platform} session: {session_id} (type: {session_type})"
                )
            else:
                self.logger.info(f"Retrieved existing session: {session_id}")

            return self.sessions[session_id]

    def get_result(self, session_id: str) -> Optional[Dict[str, any]]:
        """
        Get the result of a completed session.
        :param session_id: The ID of the session to retrieve the result for.
        :return: A dictionary containing the session result, or None if not found.
        """
        with self.lock:
            if session_id in self.sessions:
                return self.sessions[session_id].results
            return None

    def get_result_by_task(self, task_name: str) -> Optional[Dict[str, any]]:
        """
        Get the result of a completed session by task name.
        :param task_name: The name of the task to retrieve the result for.
        :return: A dictionary containing the session result, or None if not found.
        """
        with self.lock:
            session_id = self.session_id_dict.get(task_name)
            if session_id:
                return self.get_result(session_id)

    def set_results(self, session_id: str):
        """
        Set the result for a completed session.
        :param session_id: The ID of the session to set the result for.
        """
        with self.lock:
            if session_id in self.sessions:
                self.results[session_id] = self.sessions[session_id].results

    def remove_session(self, session_id: str):
        """
        Remove a session by its ID.
        :param session_id: The ID of the session to remove.
        """
        with self.lock:
            self.sessions.pop(session_id, None)
            self.logger.info(f"Removed session: {session_id}")

    async def execute_task_async(
        self,
        session_id: str,
        task_name: str,
        request: str,
        task_protocol: Optional["TaskExecutionProtocol"] = None,
        platform_override: str = None,
        callback: Optional[Callable[[str, ServerMessage], None]] = None,
    ) -> str:
        """
        Execute a task in the background without blocking the event loop.

        This method:
        1. Creates or retrieves the session
        2. Starts session execution in background task
        3. Calls callback when complete with results

        This allows the WebSocket handler to continue processing other messages
        (heartbeats, ping/pong) while the session runs.

        :param session_id: Session identifier
        :param task_name: Task name
        :param request: User request
        :param task_protocol: AIP TaskExecutionProtocol instance
        :param platform_override: Platform type ('windows', 'linux', or 'mobile')
        :param callback: Optional async callback(session_id, ServerMessage) when task completes
        :return: session_id
        """
        # Create session
        session = self.get_or_create_session(
            session_id=session_id,
            task_name=task_name,
            request=request,
            task_protocol=task_protocol,
            platform_override=platform_override,
        )

        # Start background task
        task = asyncio.create_task(
            self._run_session_background(session_id, session, callback)
        )
        self._running_tasks[session_id] = task

        self.logger.info(f"[SessionManager] 🚀 Started background task {session_id}")
        return session_id

    async def cancel_task(
        self, session_id: str, reason: str = "constellation_disconnected"
    ) -> bool:
        """
        Cancel a running background task.

        :param session_id: The session ID to cancel.
        :param reason: Reason for cancellation. Options:
                      - "constellation_disconnected": Constellation client disconnected (don't send callback)
                      - "device_disconnected": Target device disconnected (send callback to constellation)
        :return: True if task was found and cancelled, False otherwise.
        """
        task = self._running_tasks.get(session_id)
        if task and not task.done():
            self.logger.info(
                f"[SessionManager] 🛑 Cancelling session {session_id} (reason: {reason})"
            )

            # Store cancellation reason for use in _run_session_background
            self._cancellation_reasons[session_id] = reason

            task.cancel()

            # Wait a bit for graceful cancellation
            try:
                await asyncio.wait_for(task, timeout=2.0)
            except (asyncio.CancelledError, asyncio.TimeoutError):
                pass

            self._running_tasks.pop(session_id, None)
            self._cancellation_reasons.pop(session_id, None)  # Clean up reason
            self.remove_session(session_id)
            self.logger.info(f"[SessionManager] ✅ Session {session_id} cancelled")
            return True

        self.logger.warning(
            f"[SessionManager] ⚠️ No running task found for {session_id}"
        )
        return False

    async def _run_session_background(
        self,
        session_id: str,
        session: BaseSession,
        callback: Optional[Callable],
    ) -> None:
        """
        Run session in background and notify callback when complete.

        This method runs the session without blocking the event loop,
        allowing WebSocket ping/pong and heartbeat messages to continue.

        :param session_id: Session identifier
        :param session: Session instance to run
        :param callback: Optional async callback to notify when complete
        """
        error = None
        status = TaskStatus.FAILED
        was_cancelled = False

        try:
            self.logger.info(f"[SessionManager] 🚀 Executing session {session_id}")
            start_time = asyncio.get_event_loop().time()

            # Run the session (this may contain sync LLM calls that need fixing)
            await session.run()

            elapsed = asyncio.get_event_loop().time() - start_time
            self.logger.info(
                f"[SessionManager] ⏱️ Session {session_id} execution took {elapsed:.2f}s"
            )

            # Determine final status
            if session.is_error():
                status = TaskStatus.FAILED
                session.results = session.results or {
                    "failure": "session ended with an error"
                }
                self.logger.info(
                    f"[SessionManager] ⚠️ Session {session_id} ended with error"
                )
            elif session.is_finished():
                status = TaskStatus.COMPLETED
                self.logger.info(
                    f"[SessionManager] ✅ Session {session_id} finished successfully"
                )
            else:
                status = TaskStatus.FAILED
                error = "Session ended in unknown state"
                self.logger.warning(
                    f"[SessionManager] ⚠️ Session {session_id} ended in unknown state"
                )

            session.reset()

        except asyncio.CancelledError:
            # Handle task cancellation
            cancellation_reason = self._cancellation_reasons.get(
                session_id, "constellation_disconnected"
            )

            self.logger.warning(
                f"[SessionManager] 🛑 Session {session_id} was cancelled (reason: {cancellation_reason})"
            )
            status = TaskStatus.FAILED

            # Set appropriate error message based on cancellation reason
            if cancellation_reason == "device_disconnected":
                error = "Task was cancelled because target device disconnected"
                was_cancelled = False  # Still send callback to constellation
            else:  # constellation_disconnected or other reasons
                error = "Task was cancelled due to client disconnection"
                was_cancelled = True  # Don't send callback

            # Don't re-raise, just handle gracefully

        except Exception as e:
            import traceback

            traceback.print_exc()
            self.logger.error(f"[SessionManager] ❌ Error in session {session_id}: {e}")
            status = TaskStatus.FAILED
            error = str(e)

        finally:
            # Don't send callback if task was cancelled (client already disconnected)
            if was_cancelled:
                self.logger.info(
                    f"[SessionManager] 🛑 Session {session_id} cancelled, skipping callback"
                )
                self._running_tasks.pop(session_id, None)
                return

            self.logger.info(
                f"[SessionManager] 📦 Building result message for session {session_id} (status={status})"
            )

            # Build result message
            result_message = ServerMessage(
                type=ServerMessageType.TASK_END,
                status=status,
                session_id=session_id,
                error=error,
                result=session.results,
                timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                response_id=str(uuid.uuid4()),
            )

            # Save results
            self.set_results(session_id)
            self.logger.info(
                f"[SessionManager] 💾 Saved results for session {session_id}"
            )

            # Notify callback
            if callback:
                self.logger.info(
                    f"[SessionManager] 📞 Calling callback for session {session_id}"
                )
                try:
                    await callback(session_id, result_message)
                    self.logger.info(
                        f"[SessionManager] ✅ Callback completed for session {session_id}"
                    )
                except Exception as e:
                    import traceback

                    self.logger.error(
                        f"[SessionManager] ❌ Callback error for session {session_id}: {e}\n{traceback.format_exc()}"
                    )
            else:
                self.logger.warning(
                    f"[SessionManager] ⚠️ No callback registered for session {session_id}"
                )

            # Cleanup
            self._running_tasks.pop(session_id, None)
            self.logger.info(
                f"[SessionManager] ✅ Session {session_id} completed with status {status}"
            )
