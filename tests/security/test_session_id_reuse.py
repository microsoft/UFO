"""Regression tests for the cross-client ``session_id`` reuse vulnerability.

These tests pin the behavior that fixes the published advisory where:

* :class:`SessionManager` re-used an existing in-memory session object
  whenever a client supplied a known/predicted ``session_id``, without
  verifying that the requester was the original creator.
* Completed sessions persisted in :attr:`SessionManager.sessions`
  indefinitely, so a later authenticated peer could trigger the normal
  task-end callback path and receive the prior requester's stored
  ``session.results`` — a stale-result replay across clients.

After the fix:

1. :class:`SessionManager.get_or_create_session` records the creator's
   ``client_id`` on first creation and raises
   :class:`SessionOwnershipError` when a different ``client_id`` tries
   to reuse the same ``session_id``.
2. :meth:`UFOWebSocketHandler.handle_task_request` plumbs the
   connection-bound (registered) ``client_id`` into
   :meth:`SessionManager.execute_task_async`, catches
   :class:`SessionOwnershipError`, and responds to the requester with
   an explanatory error instead of re-entering the existing session.
3. Sessions are removed from :attr:`SessionManager.sessions` after the
   task-end callback fires, so the in-memory store cannot accumulate
   completed sessions whose ``results`` could later be replayed.
"""

from __future__ import annotations

import asyncio
import sys
import types
import unittest
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


REPO_ROOT = Path(__file__).resolve().parents[2]


def _stub_module(name: str, attrs: Optional[dict] = None) -> types.ModuleType:
    if name in sys.modules:
        return sys.modules[name]
    mod = types.ModuleType(name)
    for attr, value in (attrs or {}).items():
        setattr(mod, attr, value)
    sys.modules[name] = mod
    return mod


def _ensure_repo_on_path() -> None:
    if str(REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(REPO_ROOT))

    # ``art`` is an optional dependency pulled in transitively by some
    # downstream modules; stub it out in trimmed CI environments so
    # imports succeed. (No-op when the real package is installed.)
    if "art" not in sys.modules:
        art_mod = types.ModuleType("art")
        art_mod.text2art = lambda *args, **kwargs: ""
        sys.modules["art"] = art_mod

    # NOTE: We deliberately do NOT stub ``ufo.utils``,
    # ``ufo.module.basic``, ``ufo.module.session_pool``, or
    # ``ufo.module.dispatcher`` here. The real modules import cleanly
    # and other security tests in this directory depend on the real
    # ``ufo.utils.is_safe_task_name`` and friends being available.
    # Polluting ``sys.modules`` with thin stubs would break those tests
    # (pytest shares ``sys.modules`` across test files in a single run).


_ensure_repo_on_path()


# ---------------------------------------------------------------------------
# Real module loader.
# ---------------------------------------------------------------------------
#
# Other security test files (notably ``test_ws_role_spoof.py`` and
# ``test_ws_shared_handler_isolation.py``) install lightweight stubs for
# ``ufo.server.services.session_manager`` / ``ufo.module.dispatcher`` at
# module-import time. Pytest imports every test file during the
# collection phase, so by the time *our* test cases run those stubs
# already live in :mod:`sys.modules` and override the real
# implementations. We need the *real* :class:`SessionManager` here so
# the ownership logic under test actually executes, so we restore the
# affected modules to their real implementations before each test run.
#
# We snapshot any stubs first and restore them in :meth:`tearDownClass`
# so that test files which intentionally rely on the stubs continue to
# work if they happen to run after us.


from aip.messages import (  # noqa: E402
    ClientMessage,
    ClientMessageType,
    ClientType,
    TaskStatus,
)
from ufo.server.services.client_connection_manager import (  # noqa: E402
    ClientConnectionManager,
)


_MODULES_TO_RESTORE = (
    "ufo.server.services.session_manager",
    "ufo.server.ws.handler",
    "ufo.module.dispatcher",
    "ufo.module.basic",
    "ufo.module.session_pool",
    "ufo.module.context",
)


