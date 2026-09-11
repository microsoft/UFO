import asyncio
import os
import socket
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, Optional
from unittest.mock import AsyncMock

import pytest
from fastmcp import Client, FastMCP
from fastmcp.client.transports import StreamableHttpTransport

from ufo.client.mcp.http_servers.mobile_mcp_server import (
    create_mobile_action_server,
    create_mobile_data_collection_server,
)
from ufo.client.mcp.mcp_server_manager import HTTPMCPServer


TEST_API_KEY = "test-mobile-mcp-api-key"


@dataclass(frozen=True)
class RunningMobileServer:
    url: str
    marker: Path


def _get_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
        listener.bind(("127.0.0.1", 0))
        return listener.getsockname()[1]


def _wait_for_server(process: subprocess.Popen, port: int) -> None:
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        if process.poll() is not None:
            stdout, stderr = process.communicate()
            pytest.fail(
                f"Mobile MCP server exited during startup.\nstdout:\n{stdout}\nstderr:\n{stderr}"
            )

        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.2):
                return
        except OSError:
            time.sleep(0.05)

    pytest.fail("Timed out waiting for the Mobile MCP server to start.")


def _create_fake_adb(tmp_path: Path) -> Path:
    if os.name == "nt":
        fake_adb = tmp_path / "fake_adb.cmd"
        fake_adb.write_text(
            '@echo off\r\n>>"%FAKE_ADB_MARKER%" echo %*\r\n'
            'if "%1"=="pull" (>"%~3" echo fake-png)\r\n',
            encoding="utf-8",
        )
        return fake_adb

    fake_adb = tmp_path / "fake_adb"
    fake_adb.write_text(
        '#!/bin/sh\nprintf \'%s\\n\' "$*" >> "$FAKE_ADB_MARKER"\n'
        'if [ "$1" = "pull" ]; then printf \'fake-png\' > "$3"; fi\n',
        encoding="utf-8",
    )
    fake_adb.chmod(0o700)
    return fake_adb


def _run_mobile_server(
    tmp_path: Path, factory_name: str
) -> Iterator[RunningMobileServer]:
    port = _get_free_port()
    marker = tmp_path / "fake_adb_args.txt"
    fake_adb = _create_fake_adb(tmp_path)
    environment = os.environ.copy()
    environment["UFO_MCP_API_KEY"] = TEST_API_KEY
    environment["FAKE_ADB_MARKER"] = str(marker)

    server_code = (
        f"from ufo.client.mcp.http_servers.mobile_mcp_server import {factory_name}; "
        f"{factory_name}(host='127.0.0.1', port={port}, "
        f"adb_path={str(fake_adb)!r})"
    )
    process = subprocess.Popen(
        [sys.executable, "-c", server_code],
        env=environment,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    try:
        _wait_for_server(process, port)
        yield RunningMobileServer(
            url=f"http://127.0.0.1:{port}/mcp", marker=marker
        )
    finally:
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)


@pytest.fixture
def mobile_action_server(tmp_path: Path) -> Iterator[RunningMobileServer]:
    yield from _run_mobile_server(tmp_path, "create_mobile_action_server")


@pytest.fixture
def mobile_data_server(tmp_path: Path) -> Iterator[RunningMobileServer]:
    yield from _run_mobile_server(tmp_path, "create_mobile_data_collection_server")


async def _call_tap(url: str, credential: Optional[str]):
    transport = StreamableHttpTransport(url, auth=credential)
    async with Client(transport) as client:
        return await client.call_tool("tap", {"x": 17, "y": 29})


async def _capture_screenshot(url: str, credential: Optional[str]):
    transport = StreamableHttpTransport(url, auth=credential)
    async with Client(transport) as client:
        return await client.call_tool("capture_screenshot", {})


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "credential", [None, "incorrect-key"], ids=["missing", "incorrect"]
)
async def test_unauthorized_mobile_action_is_rejected_before_adb(
    mobile_action_server: RunningMobileServer, credential: Optional[str]
) -> None:
    with pytest.raises(Exception):
        await _call_tap(mobile_action_server.url, credential)

    assert not mobile_action_server.marker.exists()


