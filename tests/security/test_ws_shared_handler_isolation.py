"""Cross-client WebSocket response isolation regression tests.

These tests cover the cross-client response hijack reported against the
shared :class:`UFOWebSocketHandler`. They exercise the real
``connect()`` / ``handler.handle_message()`` code paths with in-process
``FakeWebSocket`` stand-ins, mirroring the published PoC.

A regression in the fix would reveal itself as a response sent on a
peer connection's transport (e.g. the most recently connected client
receiving another client's ``device_info_response`` or task ACK).
"""

from __future__ import annotations

import asyncio
import os
import sys
import types
import unittest
from pathlib import Path
from typing import Any, List


# Allow importing the in-tree package without installation, mirroring
# the layout used by the other security regression tests.
REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def _stub_module(name: str) -> types.ModuleType:
    if name in sys.modules:
        return sys.modules[name]
    mod = types.ModuleType(name)
    sys.modules[name] = mod
    return mod


# ``art`` is an optional dependency pulled in transitively by some
# downstream modules. Stub it out so the security tests run in a slim
# CI environment.
if "art" not in sys.modules:
    art_mod = types.ModuleType("art")
    art_mod.text2art = lambda *args, **kwargs: ""  # type: ignore[attr-defined]
    sys.modules["art"] = art_mod


# ``ufo.module.basic`` (transitively imported via ``SessionManager``)
# pulls in pywinauto / LLM packages that are irrelevant to the
# WebSocket isolation property under test. Inject the smallest set of
# stubs the handler imports directly so the import chain succeeds in
# trimmed environments — mirroring ``tests/security/test_ws_role_spoof.py``.


class _SessionManagerStub:  # pragma: no cover - shape stub only
    pass


class _SessionOwnershipErrorStub(PermissionError):  # pragma: no cover
    """Stub for :class:`ufo.server.services.session_manager.SessionOwnershipError`."""

    def __init__(self, session_id="", owner="", attempted_by=""):
        self.session_id = session_id
        self.owner = owner
        self.attempted_by = attempted_by
        super().__init__(session_id)


_sm_mod = _stub_module("ufo.server.services.session_manager")
_sm_mod.SessionManager = _SessionManagerStub  # type: ignore[attr-defined]
_sm_mod.SessionOwnershipError = _SessionOwnershipErrorStub  # type: ignore[attr-defined]


class _WebSocketCommandDispatcherStub:  # pragma: no cover
    pass


_dispatcher_mod = _stub_module("ufo.module.dispatcher")
_dispatcher_mod.WebSocketCommandDispatcher = (  # type: ignore[attr-defined]
    _WebSocketCommandDispatcherStub
)


if "ufo.utils" not in sys.modules:
    _utils_mod = types.ModuleType("ufo.utils")

    def _passthrough_sanitize(name, fallback=None):
        return name or (fallback or "task")

    _utils_mod.sanitize_task_name = _passthrough_sanitize  # type: ignore[attr-defined]
    sys.modules["ufo.utils"] = _utils_mod


from starlette.websockets import WebSocketState  # noqa: E402

from aip.messages import (  # noqa: E402
    ClientMessage,
    ClientMessageType,
    ClientType,
    ServerMessage,
    TaskStatus,
)
from ufo.server.services.client_connection_manager import (  # noqa: E402
    ClientConnectionManager,
)
from ufo.server.ws.handler import UFOWebSocketHandler  # noqa: E402


class _FakeWebSocket:
    """Minimal in-process WebSocket stand-in.

    Each instance buffers a queue of incoming JSON strings and records
    the strings sent back to it. ``client_state`` / ``application_state``
    are required by ``starlette`` introspection.
    """

    def __init__(self, incoming: List[str], label: str) -> None:
        self.incoming = list(incoming)
        self.sent: List[str] = []
        self.label = label
        self.client_state = WebSocketState.CONNECTED
        self.application_state = WebSocketState.CONNECTED

    async def accept(self) -> None:  # pragma: no cover - trivial
        return None

    async def receive_text(self) -> str:
        if not self.incoming:
            raise RuntimeError(f"no incoming message left for {self.label}")
        return self.incoming.pop(0)

    async def send_text(self, data: str) -> None:
        self.sent.append(data)

    async def close(self, *args: Any, **kwargs: Any) -> None:
        self.client_state = WebSocketState.DISCONNECTED
        self.application_state = WebSocketState.DISCONNECTED


