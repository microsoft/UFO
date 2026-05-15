"""
Regression tests for the WebSocket role/identity-spoofing hardening.

These tests pin behavior that fixes the vulnerability where:

1. A connection registered as a ``DEVICE`` could send a later ``TASK``
   message claiming ``client_type=CONSTELLATION`` and target a peer
   device. The server trusted the wire-supplied role and ``target_id``
   rather than the role bound to the connection at registration.

2. Re-using an existing ``client_id`` in
   :meth:`ClientConnectionManager.add_client` silently overwrote the
   live client's stored ``websocket``, role, and task protocol.

The tests exercise the real ``UFOWebSocketHandler`` and
``ClientConnectionManager`` against in-memory recorder protocols, the
same way the published PoC does.
"""

from __future__ import annotations

import asyncio
import os
import sys
import types
import unittest
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List


REPO_ROOT = Path(__file__).resolve().parents[2]


def _stub_module(name: str, attrs: dict[str, Any] | None = None) -> types.ModuleType:
    """Register a stub module so that deep imports succeed without the real package."""
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

    # ``art`` is only used for banner text and is irrelevant to this test.
    if "art" not in sys.modules:
        art_mod = types.ModuleType("art")
        art_mod.text2art = lambda *args, **kwargs: ""
        sys.modules["art"] = art_mod

    # ``ufo.module.basic`` (transitively imported via ``SessionManager``)
    # pulls in heavy Windows automation and LLM packages that are
    # irrelevant to the WebSocket identity/role enforcement under test.
    # Stub the smallest set of modules that the handler imports
    # directly so that import succeeds in trimmed environments.

    class _SessionManagerStub:  # pragma: no cover - shape stub only
        pass

    class _SessionOwnershipErrorStub(PermissionError):  # pragma: no cover
        """Stub matching the real ``SessionOwnershipError`` shape."""

        def __init__(self, session_id="", owner="", attempted_by=""):
            self.session_id = session_id
            self.owner = owner
            self.attempted_by = attempted_by
            super().__init__(session_id)

    sm_mod = _stub_module("ufo.server.services.session_manager")
    sm_mod.SessionManager = _SessionManagerStub
    sm_mod.SessionOwnershipError = _SessionOwnershipErrorStub

    class _WebSocketCommandDispatcherStub:  # pragma: no cover
        pass

    dispatcher_mod = _stub_module("ufo.module.dispatcher")
    dispatcher_mod.WebSocketCommandDispatcher = _WebSocketCommandDispatcherStub

    # ``ufo.utils`` is small but the package's ``__init__`` imports
    # pywinauto. Inject a minimal stub exposing only the function we
    # actually need (``sanitize_task_name``).
    if "ufo.utils" not in sys.modules:
        utils_mod = types.ModuleType("ufo.utils")

        def _passthrough_sanitize(name, fallback=None):
            return name or (fallback or "task")

        utils_mod.sanitize_task_name = _passthrough_sanitize
        sys.modules["ufo.utils"] = utils_mod


_ensure_repo_on_path()


from aip.messages import (  # noqa: E402
    ClientMessage,
    ClientMessageType,
    ClientType,
    TaskStatus,
)
from ufo.server.services.client_connection_manager import (  # noqa: E402
    ClientConnectionManager,
    DuplicateClientError,
)
from ufo.server.ws.handler import UFOWebSocketHandler  # noqa: E402


@dataclass
class RecorderProtocol:
    """In-memory stand-in for an AIP TaskExecutionProtocol."""

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


class RecordingSessionManager:
    """Captures ``execute_task_async`` invocations without running any."""

    def __init__(self) -> None:
        self.calls: List[Dict[str, Any]] = []

    async def execute_task_async(
        self,
        session_id: str,
        task_name: str,
        request: str,
        task_protocol: Any = None,
        platform_override: str | None = None,
        callback: Any = None,
        owner_client_id: str | None = None,
    ) -> str:
        self.calls.append(
            {
                "session_id": session_id,
                "task_name": task_name,
                "request": request,
                "task_protocol": task_protocol,
                "platform_override": platform_override,
                "callback": callback,
                "owner_client_id": owner_client_id,
            }
        )
        return session_id


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


def _new_loop() -> None:
    asyncio.set_event_loop(asyncio.new_event_loop())