@pytest.mark.asyncio
async def test_authenticated_mobile_action_reaches_fake_adb(
    mobile_action_server: RunningMobileServer,
) -> None:
    result = await _call_tap(mobile_action_server.url, TEST_API_KEY)

    assert result.data["success"] is True
    assert (
        mobile_action_server.marker.read_text(encoding="utf-8").strip()
        == "shell input tap 17 29"
    )


@pytest.fixture
def keyevent_server(monkeypatch: pytest.MonkeyPatch) -> FastMCP:
    servers = []
    monkeypatch.setenv("UFO_MCP_API_KEY", TEST_API_KEY)
    monkeypatch.setattr(FastMCP, "run", lambda server, **kwargs: servers.append(server))
    create_mobile_action_server(adb_path="test-adb")
    return servers[0]


@pytest.fixture
def keyevent_subprocess(monkeypatch: pytest.MonkeyPatch) -> AsyncMock:
    process = AsyncMock()
    process.returncode = 0
    process.communicate.return_value = (b"", b"")
    create_process = AsyncMock(return_value=process)
    monkeypatch.setattr(asyncio, "create_subprocess_exec", create_process)
    return create_process


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "key_code",
    [
        "KEYCODE_HOME; echo AUDIT_MARKER",
        "KEYCODE_HOME&&echo AUDIT_MARKER",
        "KEYCODE_HOME||echo AUDIT_MARKER",
        "KEYCODE_HOME|echo AUDIT_MARKER",
        "KEYCODE_HOME&echo AUDIT_MARKER",
        "KEYCODE_HOME\necho AUDIT_MARKER",
        "KEYCODE_HOME\recho AUDIT_MARKER",
        "KEYCODE_HOME$(echo AUDIT_MARKER)",
        "KEYCODE_HOME`echo AUDIT_MARKER`",
        "KEYCODE_HOME>AUDIT_MARKER",
        "KEYCODE_HOME<AUDIT_MARKER",
        "KEYCODE_HOME KEYCODE_BACK",
        "3 4",
        "KEYCODE_HOME\tKEYCODE_BACK",
        "KEYCODE_HOME\n",
        " KEYCODE_HOME",
        "KEYCODE_HOME ",
        "'KEYCODE_HOME'",
        '"KEYCODE_HOME"',
        "KEYCODE_HOME\\",
        "KEYCODE_HOME\x00",
        "KEYCODE_*",
        "$KEY_CODE",
        "--longpress",
        "-1",
        "3.0",
        "\u0663",
        "KEYCODE_H\u041eME",
        "",
    ],
)
async def test_press_key_rejects_invalid_input_before_adb(
    keyevent_server: FastMCP, keyevent_subprocess: AsyncMock, key_code: str
) -> None:
    async with Client(keyevent_server) as client:
        result = await client.call_tool("press_key", {"key_code": key_code})

    keyevent_subprocess.assert_not_called()
    assert result.data["success"] is False
    assert "invalid key code" in result.data["error"].lower()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "key_code",
    [
        "KEYCODE_HOME",
        "KEYCODE_BACK",
        "KEYCODE_ENTER",
        "KEYCODE_MENU",
        "KEYCODE_VOLUME_UP",
        "KEYCODE_3D_MODE",
        "3D_MODE",
        "HOME",
        "BACK",
        "0",
        "3",
        "66",
    ],
)
async def test_press_key_preserves_single_key_adb_arguments(
    keyevent_server: FastMCP, keyevent_subprocess: AsyncMock, key_code: str
) -> None:
    async with Client(keyevent_server) as client:
        result = await client.call_tool("press_key", {"key_code": key_code})

    assert result.data["success"] is True
    assert result.data["action"] == f"press_key({key_code})"
    keyevent_subprocess.assert_awaited_once_with(
        "test-adb",
        "shell",
        "input",
        "keyevent",
        key_code,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )


