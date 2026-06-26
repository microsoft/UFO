# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Unit tests for SSRF protection on device ``server_url`` validation.

Verifies that the Galaxy Web UI rejects URLs that could be used for
server-side request forgery (cloud metadata, loopback, non-WebSocket
schemes) while still accepting legitimate device endpoints.
"""

import sys
import unittest
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from galaxy.webui.security import (
    ServerUrlValidationError,
    UrlValidationPolicy,
    validate_server_url,
)


class TestServerUrlValidation(unittest.TestCase):
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
        self.assertEqual(validate_server_url(url, policy), url)
        with self.assertRaises(ServerUrlValidationError):
            validate_server_url("ws://8.8.8.8:8080/", policy)

    def test_ipv4_mapped_ipv6_metadata_blocked(self):
        """IPv4-mapped IPv6 metadata addresses are normalized and blocked."""
        with self.assertRaises(ServerUrlValidationError):
            validate_server_url("ws://[::ffff:169.254.169.254]:80/")

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


if __name__ == "__main__":
    unittest.main()
