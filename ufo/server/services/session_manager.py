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


class SessionOwnershipError(PermissionError):
    """
    Raised when a client attempts to access a ``session_id`` that was
    created by a different client.

    UFO's :class:`SessionManager` keeps a single shared in-memory store
    of live and recently completed sessions. Without ownership binding,
    any authenticated WebSocket client could submit a ``TASK`` message
    that reuses another client's ``session_id`` and:

    * receive the previously stored ``session.results`` (stale-result
      replay across clients), and/or
    * piggy-back on a still-running session object created by another
      principal.

    To defeat this, the manager records the ``client_id`` that first
    created each session and rejects subsequent access from a different
    client by raising :class:`SessionOwnershipError`. The WebSocket
    handler catches this exception and responds to the requester with
    an error instead of leaking the original session's state.
    """

    def __init__(self, session_id: str, owner: str, attempted_by: str):
        self.session_id = session_id
        self.owner = owner
        self.attempted_by = attempted_by
        super().__init__(
            f"session_id {session_id!r} is owned by another client; "
            "reuse from a different principal is not permitted"
        )


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
        # Mapping of session_id -> the ``client_id`` that first created
        # the session. This is the authoritative owner used to defeat
        # cross-client session reuse (see :class:`SessionOwnershipError`).
        # The handler passes the registered ``client_id`` of the
        # requesting WebSocket connection; if a later request supplies a
        # different ``client_id`` for the same ``session_id`` we refuse
        # to hand back the existing session object rather than leaking
        # its accumulated results.
        self._session_owners: Dict[str, str] = {}
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
        owner_client_id: Optional[str] = None,
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
        :param owner_client_id: The ``client_id`` of the requester that
            is creating or reusing the session. When supplied, the
            manager records this value on first creation and enforces
            that subsequent reuses come from the same principal. Passing
            ``None`` preserves the legacy unauthenticated/local code
            path (no ownership check) for callers that operate outside
            of the multi-client WebSocket server (e.g. CLI / single-
            process runs).
        :raises SessionOwnershipError: If ``session_id`` already exists
            in the in-memory store under a different ``owner_client_id``.
        :return: The BaseSession object for the session (Windows, Linux, or Mobile).
        """
        with self.lock:
            if session_id in self.sessions:
                # ---------- Cross-client session reuse defense ----------
                # Refuse to hand back another principal's session object.
                # If the recorded owner does not match the caller, raise
                # rather than silently returning the existing session
                # (whose ``results`` could be replayed to the attacker
                # via the normal task-end callback path).
                #
                # An authenticated caller (``owner_client_id`` supplied)
                # may only reuse a session that was created under the
                # *same* recorded owner. Sessions that exist with no
                # recorded owner — either because they were injected by
                # a bypass path or were created by a legacy/local code
                # path — must NOT be claimed post-hoc by a WebSocket
                # peer, since doing so would expose any prior
                # ``session.results`` to the new requester.
                if owner_client_id is not None:
                    recorded_owner = self._session_owners.get(session_id)
                    if (
                        recorded_owner is None
                        or recorded_owner != owner_client_id
                    ):
                        self.logger.warning(
                            "[SessionManager] 🚨 cross-client session reuse "
                            f"rejected: session_id={session_id!r} owner="
                            f"{recorded_owner!r} attempted_by={owner_client_id!r}"
                        )
                        raise SessionOwnershipError(
                            session_id=session_id,
                            owner=recorded_owner or "<unowned>",
                            attempted_by=owner_client_id,
                        )
                self.logger.info(f"Retrieved existing session: {session_id}")
            else:
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
                # Bind the session to its creator for the lifetime of
                # the in-memory entry. Subsequent reuse with a different
                # ``owner_client_id`` will be rejected above. Callers
                # that pass ``owner_client_id=None`` (legacy/local
                # paths) opt out of the binding entirely.
                if owner_client_id is not None:
                    self._session_owners[session_id] = owner_client_id

                session_type = session.__class__.__name__
                self.logger.info(
                    f"Created new {target_platform} session: {session_id} "
                    f"(type: {session_type}, owner: {owner_client_id!r})"
                )

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
            # Also drop the recorded owner so that the same
            # ``session_id`` may legitimately be reused by a future
            # principal once the prior session is gone.
            self._session_owners.pop(session_id, None)
            self.logger.info(f"Removed session: {session_id}")

    async def execute_task_async(
        self,
        session_id: str,
        task_name: str,
        request: str,
        task_protocol: Optional["TaskExecutionProtocol"] = None,
        platform_override: str = None,
        callback: Optional[Callable[[str, ServerMessage], None]] = None,
        owner_client_id: Optional[str] = None,
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
        :param owner_client_id: The ``client_id`` of the requester. When
            provided, the manager binds the session to this principal
            on first creation and rejects reuse by any other principal
            with :class:`SessionOwnershipError`.
        :return: session_id
        :raises SessionOwnershipError: Propagated from
            :meth:`get_or_create_session` when a different client tries
            to reuse an existing ``session_id``.
        """
        # Create session
        session = self.get_or_create_session(
            session_id=session_id,
            task_name=task_name,
            request=request,
            task_protocol=task_protocol,
            platform_override=platform_override,
            owner_client_id=owner_client_id,
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
            # Drop the completed session from the in-memory store so its
            # ``results`` cannot be replayed to a future requester that
            # re-uses (or guesses) the same ``session_id``. The session
            # has already been delivered to its rightful requester via
            # the callback above; keeping the populated session object
            # alive in :attr:`sessions` was the root cause of the
            # stale-result replay vulnerability.
            self.remove_session(session_id)
            self.logger.info(
                f"[SessionManager] ✅ Session {session_id} completed with status {status}"
            )