@pytest.mark.asyncio
async def test_authenticated_press_key_rejects_injection_before_adb(
    mobile_action_server: RunningMobileServer,
) -> None:
    transport = StreamableHttpTransport(mobile_action_server.url, auth=TEST_API_KEY)
    async with Client(transport) as client:
        result = await client.call_tool(
            "press_key", {"key_code": "KEYCODE_HOME; echo AUDIT_MARKER"}
        )

    assert result.data["success"] is False
    assert "invalid key code" in result.data["error"].lower()
    assert not mobile_action_server.marker.exists()


@pytest.mark.asyncio
async def test_unauthenticated_mobile_data_is_rejected_before_adb(
    mobile_data_server: RunningMobileServer,
) -> None:
    with pytest.raises(Exception):
        await _capture_screenshot(mobile_data_server.url, None)

    assert not mobile_data_server.marker.exists()


@pytest.mark.asyncio
async def test_authenticated_mobile_data_reaches_fake_adb(
    mobile_data_server: RunningMobileServer,
) -> None:
    result = await _capture_screenshot(mobile_data_server.url, TEST_API_KEY)

    assert result.data.startswith("data:image/png;base64,")
    adb_calls = mobile_data_server.marker.read_text(encoding="utf-8")
    assert "shell screencap -p /sdcard/screen_temp.png" in adb_calls
    assert "pull /sdcard/screen_temp.png" in adb_calls


@pytest.mark.parametrize(
    "factory", [create_mobile_data_collection_server, create_mobile_action_server]
)
def test_mobile_server_fails_closed_without_api_key(
    monkeypatch: pytest.MonkeyPatch, factory
) -> None:
    monkeypatch.delenv("UFO_MCP_API_KEY", raising=False)
    monkeypatch.setattr(FastMCP, "run", lambda *args, **kwargs: None)

    with pytest.raises(RuntimeError, match="UFO_MCP_API_KEY"):
        factory(host="127.0.0.1", port=0, adb_path="unused")


@pytest.mark.parametrize(
    "credential",
    [
        "${UFO_MCP_API_KEY}",
        "prefix-${UFO_MCP_API_KEY}",
        "token-$UFO_MCP_API_KEY-suffix",
    ],
)
def test_http_mcp_server_rejects_unresolved_auth_placeholder(
    credential: str,
) -> None:
    server = HTTPMCPServer(
        {
            "host": "localhost",
            "port": 8020,
            "path": "/mcp",
            "auth": credential,
        }
    )

    with pytest.raises(ValueError, match="unresolved environment variable"):
        server.start()


def test_http_mcp_server_uses_authenticated_transport() -> None:
    server = HTTPMCPServer(
        {
            "host": "localhost",
            "port": 8020,
            "path": "/mcp",
            "auth": TEST_API_KEY,
        }
    )

    server.start()

    assert isinstance(server.server, StreamableHttpTransport)
    assert server.server.auth.token.get_secret_value() == TEST_API_KEY


def test_http_mcp_server_allows_literal_dollar_in_auth() -> None:
    credential = "valid-prefix$-valid-suffix"
    server = HTTPMCPServer(
        {
            "host": "localhost",
            "port": 8020,
            "path": "/mcp",
            "auth": credential,
        }
    )

    server.start()

    assert isinstance(server.server, StreamableHttpTransport)
    assert server.server.auth.token.get_secret_value() == credential


def test_http_mcp_server_without_auth_keeps_bare_url() -> None:
    server = HTTPMCPServer(
        {"host": "localhost", "port": 8020, "path": "/mcp"}
    )

    server.start()

    assert server.server == "http://localhost:8020/mcp"