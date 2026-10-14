# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Regression tests for WebUI credential provisioning and disclosure."""

import logging
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from galaxy.webui import dependencies, server


TEST_API_KEY = "webui-regression-test-key-not-for-production"
ENV_API_KEY = "webui-environment-test-key-not-for-production"


@pytest.fixture(autouse=True)
def app_state(monkeypatch):
    state = dependencies.AppState()
    monkeypatch.setattr(dependencies, "app_state", state)
    monkeypatch.delenv("GALAXY_WEBUI_API_KEY", raising=False)
    return state


@pytest.mark.parametrize("key_source", ["state", "environment"])
def test_lifespan_does_not_disclose_api_key(
    key_source, app_state, monkeypatch, caplog, capsys
):
    if key_source == "state":
        app_state.api_key = TEST_API_KEY
    else:
        monkeypatch.setenv("GALAXY_WEBUI_API_KEY", TEST_API_KEY)
    caplog.set_level(logging.DEBUG)

    with TestClient(server.app):
        assert app_state.api_key == TEST_API_KEY

    output = capsys.readouterr()
    assert TEST_API_KEY not in output.out
    assert TEST_API_KEY not in output.err
    assert TEST_API_KEY not in caplog.text


def test_lifespan_preserves_explicit_key_over_environment(app_state, monkeypatch):
    app_state.api_key = TEST_API_KEY
    monkeypatch.setenv("GALAXY_WEBUI_API_KEY", ENV_API_KEY)

    with TestClient(server.app):
        assert app_state.api_key == TEST_API_KEY


@pytest.mark.parametrize(
    ("explicit_key", "environment_key", "expected_key"),
    [
        (TEST_API_KEY, None, TEST_API_KEY),
        (None, ENV_API_KEY, ENV_API_KEY),
        (TEST_API_KEY, ENV_API_KEY, TEST_API_KEY),
    ],
)
def test_start_server_uses_configured_key_without_disclosure(
    explicit_key, environment_key, expected_key, app_state, monkeypatch, caplog, capsys
):
    if environment_key is not None:
        monkeypatch.setenv("GALAXY_WEBUI_API_KEY", environment_key)
    caplog.set_level(logging.DEBUG)

    with patch("uvicorn.run") as run_server:
        server.start_server(api_key=explicit_key)
        run_server.assert_called_once_with(
            server.app, host="127.0.0.1", port=8000, log_level="info"
        )

    with TestClient(server.app):
        assert app_state.api_key == expected_key

    output = capsys.readouterr()
    for key in (TEST_API_KEY, ENV_API_KEY):
        assert key not in output.out
        assert key not in output.err
        assert key not in caplog.text


@pytest.mark.parametrize("entry_point", ["lifespan", "start_server"])
@pytest.mark.parametrize("environment_key", [None, ""])
def test_startup_rejects_missing_key(
    entry_point, environment_key, app_state, monkeypatch
):
    if environment_key is not None:
        monkeypatch.setenv("GALAXY_WEBUI_API_KEY", environment_key)

    with patch("uvicorn.run") as run_server:
        with pytest.raises(RuntimeError, match="GALAXY_WEBUI_API_KEY"):
            if entry_point == "lifespan":
                with TestClient(server.app):
                    pass
            else:
                server.start_server()
        run_server.assert_not_called()

    assert app_state.api_key is None


@pytest.mark.parametrize("endpoint", ["/api/authenticate", "/health"])
@pytest.mark.parametrize(
    ("key", "expected_status"),
    [(TEST_API_KEY, 200), ("incorrect-test-key", 401), (None, 422)],
)
def test_http_authentication_uses_configured_key(
    endpoint, key, expected_status, monkeypatch
):
    monkeypatch.setenv("GALAXY_WEBUI_API_KEY", TEST_API_KEY)
    headers = {"X-API-Key": key} if key is not None else {}

    with TestClient(server.app) as client:
        method = "POST" if endpoint == "/api/authenticate" else "GET"
        response = client.request(method, endpoint, headers=headers)

    assert response.status_code == expected_status
    assert TEST_API_KEY not in response.text
    if endpoint == "/api/authenticate" and expected_status == 200:
        assert response.json() == {"authenticated": True}


@pytest.mark.parametrize("key", [TEST_API_KEY, "incorrect-test-key", None])
def test_websocket_authentication_uses_configured_key(key, monkeypatch):
    monkeypatch.setenv("GALAXY_WEBUI_API_KEY", TEST_API_KEY)
    url = "/ws" if key is None else f"/ws?token={key}"

    with TestClient(server.app) as client:
        if key == TEST_API_KEY:
            with client.websocket_connect(url) as websocket:
                assert websocket.receive_json()["type"] == "welcome"
        else:
            with pytest.raises(WebSocketDisconnect) as error:
                with client.websocket_connect(url):
                    pass
            assert error.value.code == 1008


def test_root_does_not_expose_configured_key(monkeypatch):
    monkeypatch.setenv("GALAXY_WEBUI_API_KEY", TEST_API_KEY)

    with TestClient(server.app) as client:
        response = client.get("/")

    assert response.status_code == 200
    assert TEST_API_KEY not in response.text