class RoleSpoofRejectionTests(unittest.TestCase):
    """Connection-bound identity must override wire-supplied identity."""

    def setUp(self) -> None:
        _new_loop()
        self.session_manager = RecordingSessionManager()
        self.client_manager = ClientConnectionManager()
        self.handler = UFOWebSocketHandler(self.client_manager, self.session_manager)

        self.victim_protocol = RecorderProtocol("victim-device")
        self.attacker_protocol = RecorderProtocol("attacker-device")

        self.client_manager.add_client(
            "victim-device",
            "windows",
            object(),
            ClientType.DEVICE,
            task_protocol=self.victim_protocol,
        )
        self.client_manager.add_client(
            "attacker-device",
            "linux",
            object(),
            ClientType.DEVICE,
            task_protocol=self.attacker_protocol,
        )

        # Mirror the per-connection state that ``connect()`` would set.
        self.handler.task_protocol = self.attacker_protocol

    def _forged_constellation_task(self) -> str:
        forged = ClientMessage(
            type=ClientMessageType.TASK,
            status=TaskStatus.OK,
            client_type=ClientType.CONSTELLATION,
            client_id="attacker-device",
            target_id="victim-device",
            request="open the confidential spreadsheet",
            task_name="role-spoofed-task",
            session_id="session-role-spoof",
        )
        return forged.model_dump_json()

    def test_forged_constellation_role_is_rejected(self) -> None:
        """The PoC's forged TASK must not dispatch any session."""
        _run(
            self.handler.handle_message(
                self._forged_constellation_task(),
                registered_client_id="attacker-device",
                registered_client_type=ClientType.DEVICE,
            )
        )

        self.assertEqual(
            self.session_manager.calls,
            [],
            "Forged constellation TASK must not invoke execute_task_async",
        )
        self.assertEqual(
            self.attacker_protocol.acks,
            [],
            "Forged TASK must not be acknowledged",
        )
        self.assertTrue(
            any("client_type" in err for err in self.attacker_protocol.errors),
            "An explanatory error must be returned for the role spoof",
        )

    def test_spoofed_client_id_is_rejected(self) -> None:
        """A connection cannot claim a different client_id at message time."""
        spoof = ClientMessage(
            type=ClientMessageType.TASK,
            status=TaskStatus.OK,
            client_type=ClientType.DEVICE,
            client_id="victim-device",  # not the registered identity
            request="exfiltrate-as-peer",
            task_name="impersonation",
            session_id="session-impersonation",
        )

        _run(
            self.handler.handle_message(
                spoof.model_dump_json(),
                registered_client_id="attacker-device",
                registered_client_type=ClientType.DEVICE,
            )
        )

        self.assertEqual(self.session_manager.calls, [])
        self.assertTrue(
            any("client_id" in err for err in self.attacker_protocol.errors),
            "An explanatory error must be returned for the client_id spoof",
        )

    def test_device_cannot_target_peer_device(self) -> None:
        """Defense-in-depth: even if role is right, target_id must equal client_id."""
        cross_target = ClientMessage(
            type=ClientMessageType.TASK,
            status=TaskStatus.OK,
            client_type=ClientType.DEVICE,
            client_id="attacker-device",
            target_id="victim-device",
            request="route-to-peer",
            task_name="peer-target",
            session_id="session-peer-target",
        )

        _run(
            self.handler.handle_message(
                cross_target.model_dump_json(),
                registered_client_id="attacker-device",
                registered_client_type=ClientType.DEVICE,
            )
        )

        self.assertEqual(self.session_manager.calls, [])
        self.assertTrue(
            any("target" in err.lower() for err in self.attacker_protocol.errors),
            "An explanatory error must be returned for cross-device targeting",
        )

    def test_legitimate_device_task_still_dispatches(self) -> None:
        """Non-spoofed device task on the same connection still works."""
        legit = ClientMessage(
            type=ClientMessageType.TASK,
            status=TaskStatus.OK,
            client_type=ClientType.DEVICE,
            client_id="attacker-device",  # matches registered identity
            request="normal request",
            task_name="legit-task",
            session_id="session-legit",
        )

        _run(
            self.handler.handle_message(
                legit.model_dump_json(),
                registered_client_id="attacker-device",
                registered_client_type=ClientType.DEVICE,
            )
        )

        self.assertEqual(len(self.session_manager.calls), 1)
        call = self.session_manager.calls[0]
        self.assertIs(call["task_protocol"], self.attacker_protocol)
        self.assertEqual(call["platform_override"], "linux")
        self.assertEqual(self.attacker_protocol.acks, ["session-legit"])

    def test_unregistered_connection_refuses_task(self) -> None:
        """Messages without a server-bound identity must not dispatch tasks."""
        _run(
            self.handler.handle_message(
                self._forged_constellation_task(),
                # No registered identity -- e.g. direct call without connect().
                registered_client_id=None,
                registered_client_type=None,
            )
        )

        self.assertEqual(self.session_manager.calls, [])
        self.assertTrue(
            any(
                "not registered" in err.lower() or "privileged" in err.lower()
                for err in self.attacker_protocol.errors
            ),
            "Unregistered connections must be rejected explicitly",
        )


class DuplicateClientRegistrationTests(unittest.TestCase):
    """``add_client`` must not silently overwrite a live client entry."""

    def test_duplicate_client_id_is_rejected(self) -> None:
        manager = ClientConnectionManager()
        first_socket = object()
        second_socket = object()

        manager.add_client(
            "shadowed-device",
            "windows",
            first_socket,
            ClientType.DEVICE,
        )

        with self.assertRaises(DuplicateClientError):
            manager.add_client(
                "shadowed-device",
                "linux",
                second_socket,
                ClientType.CONSTELLATION,
            )

        # The original mapping must remain intact.
        self.assertIs(manager.get_client("shadowed-device"), first_socket)
        self.assertEqual(
            manager.get_client_type("shadowed-device"),
            ClientType.DEVICE,
        )

    def test_remove_then_readd_is_allowed(self) -> None:
        """Legitimate reconnect path: removing first then re-adding works."""
        manager = ClientConnectionManager()
        first_socket = object()
        second_socket = object()

        manager.add_client(
            "reconnecting-device",
            "windows",
            first_socket,
            ClientType.DEVICE,
        )
        manager.remove_client("reconnecting-device")
        manager.add_client(
            "reconnecting-device",
            "windows",
            second_socket,
            ClientType.DEVICE,
        )

        self.assertIs(manager.get_client("reconnecting-device"), second_socket)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
