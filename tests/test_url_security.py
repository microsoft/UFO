# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Tests for SSRF-safe URL validation."""

import ipaddress
import socket

import pytest
import requests
import urllib3.util.connection

from ufo.utils import url_security


@pytest.mark.parametrize(
    "url",
    [
        "http://[64:ff9b::a9fe:a9fe]/latest/meta-data/",
        "http://[64:ff9b:1::a9fe:a9fe]/latest/meta-data/",
        "http://[2002:7f00:1::]/",
        "http://[2001:0000:4136:e378:8000:63bf:f5ff:fffe]/",
    ],
)
def test_validate_url_blocks_transition_addresses_with_private_ipv4(url):
    with pytest.raises(ValueError, match="private/internal"):
        url_security.validate_url(url)


@pytest.mark.parametrize(
    "url",
    [
        "http://[64:ff9b::808:808]/",
        "http://[64:ff9b:1::808:808]/",
        "http://[2002:0808:0808::]/",
        "http://[2001:0000:4136:e378:8000:63bf:f7f7:f7f7]/",
    ],
)
def test_validate_url_blocks_transition_addresses_with_public_ipv4(url):
    with pytest.raises(ValueError, match="private/internal"):
        url_security.validate_url(url)


@pytest.mark.parametrize(
    "url",
    [
        "http://8.8.8.8/",
        "http://[2606:4700:4700::1111]/",
    ],
)
def test_validate_url_allows_public_literal_addresses(url):
    url_security.validate_url(url)


def test_safe_get_connects_to_vetted_ip_instead_of_resolving_hostname(monkeypatch):
    resolved_address = "8.8.8.8"
    connection_destinations = []

    def resolve_public_address(hostname, port):
        assert hostname == "rebinding.test"
        return [
            (
                socket.AF_INET,
                socket.SOCK_STREAM,
                socket.IPPROTO_TCP,
                "",
                (resolved_address, 0),
            )
        ]

    def stop_before_network_io(address, *args, **kwargs):
        connection_destinations.append(address)
        raise OSError("connection stopped by test")

    monkeypatch.setattr(socket, "getaddrinfo", resolve_public_address)
    monkeypatch.setattr(
        urllib3.util.connection, "create_connection", stop_before_network_io
    )

    monkeypatch.setenv("NO_PROXY", "*")

    with pytest.raises(requests.ConnectionError, match="connection stopped by test"):
        url_security.safe_get("http://rebinding.test:8080/path", timeout=0.1)

    assert connection_destinations == [(resolved_address, 8080)]


def test_safe_get_rejects_selected_proxy(monkeypatch):
    def return_without_network(self, request, **kwargs):
        response = requests.Response()
        response.status_code = 200
        response.url = request.url
        response.request = request
        response._content = b"ok"
        return response

    monkeypatch.setattr(url_security._PinnedHTTPAdapter, "send", return_without_network)

    session = requests.Session()
    session.trust_env = False
    session.proxies = {"http": "http://proxy.test:3128"}

    with pytest.raises(ValueError, match="proxy"):
        url_security.safe_get("http://8.8.8.8/", session=session)


def test_safe_get_closes_internal_session(monkeypatch):
    created_sessions = []
    session_class = requests.Session

    class TrackingSession(session_class):
        closed = False

        def __init__(self):
            super().__init__()
            self.trust_env = False
            created_sessions.append(self)

        def close(self):
            self.closed = True
            super().close()

    def return_response(self, request, **kwargs):
        response = requests.Response()
        response.status_code = 200
        response.url = request.url
        response.request = request
        response._content = b"ok"
        return response

    monkeypatch.setattr(requests, "Session", TrackingSession)
    monkeypatch.setattr(url_security._PinnedHTTPAdapter, "send", return_response)

    url_security.safe_get("http://8.8.8.8/")

    assert created_sessions[0].closed


def test_safe_get_closes_redirect_response(monkeypatch):
    responses = []

    class TrackingResponse(requests.Response):
        closed = False

        def close(self):
            self.closed = True
            super().close()

    def return_redirect_then_success(self, request, **kwargs):
        response = TrackingResponse()
        response.status_code = 302 if not responses else 200
        response.url = request.url
        response.request = request
        response._content = b""
        if not responses:
            response.headers["Location"] = "http://8.8.4.4/final"
        responses.append(response)
        return response

    monkeypatch.setattr(
        url_security._PinnedHTTPAdapter, "send", return_redirect_then_success
    )
    session = requests.Session()
    session.trust_env = False

    url_security.safe_get("http://8.8.8.8/start", session=session)

    assert responses[0].closed