def _load_real_modules() -> tuple:
    """Drop any test-stubbed entries and re-import the real modules."""
    import importlib

    saved: Dict[str, Any] = {}
    for name in _MODULES_TO_RESTORE:
        if name in sys.modules:
            saved[name] = sys.modules.pop(name)

    try:
        session_manager_module = importlib.import_module(
            "ufo.server.services.session_manager"
        )
        handler_module = importlib.import_module("ufo.server.ws.handler")
    except Exception:
        # If the real modules cannot be imported (e.g. the trimmed CI
        # environment is missing optional deps), put the previously
        # cached entries back and re-raise so the failure is visible.
        for name, mod in saved.items():
            sys.modules[name] = mod
        raise

    return session_manager_module, handler_module, saved


def _new_loop() -> None:
    asyncio.set_event_loop(asyncio.new_event_loop())


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


# ---------------------------------------------------------------------------
# Unit-level tests against the real ``SessionManager``.
# ---------------------------------------------------------------------------


class SessionManagerOwnershipTests(unittest.TestCase):
    """The session manager must bind sessions to their creating client."""

    _saved_modules: Dict[str, Any] = {}

    @classmethod
    def setUpClass(cls) -> None:
        session_manager_module, _handler_module, saved = _load_real_modules()
        cls._saved_modules = saved
        cls._SessionManager = session_manager_module.SessionManager
        cls._SessionOwnershipError = session_manager_module.SessionOwnershipError

    @classmethod
    def tearDownClass(cls) -> None:
        # Put any previously-stubbed entries back so other test files
        # that depend on them keep working.
        for name, mod in cls._saved_modules.items():
            sys.modules[name] = mod

    def setUp(self) -> None:
        self.manager = self._SessionManager(platform_override="windows")

    def _seed_completed_session(
        self,
        session_id: str,
        owner: Optional[str],
        results: Dict[str, Any],
    ) -> "_CompletedSession":
        """Inject a completed session into the manager's store.

        Mirrors the published PoC, which pre-populates a completed
        session under a known ``session_id`` to simulate the
        steady-state where the manager has not yet cleaned up.
        """
        session = _CompletedSession(results)
        # Reach into the manager exactly like the PoC does so the test
        # exercises the same attack surface.
        self.manager.sessions[session_id] = session
        if owner is not None:
            # Use the real binding API path (``get_or_create_session``)
            # so the recorded-owner state is set the way production
            # code sets it. Direct dict mutation is reserved for the
            # PoC's "no recorded owner" scenario below.
            self.manager._session_owners[session_id] = owner
        return session

    def test_creator_can_reuse_their_own_session(self) -> None:
        """An owner re-issuing the same ``session_id`` is not rejected."""
        session_id = "owned-session"
        self._seed_completed_session(
            session_id, owner="victim-device", results={"ok": True}
        )

        # Same principal: must succeed and return the same object.
        returned = self.manager.get_or_create_session(
            session_id=session_id,
            owner_client_id="victim-device",
        )

        self.assertIs(returned, self.manager.sessions[session_id])

    def test_different_client_cannot_reuse_session(self) -> None:
        """A different ``client_id`` must be rejected with ownership error."""
        session_id = "owned-session"
        self._seed_completed_session(
            session_id, owner="victim-device", results={"secret": "victim"}
        )

        with self.assertRaises(self._SessionOwnershipError) as cm:
            self.manager.get_or_create_session(
                session_id=session_id,
                owner_client_id="attacker-device",
            )

        self.assertEqual(cm.exception.session_id, session_id)
        self.assertEqual(cm.exception.owner, "victim-device")
        self.assertEqual(cm.exception.attempted_by, "attacker-device")

    def test_unowned_session_cannot_be_claimed_post_hoc(self) -> None:
        """A session present without a recorded owner is not claimable.

        This matches the published PoC, which injects a stale
        ``CompletedSession`` directly into ``manager.sessions`` without
        going through :meth:`get_or_create_session`. The manager must
        refuse to bind such a session to a WebSocket peer at access
        time, since doing so would replay the injected ``results``.
        """
        session_id = "unowned-session"
        self._seed_completed_session(
            session_id, owner=None, results={"secret": "leaked"}
        )

        with self.assertRaises(self._SessionOwnershipError):
            self.manager.get_or_create_session(
                session_id=session_id,
                owner_client_id="attacker-device",
            )

    def test_remove_session_clears_owner_binding(self) -> None:
        """``remove_session`` must drop the recorded owner mapping."""
        session_id = "to-be-removed"
        self._seed_completed_session(
            session_id, owner="victim-device", results={"ok": True}
        )

        self.manager.remove_session(session_id)

        self.assertNotIn(session_id, self.manager.sessions)
        self.assertNotIn(session_id, self.manager._session_owners)