class _DummySessionManager:
    """Captures ``execute_task_async`` invocations."""

    def __init__(self) -> None:
        self.calls: List[dict] = []

    async def execute_task_async(self, **kwargs: Any) -> str:
        self.calls.append(kwargs)
        return kwargs["session_id"]


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


def _new_loop() -> None:
    asyncio.set_event_loop(asyncio.new_event_loop())


class SharedHandlerCrossClientIsolationTests(unittest.TestCase):
    """The shared handler must never route responses across clients."""

    def setUp(self) -> None:
        _new_loop()

    def test_device_info_response_is_sent_only_to_requester(self) -> None:
        """A constellation's device-info response stays on its own socket.

        Regression test for the published PoC where a third client
        connecting after the requesting constellation would receive the
        device_info_response intended for the constellation.
        """
        client_manager = ClientConnectionManager()
        handler = UFOWebSocketHandler(client_manager, _DummySessionManager())

        device_reg = ClientMessage(
            type=ClientMessageType.REGISTER,
            status=TaskStatus.OK,
            client_type=ClientType.DEVICE,
            client_id="device-1",
            metadata={
                "platform": "windows",
                "system_info": {"hostname": "victim-host"},
            },
        )
        constellation_reg = ClientMessage(
            type=ClientMessageType.REGISTER,
            status=TaskStatus.OK,
            client_type=ClientType.CONSTELLATION,
            client_id="constellation-1",
            target_id="device-1",
            metadata={"platform": "windows"},
        )
        observer_reg = ClientMessage(
            type=ClientMessageType.REGISTER,
            status=TaskStatus.OK,
            client_type=ClientType.DEVICE,
            client_id="observer-1",
            metadata={"platform": "linux"},
        )

        ws_device = _FakeWebSocket(
            [device_reg.model_dump_json()], "device-1"
        )
        ws_constellation = _FakeWebSocket(
            [constellation_reg.model_dump_json()], "constellation-1"
        )
        ws_observer = _FakeWebSocket(
            [observer_reg.model_dump_json()], "observer-1"
        )

        ctx_device = _run(handler.connect(ws_device))
        ctx_constellation = _run(handler.connect(ws_constellation))
        ctx_observer = _run(handler.connect(ws_observer))

        # Snapshot how many messages each socket has already received
        # from the registration handshake, so we can detect any *new*
        # message delivered as part of the device-info request flow.
        device_sent_before = len(ws_device.sent)
        observer_sent_before = len(ws_observer.sent)

        info_request = ClientMessage(
            type=ClientMessageType.DEVICE_INFO_REQUEST,
            status=TaskStatus.OK,
            client_type=ClientType.CONSTELLATION,
            client_id="constellation-1",
            target_id="device-1",
            request_id="req-123",
        )

        _run(
            handler.handle_message(
                info_request.model_dump_json(), ctx_constellation
            )
        )

        # The observer (last-connected) must NOT have received anything
        # new — this is exactly the cross-client hijack the PoC
        # demonstrated.
        self.assertEqual(
            len(ws_observer.sent),
            observer_sent_before,
            "observer received a leaked device_info_response",
        )
        # Nor should the device get a misrouted response.
        self.assertEqual(
            len(ws_device.sent),
            device_sent_before,
            "device received a leaked device_info_response",
        )

        # The requesting constellation IS the recipient.
        last = ServerMessage.model_validate_json(ws_constellation.sent[-1])
        self.assertEqual(last.type, "device_info_response")
        self.assertEqual(last.result, {"hostname": "victim-host"})

    def test_task_ack_is_sent_only_to_requesting_device(self) -> None:
        """A device's TASK ACK stays on the requesting device's socket.

        Regression test for the second half of the PoC where the
        most-recently-connected observer received the task ACK intended
        for an earlier device.
        """
        client_manager = ClientConnectionManager()
        session_manager = _DummySessionManager()
        handler = UFOWebSocketHandler(client_manager, session_manager)

        device_reg = ClientMessage(
            type=ClientMessageType.REGISTER,
            status=TaskStatus.OK,
            client_type=ClientType.DEVICE,
            client_id="device-1",
            metadata={"platform": "windows"},
        )
        observer_reg = ClientMessage(
            type=ClientMessageType.REGISTER,
            status=TaskStatus.OK,
            client_type=ClientType.DEVICE,
            client_id="observer-2",
            metadata={"platform": "linux"},
        )

        ws_device = _FakeWebSocket(
            [device_reg.model_dump_json()], "device-1"
        )
        ws_observer = _FakeWebSocket(
            [observer_reg.model_dump_json()], "observer-2"
        )

        ctx_device = _run(handler.connect(ws_device))
        ctx_observer = _run(handler.connect(ws_observer))

        observer_sent_before = len(ws_observer.sent)
        device_sent_before = len(ws_device.sent)

        task_msg = ClientMessage(
            type=ClientMessageType.TASK,
            status=TaskStatus.CONTINUE,
            client_type=ClientType.DEVICE,
            client_id="device-1",
            request="do thing",
            task_name="demo",
            session_id="sess-1",
        )

        _run(handler.handle_message(task_msg.model_dump_json(), ctx_device))

        # The session must have been dispatched on behalf of device-1.
        self.assertEqual(len(session_manager.calls), 1)
        self.assertEqual(session_manager.calls[0]["session_id"], "sess-1")

        # The observer (last-connected) must NOT have received any ACK.
        self.assertEqual(
            len(ws_observer.sent),
            observer_sent_before,
            "observer received a leaked task ACK",
        )
        # The requesting device IS the recipient of the ACK.
        self.assertGreater(len(ws_device.sent), device_sent_before)
        ack_msg = ServerMessage.model_validate_json(ws_device.sent[-1])
        self.assertEqual(ack_msg.session_id, "sess-1")