def test_safe_get_resolves_and_pins_each_redirect_hop(monkeypatch):
    resolved_addresses = {
        "first.test": "8.8.8.8",
        "second.test": "8.8.4.4",
    }
    pinned_addresses = []

    def resolve_address(hostname, port):
        return [
            (
                socket.AF_INET,
                socket.SOCK_STREAM,
                socket.IPPROTO_TCP,
                "",
                (resolved_addresses[hostname], 0),
            )
        ]

    def return_redirect_then_success(self, request, **kwargs):
        pinned_addresses.append(self._address)
        response = requests.Response()
        response.status_code = 302 if len(pinned_addresses) == 1 else 200
        response.url = request.url
        response.request = request
        response._content = b""
        if response.status_code == 302:
            response.headers["Location"] = "http://second.test/final"
        return response

    monkeypatch.setattr(socket, "getaddrinfo", resolve_address)
    monkeypatch.setattr(
        url_security._PinnedHTTPAdapter, "send", return_redirect_then_success
    )
    session = requests.Session()
    session.trust_env = False

    url_security.safe_get("http://first.test/start", session=session)

    assert pinned_addresses == ["8.8.8.8", "8.8.4.4"]


def test_safe_get_strips_authorization_on_cross_origin_redirect(monkeypatch):
    request_headers = []

    def return_redirect_then_success(self, request, **kwargs):
        request_headers.append(request.headers.copy())
        response = requests.Response()
        response.status_code = 302 if len(request_headers) == 1 else 200
        response.url = request.url
        response.request = request
        response._content = b""
        if response.status_code == 302:
            response.headers["Location"] = "http://8.8.4.4/final"
        return response

    monkeypatch.setattr(
        url_security._PinnedHTTPAdapter, "send", return_redirect_then_success
    )
    session = requests.Session()
    session.trust_env = False

    url_security.safe_get(
        "http://8.8.8.8/start",
        session=session,
        headers={"Authorization": "Bearer secret"},
    )

    assert request_headers[0]["Authorization"] == "Bearer secret"
    assert "Authorization" not in request_headers[1]


def test_pinned_https_adapter_preserves_tls_identity_and_client_settings():
    request = requests.Request("GET", "https://service.test:8443/path").prepare()
    adapter = url_security._PinnedHTTPAdapter("8.8.8.8", "service.test")

    pool = adapter.get_connection_with_tls_context(
        request,
        verify="C:/certs/ca.pem",
        cert=("C:/certs/client.pem", "C:/certs/client.key"),
    )

    assert pool.host == "8.8.8.8"
    assert pool.port == 8443
    assert pool.assert_hostname == "service.test"
    assert pool.conn_kw["server_hostname"] == "service.test"
    assert pool.ca_certs == "C:/certs/ca.pem"
    assert pool.cert_file == "C:/certs/client.pem"
    assert pool.key_file == "C:/certs/client.key"


def test_pinned_http_connection_rejects_unvetted_peer(monkeypatch):
    class Socket:
        def getpeername(self):
            return ("127.0.0.1", 8080)

        def close(self):
            pass

    def connect_to_unvetted_peer(self):
        self.sock = Socket()

    monkeypatch.setattr(
        urllib3.connection.HTTPConnection, "connect", connect_to_unvetted_peer
    )
    connection = url_security._PinnedHTTPConnection("8.8.8.8", 8080)

    with pytest.raises(requests.ConnectionError, match="unexpected peer"):
        connection.connect()


@pytest.mark.parametrize(
    ("address", "embedded"),
    [
        ("::ffff:10.0.0.1", "10.0.0.1"),
        ("64:ff9b::a9fe:a9fe", "169.254.169.254"),
        ("2002:7f00:1::", "127.0.0.1"),
        ("2001:0000:4136:e378:8000:63bf:f5ff:fffe", "10.0.0.1"),
    ],
)
def test_iter_embedded_ipv4_extracts_transition_destination(address, embedded):
    result = list(
        url_security._iter_embedded_ipv4(ipaddress.ip_address(address))
    )

    assert result == [ipaddress.ip_address(embedded)]