class _CompletedSession:
    """Stand-in for a ``BaseSession`` that has already finished.

    Mirrors the published PoC's stand-in (only what
    :meth:`SessionManager._run_session_background` consumes).
    """

    def __init__(self, results: Dict[str, Any]) -> None:
        self.results = results
        self.run_calls = 0
        self.reset_calls = 0

    async def run(self) -> Dict[str, Any]:
        self.run_calls += 1
        return self.results

    def is_error(self) -> bool:
        return False

    def is_finished(self) -> bool:
        return True

    def reset(self) -> None:
        self.reset_calls += 1


# ---------------------------------------------------------------------------
# Handler-level tests against the real ``UFOWebSocketHandler``.
# ---------------------------------------------------------------------------


@dataclass
class _RecorderProtocol:
    """Captures the AIP protocol calls the handler would send."""

    label: str
    acks: List[str] = field(default_factory=list)
    task_ends: List[Dict[str, Any]] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    async def send_ack(self, session_id: str) -> None:
        self.acks.append(session_id)

    async def send_task_end(self, **kwargs: Any) -> None:
        self.task_ends.append(kwargs)

    async def send_error(self, error: str) -> None:
        self.errors.append(error)


class HandlerCrossClientReplayRejectionTests(unittest.TestCase):
    """End-to-end: the handler must reject session_id replay attempts."""

    _saved_modules: Dict[str, Any] = {}

    @classmethod
    def setUpClass(cls) -> None:
        session_manager_module, handler_module, saved = _load_real_modules()
        cls._saved_modules = saved
        cls._SessionManager = session_manager_module.SessionManager
        cls._UFOWebSocketHandler = handler_module.UFOWebSocketHandler

    @classmethod
    def tearDownClass(cls) -> None:
        for name, mod in cls._saved_modules.items():
            sys.modules[name] = mod

    def setUp(self) -> None:
        _new_loop()

        self.session_manager = self._SessionManager(platform_override="windows")
        self.client_manager = ClientConnectionManager()
        self.handler = self._UFOWebSocketHandler(
            self.client_manager, self.session_manager, local=False
        )

        self.attacker_protocol = _RecorderProtocol("attacker-device")
        # Mirror the per-connection wiring that ``connect()`` performs.
        self.handler.task_protocol = self.attacker_protocol

        self.client_manager.add_client(
            client_id="attacker-device",
            platform="windows",
            ws=object(),
            client_type=ClientType.DEVICE,
            metadata={},
            transport=None,
            task_protocol=self.attacker_protocol,
        )

    def test_replay_of_victim_session_id_is_rejected(self) -> None:
        """Reuse of a victim ``session_id`` must not leak ``session.results``.

        This is the published PoC, expressed against the real handler:

        * Pre-populate :attr:`SessionManager.sessions` with a completed
          session under a guessable ID (``"constellation-demo@task_001"``)
          and ``results`` representing the victim's prior task output.
        * The attacker connects, registers as a device, and sends a
          ``TASK`` message reusing the victim ``session_id``.
        * The handler must:
            - NOT invoke the session's ``run`` method,
            - NOT send a ``task_end`` carrying ``session.results``,
            - NOT issue an ACK for the replayed ``session_id``,
            - Send an error response to the attacker.
        """
        victim_session_id = "constellation-demo@task_001"
        victim_results = {
            "secret": "victim-result",
            "device": "victim-device",
        }

        completed = _CompletedSession(victim_results)
        self.session_manager.sessions[victim_session_id] = completed
        # Simulate the production state where the victim's session was
        # originally created via ``get_or_create_session(..., owner_client_id="victim-device")``
        # and thus carries a recorded owner.
        self.session_manager._session_owners[victim_session_id] = "victim-device"

        replay = ClientMessage(
            type=ClientMessageType.TASK,
            status=TaskStatus.CONTINUE,
            client_type=ClientType.DEVICE,
            client_id="attacker-device",
            request="attacker replay request",
            session_id=victim_session_id,
            task_name="attacker-task",
        )

        _run(
            self.handler.handle_message(
                replay.model_dump_json(),
                registered_client_id="attacker-device",
                registered_client_type=ClientType.DEVICE,
            )
        )

        # Give any scheduled background coroutine a chance to run. The
        # handler must NOT have scheduled the existing session.
        _run(asyncio.sleep(0.05))

        self.assertEqual(
            completed.run_calls,
            0,
            "Victim session must not be (re)executed for the attacker",
        )
        self.assertEqual(
            self.attacker_protocol.task_ends,
            [],
            "No task_end carrying victim results may be sent to the attacker",
        )
        self.assertEqual(
            self.attacker_protocol.acks,
            [],
            "The replayed session_id must not be acknowledged",
        )
        self.assertTrue(
            any(
                "owned by another client" in err
                for err in self.attacker_protocol.errors
            ),
            f"Expected an ownership error; got {self.attacker_protocol.errors!r}",
        )

    def test_replay_of_unowned_seeded_session_is_rejected(self) -> None:
        """The exact PoC shape (no recorded owner) must also be rejected.

        The published PoC injects a stale ``CompletedSession`` directly
        into ``session_manager.sessions`` without registering an owner.
        The fix must refuse to bind that orphan entry to a WebSocket
        peer at access time, otherwise the attacker still receives the
        injected ``results``.
        """
        victim_session_id = "constellation-demo@task_001"
        completed = _CompletedSession(
            {"secret": "victim-result", "device": "victim-device"}
        )
        self.session_manager.sessions[victim_session_id] = completed
        # No entry in ``_session_owners`` — mirror the PoC exactly.

        replay = ClientMessage(
            type=ClientMessageType.TASK,
            status=TaskStatus.CONTINUE,
            client_type=ClientType.DEVICE,
            client_id="attacker-device",
            request="attacker replay request",
            session_id=victim_session_id,
            task_name="attacker-task",
        )

        _run(
            self.handler.handle_message(
                replay.model_dump_json(),
                registered_client_id="attacker-device",
                registered_client_type=ClientType.DEVICE,
            )
        )
        _run(asyncio.sleep(0.05))

        self.assertEqual(completed.run_calls, 0)
        self.assertEqual(self.attacker_protocol.task_ends, [])
        self.assertEqual(self.attacker_protocol.acks, [])
        self.assertTrue(
            any(
                "owned by another client" in err
                for err in self.attacker_protocol.errors
            ),
            f"Expected an ownership error; got {self.attacker_protocol.errors!r}",
        )