class DeviceInfoRequestAuthorizationTests(unittest.TestCase):
    """``DEVICE_INFO_REQUEST`` must enforce caller authorization.

    Regression tests for the cross-device disclosure where a client
    registered as a ``DEVICE`` could read any other device's stored
    ``system_info`` simply by naming it in ``target_id``. The dispatcher
    authenticated the caller's role but never checked whether that role
    (or that target) was permitted to run the operation.
    """

    def setUp(self) -> None:
        _new_loop()

    @staticmethod
    def _register_device(
        handler: UFOWebSocketHandler,
        client_id: str,
        *,
        platform: str = "windows",
        system_info: dict | None = None,
    ):
        metadata: dict = {"platform": platform}
        if system_info is not None:
            metadata["system_info"] = system_info
        reg = ClientMessage(
            type=ClientMessageType.REGISTER,
            status=TaskStatus.OK,
            client_type=ClientType.DEVICE,
            client_id=client_id,
            metadata=metadata,
        )
        ws = _FakeWebSocket([reg.model_dump_json()], client_id)
        ctx = _run(handler.connect(ws))
        return ctx, ws

    @staticmethod
    def _register_constellation(
        handler: UFOWebSocketHandler,
        client_id: str,
        *,
        target_id: str | None = None,
    ):
        reg = ClientMessage(
            type=ClientMessageType.REGISTER,
            status=TaskStatus.OK,
            client_type=ClientType.CONSTELLATION,
            client_id=client_id,
            target_id=target_id,
            metadata={"platform": "windows"},
        )
        ws = _FakeWebSocket([reg.model_dump_json()], client_id)
        ctx = _run(handler.connect(ws))
        return ctx, ws

    def test_device_info_request_rejected_for_device_role(self) -> None:
        """A DEVICE caller must not read another device's system_info."""
        client_manager = ClientConnectionManager()
        handler = UFOWebSocketHandler(client_manager, _DummySessionManager())

        victim_info = {
            "hostname": "FINANCE-WS-07",
            "ip_address": "10.4.12.37",
            "tags": ["finance", "pci"],
        }
        self._register_device(
            handler, "victim-device-A", system_info=victim_info
        )
        ctx_attacker, ws_attacker = self._register_device(
            handler, "attacker-device-B", platform="linux"
        )

        sent_before = len(ws_attacker.sent)

        info_request = ClientMessage(
            type=ClientMessageType.DEVICE_INFO_REQUEST,
            status=TaskStatus.OK,
            client_type=ClientType.DEVICE,
            client_id="attacker-device-B",
            target_id="victim-device-A",
            request_id="req-1",
        )

        _run(handler.handle_message(info_request.model_dump_json(), ctx_attacker))

        # The attacker must receive an error, never a device_info_response,
        # and the victim's system_info must not appear on the wire.
        self.assertGreater(len(ws_attacker.sent), sent_before)
        last = ServerMessage.model_validate_json(ws_attacker.sent[-1])
        self.assertNotEqual(last.type, "device_info_response")
        for frame in ws_attacker.sent[sent_before:]:
            self.assertNotIn("FINANCE-WS-07", frame)
            self.assertNotIn("10.4.12.37", frame)

    def test_device_info_request_allowed_for_constellation(self) -> None:
        """A constellation may read the info of the device it manages."""
        client_manager = ClientConnectionManager()
        handler = UFOWebSocketHandler(client_manager, _DummySessionManager())

        device_info = {"hostname": "managed-host", "ip_address": "10.0.0.5"}
        self._register_device(
            handler, "device-1", system_info=device_info
        )
        ctx_constellation, ws_constellation = self._register_constellation(
            handler, "constellation-1", target_id="device-1"
        )

        info_request = ClientMessage(
            type=ClientMessageType.DEVICE_INFO_REQUEST,
            status=TaskStatus.OK,
            client_type=ClientType.CONSTELLATION,
            client_id="constellation-1",
            target_id="device-1",
            request_id="req-2",
        )

        _run(
            handler.handle_message(
                info_request.model_dump_json(), ctx_constellation
            )
        )

        last = ServerMessage.model_validate_json(ws_constellation.sent[-1])
        self.assertEqual(last.type, "device_info_response")
        self.assertEqual(last.result, device_info)

    def test_constellation_cannot_query_unrelated_device(self) -> None:
        """A constellation scoped to one device cannot read another."""
        client_manager = ClientConnectionManager()
        handler = UFOWebSocketHandler(client_manager, _DummySessionManager())

        unrelated_info = {"hostname": "other-host", "ip_address": "10.9.9.9"}
        self._register_device(handler, "device-1")
        self._register_device(
            handler, "device-2", system_info=unrelated_info
        )
        ctx_constellation, ws_constellation = self._register_constellation(
            handler, "constellation-1", target_id="device-1"
        )

        sent_before = len(ws_constellation.sent)

        info_request = ClientMessage(
            type=ClientMessageType.DEVICE_INFO_REQUEST,
            status=TaskStatus.OK,
            client_type=ClientType.CONSTELLATION,
            client_id="constellation-1",
            target_id="device-2",
            request_id="req-3",
        )

        _run(
            handler.handle_message(
                info_request.model_dump_json(), ctx_constellation
            )
        )

        self.assertGreater(len(ws_constellation.sent), sent_before)
        last = ServerMessage.model_validate_json(ws_constellation.sent[-1])
        self.assertNotEqual(last.type, "device_info_response")
        for frame in ws_constellation.sent[sent_before:]:
            self.assertNotIn("other-host", frame)
            self.assertNotIn("10.9.9.9", frame)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
