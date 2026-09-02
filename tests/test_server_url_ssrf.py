# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Unit tests for SSRF protection on device ``server_url`` validation.

Verifies that the Galaxy Web UI rejects URLs that could be used for
server-side request forgery (cloud metadata, loopback, non-WebSocket
schemes) while still accepting legitimate device endpoints.
"""

import sys
import socket
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from galaxy.webui.security import (
    ServerUrlValidationError,
    UrlValidationPolicy,
    validate_server_url,
)
from galaxy.webui.security import url_validator


class TestServerUrlValidation(unittest.IsolatedAsyncioTestCase):
    """Test cases for SSRF-protective server_url validation."""

    def test_blocks_cloud_metadata_endpoint(self):
        """Link-local / IMDS endpoints must always be rejected."""
        with self.assertRaises(ServerUrlValidationError):
            validate_server_url("ws://169.254.169.254:80/")

    def test_blocks_loopback_ip(self):
        """Loopback IPs are rejected by default."""
        with self.assertRaises(ServerUrlValidationError):
            validate_server_url("ws://127.0.0.1:9999/")

    def test_blocks_loopback_hostname(self):
        """The 'localhost' alias is treated as loopback."""
        with self.assertRaises(ServerUrlValidationError):
            validate_server_url("ws://localhost:5005/ws")

    def test_blocks_non_websocket_scheme(self):
        """Only ws/wss schemes are permitted."""
        for url in ("http://example.com/", "https://example.com/", "gopher://x/"):
            with self.assertRaises(ServerUrlValidationError):
                validate_server_url(url)

    def test_blocks_missing_host(self):
        """A URL without a host is rejected."""
        with self.assertRaises(ServerUrlValidationError):
            validate_server_url("ws:///path")

    def test_blocks_empty_value(self):
        """Empty or non-string values are rejected."""
        with self.assertRaises(ServerUrlValidationError):
            validate_server_url("")

    def test_allows_public_ip(self):
        """A routable public IP endpoint is accepted."""
        url = "ws://8.8.8.8:8080/ws"
        self.assertEqual(validate_server_url(url), url)

    def test_validated_url_carries_deduplicated_resolved_addresses(self):
        """The connection receives the same addresses approved by validation."""
        public_results = [
            (
                socket.AF_INET,
                socket.SOCK_STREAM,
                socket.IPPROTO_TCP,
                "",
                ("8.8.8.8", 0),
            ),
            (
                socket.AF_INET,
                socket.SOCK_STREAM,
                socket.IPPROTO_TCP,
                "",
                ("8.8.8.8", 0),
            ),
        ]

        with patch("socket.getaddrinfo", return_value=public_results):
            result = url_validator.validate_and_resolve_server_url(
                "ws://device.test:8080/ws"
            )

        self.assertEqual(result.url, "ws://device.test:8080/ws")
        self.assertEqual(result.addresses, ("8.8.8.8",))

    def test_allows_private_ip_by_default(self):
        """Private networks are valid device endpoints by default."""
        url = "ws://192.168.1.100:8080"
        self.assertEqual(validate_server_url(url), url)

    def test_block_private_policy(self):
        """Private addresses are rejected when block_private is enabled."""
        policy = UrlValidationPolicy(block_private=True)
        with self.assertRaises(ServerUrlValidationError):
            validate_server_url("ws://192.168.1.100:8080", policy)

    def test_allow_loopback_policy(self):
        """Loopback can be explicitly permitted for local development."""
        policy = UrlValidationPolicy(block_loopback=False)
        url = "ws://127.0.0.1:9999/"
        self.assertEqual(validate_server_url(url, policy), url)

    def test_allowlist_strict_mode(self):
        """When an allowlist is set, only listed hosts are accepted."""
        policy = UrlValidationPolicy(allowlist={"prod-device.company.com"})
        url = "wss://prod-device.company.com"
        public_result = [
            (
                socket.AF_INET,
                socket.SOCK_STREAM,
                socket.IPPROTO_TCP,
                "",
                ("8.8.8.8", 0),
            )
        ]
        with patch("socket.getaddrinfo", return_value=public_result):
            self.assertEqual(validate_server_url(url, policy), url)
        with self.assertRaises(ServerUrlValidationError):
            validate_server_url("ws://8.8.8.8:8080/", policy)

    def test_allowlisted_host_still_enforces_address_policy(self):
        """Allowlisting a name must not bypass checks on its resolved address."""
        policy = UrlValidationPolicy(allowlist={"prod-device.company.com"})
        loopback_result = [
            (
                socket.AF_INET,
                socket.SOCK_STREAM,
                socket.IPPROTO_TCP,
                "",
                ("127.0.0.1", 0),
            )
        ]

        with patch("socket.getaddrinfo", return_value=loopback_result):
            with self.assertRaises(ServerUrlValidationError):
                validate_server_url("wss://prod-device.company.com", policy)

    def test_ipv4_mapped_ipv6_metadata_blocked(self):
        """IPv4-mapped IPv6 metadata addresses are normalized and blocked."""
        with self.assertRaises(ServerUrlValidationError):
            validate_server_url("ws://[::ffff:169.254.169.254]:80/")

    def test_ipv6_transition_address_with_loopback_destination_is_blocked(self):
        """Transition addresses cannot hide loopback from the address policy."""
        with self.assertRaises(ServerUrlValidationError):
            validate_server_url("ws://[2002:7f00:1::]:80/")

    def test_device_add_request_rejects_ssrf(self):
        """The DeviceAddRequest model rejects SSRF payloads at the boundary."""
        from pydantic import ValidationError

        from galaxy.webui.models.requests import DeviceAddRequest

        with self.assertRaises(ValidationError):
            DeviceAddRequest(
                device_id="ssrf",
                server_url="ws://169.254.169.254:80/",
                os="Windows",
                capabilities=["test"],
            )

    def test_device_add_request_accepts_valid(self):
        """The DeviceAddRequest model accepts a legitimate endpoint."""
        from galaxy.webui.models.requests import DeviceAddRequest

        req = DeviceAddRequest(
            device_id="ok",
            server_url="ws://8.8.8.8:8080/ws",
            os="Windows",
            capabilities=["test"],
        )
        self.assertEqual(req.server_url, "ws://8.8.8.8:8080/ws")

    async def test_webui_registration_retains_validated_addresses(self):
        """Delayed and repeated connects use the address approved by the service."""
        from galaxy.webui.services.device_service import DeviceService

        device_registry = Mock()
        device_manager = SimpleNamespace(device_registry=device_registry)
        app_state = SimpleNamespace(
            galaxy_client=SimpleNamespace(
                _client=SimpleNamespace(device_manager=device_manager)
            )
        )
        service = DeviceService(app_state)
        public_result = [
            (
                socket.AF_INET,
                socket.SOCK_STREAM,
                socket.IPPROTO_TCP,
                "",
                ("8.8.8.8", 0),
            )
        ]

        with patch("socket.getaddrinfo", return_value=public_result):
            registered = await service.register_and_connect_device(
                device_id="device-1",
                server_url="wss://device.test:8443/ws",
                os="Windows",
                capabilities=["test"],
                metadata=None,
                max_retries=3,
                auto_connect=False,
            )

        self.assertTrue(registered)
        self.assertEqual(
            device_registry.register_device.call_args.kwargs["pinned_addresses"],
            ("8.8.8.8",),
        )

    async def test_device_route_does_not_persist_final_validation_failure(self):
        """A URL rejected after DNS drift must never reach persistent config."""
        from fastapi import HTTPException

        from galaxy.webui.models.requests import DeviceAddRequest
        from galaxy.webui.routers import devices

        class ConfigService:
            add_called = False

            def load_devices_config(self):
                return {"devices": []}

            def device_id_exists(self, device_id):
                return False

            def add_device_to_config(self, **kwargs):
                self.add_called = True
                return kwargs

        public_result = [
            (
                socket.AF_INET,
                socket.SOCK_STREAM,
                socket.IPPROTO_TCP,
                "",
                ("8.8.8.8", 0),
            )
        ]
        loopback_result = [
            (
                socket.AF_INET,
                socket.SOCK_STREAM,
                socket.IPPROTO_TCP,
                "",
                ("127.0.0.1", 0),
            )
        ]
        device_registry = Mock()
        app_state = SimpleNamespace(
            galaxy_client=SimpleNamespace(
                _client=SimpleNamespace(
                    device_manager=SimpleNamespace(device_registry=device_registry)
                )
            )
        )

        with patch("socket.getaddrinfo", return_value=public_result):
            request = DeviceAddRequest(
                device_id="device-1",
                server_url="wss://device.test:8443/ws",
                os="Windows",
                capabilities=["test"],
                auto_connect=False,
            )

        config_service = ConfigService()
        with (
            patch.object(devices, "ConfigService", return_value=config_service),
            patch.object(devices, "get_app_state", return_value=app_state),
            patch("socket.getaddrinfo", return_value=loopback_result),
        ):
            with self.assertRaises(HTTPException):
                await devices.add_device(request)

        self.assertFalse(config_service.add_called)

    async def test_device_route_persists_final_validated_addresses(self):
        """A successful Web UI registration persists its pinned destination."""
        from galaxy.webui.models.requests import DeviceAddRequest
        from galaxy.webui.routers import devices

        class ConfigService:
            added_device = None

            def load_devices_config(self):
                return {"devices": []}

            def device_id_exists(self, device_id):
                return False

            def add_device_to_config(self, **kwargs):
                self.added_device = kwargs
                return kwargs

        public_result = [
            (
                socket.AF_INET,
                socket.SOCK_STREAM,
                socket.IPPROTO_TCP,
                "",
                ("8.8.8.8", 0),
            )
        ]
        app_state = SimpleNamespace(
            galaxy_client=SimpleNamespace(
                _client=SimpleNamespace(
                    device_manager=SimpleNamespace(device_registry=Mock())
                )
            )
        )

        with patch("socket.getaddrinfo", return_value=public_result):
            request = DeviceAddRequest(
                device_id="device-1",
                server_url="wss://device.test:8443/ws",
                os="Windows",
                capabilities=["test"],
                auto_connect=False,
            )

            config_service = ConfigService()
            with (
                patch.object(devices, "ConfigService", return_value=config_service),
                patch.object(devices, "get_app_state", return_value=app_state),
            ):
                await devices.add_device(request)

        self.assertEqual(
            config_service.added_device["pinned_addresses"], ("8.8.8.8",)
        )

    async def test_device_route_does_not_persist_without_device_manager(self):
        """An unavailable manager returns 503 and leaves config unchanged."""
        from fastapi import HTTPException

        from galaxy.webui.models.requests import DeviceAddRequest
        from galaxy.webui.routers import devices

        config_service = Mock()
        config_service.load_devices_config.return_value = {"devices": []}
        config_service.device_id_exists.return_value = False
        request = DeviceAddRequest(
            device_id="device-1",
            server_url="wss://8.8.8.8:8443/ws",
            os="Windows",
            capabilities=["test"],
            auto_connect=False,
        )

        with (
            patch.object(devices, "ConfigService", return_value=config_service),
            patch.object(
                devices,
                "get_app_state",
                return_value=SimpleNamespace(galaxy_client=None),
            ),
        ):
            with self.assertRaises(HTTPException) as raised:
                await devices.add_device(request)

        self.assertEqual(raised.exception.status_code, 503)
        config_service.add_device_to_config.assert_not_called()

    def test_persisted_pinned_addresses_survive_config_reload(self):
        """Restarted Galaxy clients retain Web UI destination pinning."""
        from galaxy.client.config_loader import ConstellationConfig

        config_text = """\
devices:
  - device_id: device-1
    server_url: wss://device.test:8443/ws
    pinned_addresses:
      - 8.8.8.8
"""
        with tempfile.TemporaryDirectory() as directory:
            config_path = Path(directory) / "devices.yaml"
            config_path.write_text(config_text, encoding="utf-8")
            config = ConstellationConfig.from_yaml(str(config_path))

        self.assertEqual(config.devices[0].pinned_addresses, ("8.8.8.8",))

    async def test_config_registration_forwards_pinned_addresses(self):
        """Config-based startup carries persisted pins into the device profile."""
        from galaxy.client.config_loader import DeviceConfig
        from galaxy.client.constellation_client import ConstellationClient

        client = object.__new__(ConstellationClient)
        client.device_manager = SimpleNamespace(
            register_device=AsyncMock(return_value=True)
        )
        device_config = DeviceConfig(
            device_id="device-1",
            server_url="wss://device.test:8443/ws",
            pinned_addresses=("8.8.8.8",),
        )

        await client.register_device_from_config(device_config)

        self.assertEqual(
            client.device_manager.register_device.call_args.kwargs[
                "pinned_addresses"
            ],
            ("8.8.8.8",),
        )


if __name__ == "__main__":
    unittest.main()