class CommandResultUnownedSquatTests(unittest.TestCase):
    """The ``COMMAND_RESULTS`` path must never create a session.

    Regression tests for the unowned-session squat: the WebSocket
    ``COMMAND_RESULTS`` handler previously routed through
    ``get_or_create_session(session_id, local=self.local)`` with no
    ``owner_client_id``. Because the message type has no role gate, any
    authenticated peer could supply an attacker-chosen ``session_id`` and
    inject an *unowned* session into the shared store. The ownership
    defense then rejected the legitimate owner forever (persistent DoS),
    and distinct IDs produced unbounded phantom sessions (resource
    exhaustion).

    After the fix the handler looks the session up only, drops the
    message when absent, and rejects results from a non-owner.
    """

    _saved_modules: Dict[str, Any] = {}

    @classmethod
    def setUpClass(cls) -> None:
        session_manager_module, handler_module, saved = _load_real_modules()
        cls._saved_modules = saved
        cls._SessionManager = session_manager_module.SessionManager
        cls._SessionOwnershipError = session_manager_module.SessionOwnershipError
        cls._UFOWebSocketHandler = handler_module.UFOWebSocketHandler

    @classmethod
    def tearDownClass(cls) -> None:
        for name, mod in cls._saved_modules.items():
            sys.modules[name] = mod

    def setUp(self) -> None:
        _new_loop()
        self.session_manager = self._SessionManager(platform_override="windows")
        self.client_manager = ClientConnectionManager()
        self.handler = self._UFOWebSocketHandler(
            self.client_manager, self.session_manager, local=False
        )
        self.attacker_protocol = _RecorderProtocol("attacker-device")
        self.client_manager.add_client(
            client_id="attacker-device",
            platform="windows",
            ws=object(),
            client_type=ClientType.DEVICE,
            metadata={},
            transport=None,
            task_protocol=self.attacker_protocol,
        )

    def _send_command_results(self, session_id: str) -> None:
        msg = ClientMessage(
            type=ClientMessageType.COMMAND_RESULTS,
            status=TaskStatus.CONTINUE,
            client_type=ClientType.DEVICE,
            client_id="attacker-device",
            session_id=session_id,
            prev_response_id="resp-1",
            action_results=[],
        )
        _run(
            self.handler.handle_message(
                msg.model_dump_json(),
                registered_client_id="attacker-device",
                registered_client_type=ClientType.DEVICE,
            )
        )

    def test_get_session_never_creates(self) -> None:
        """The lookup-only accessor returns None and creates nothing."""
        result = self.session_manager.get_session("does-not-exist")
        self.assertIsNone(result)
        self.assertNotIn("does-not-exist", self.session_manager.sessions)

    def test_command_results_does_not_inject_unowned_session(self) -> None:
        """An attacker ``COMMAND_RESULTS`` must not create a session."""
        victim_session_id = "constellation-demo@task_001"

        self._send_command_results(victim_session_id)

        # No phantom session and no orphan owner/result-sender entries.
        self.assertNotIn(victim_session_id, self.session_manager.sessions)
        self.assertNotIn(victim_session_id, self.session_manager._session_owners)
        self.assertNotIn(
            victim_session_id, self.session_manager._session_result_senders
        )

    def test_unbounded_phantom_sessions_are_not_created(self) -> None:
        """Many distinct ``session_id``s must not accumulate in the store."""
        for i in range(50):
            self._send_command_results(f"phantom@task_{i}")

        self.assertEqual(len(self.session_manager.sessions), 0)

    def test_legitimate_owner_not_locked_out_after_squat_attempt(self) -> None:
        """The victim can still claim its ``session_id`` after a squat try."""
        victim_session_id = "constellation-demo@task_001"

        # Attacker attempts the squat via COMMAND_RESULTS.
        self._send_command_results(victim_session_id)

        # The legitimate owner now creates the session via the TASK path
        # shape; this must NOT raise ``SessionOwnershipError``. Stub the
        # factory so we exercise the ownership logic without building a
        # full service session (which needs a live protocol).
        self.session_manager.session_factory.create_service_session = (
            lambda task, should_evaluate, id, request, task_protocol, platform_override: _CompletedSession(
                {}
            )
        )
        session = self.session_manager.get_or_create_session(
            session_id=victim_session_id,
            task_name="demo",
            request="legit",
            platform_override="windows",
            owner_client_id="victim-constellation",
        )
        self.assertIsNotNone(session)
        self.assertEqual(
            self.session_manager._session_owners[victim_session_id],
            "victim-constellation",
        )

    def test_result_sender_binding_authorizes_only_executor(self) -> None:
        """Only the registered executor may return command results."""
        session_id = "sess-1"
        self.session_manager.register_result_sender(session_id, "device-A")

        self.assertTrue(
            self.session_manager.is_authorized_result_sender(session_id, "device-A")
        )
        self.assertFalse(
            self.session_manager.is_authorized_result_sender(session_id, "device-B")
        )
        # Unknown session / missing identity are never authorized.
        self.assertFalse(
            self.session_manager.is_authorized_result_sender("other", "device-A")
        )
        self.assertFalse(
            self.session_manager.is_authorized_result_sender(session_id, None)
        )

    def test_remove_session_clears_result_sender_binding(self) -> None:
        """``remove_session`` drops the result-sender binding too."""
        session_id = "sess-2"
        self.session_manager.register_result_sender(session_id, "device-A")
        self.session_manager.sessions[session_id] = _CompletedSession({})

        self.session_manager.remove_session(session_id)

        self.assertNotIn(
            session_id, self.session_manager._session_result_senders
        )


if __name__ == "__main__":
    unittest.main()
