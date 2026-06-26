# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Server URL validation for SSRF protection.

The Galaxy Web UI accepts a ``server_url`` from API clients when registering a
device. That URL is later used to open an outbound WebSocket connection from the
Galaxy server. Without validation, an authenticated API caller could point the
server at internal services or cloud metadata endpoints (SSRF). For example::

    ws://169.254.169.254/    # cloud instance metadata (IMDS)
    ws://127.0.0.1:9999/     # loopback / local services
    http://internal-host/    # non-WebSocket scheme

This module validates a ``server_url`` before it is accepted, enforcing:

* an approved scheme allowlist (``ws`` / ``wss`` only),
* a block on link-local / cloud-metadata addresses (always enforced),
* a block on loopback addresses (enabled by default; opt-out for local dev),
* an optional block on private (RFC 1918 / ULA) addresses, and
* an optional explicit host allowlist for the strictest deployments.

Because a hostname can resolve to a blocked address (including via DNS
rebinding), the hostname is resolved and *every* resulting IP address is
checked.

Behaviour is configurable through environment variables so that operators can
tighten or relax the policy without code changes:

* ``GALAXY_DEVICE_URL_ALLOW_LOOPBACK`` - set truthy to permit loopback hosts.
* ``GALAXY_DEVICE_URL_BLOCK_PRIVATE`` - set truthy to reject private/ULA hosts.
* ``GALAXY_DEVICE_URL_ALLOWLIST`` - comma-separated ``host`` or ``host:port``
  entries. When set, only matching hosts are accepted (strict mode).
"""

import ipaddress
import logging
import os
import socket
from dataclasses import dataclass, field
from typing import List, Set
from urllib.parse import urlsplit

logger = logging.getLogger(__name__)

# Schemes that are valid for an outbound device WebSocket connection.
_ALLOWED_SCHEMES: Set[str] = {"ws", "wss"}

# Hostnames that always resolve to the local machine but may not parse as IPs.
_LOOPBACK_HOSTNAMES: Set[str] = {"localhost"}


class ServerUrlValidationError(ValueError):
    """Raised when a ``server_url`` fails SSRF validation."""


def _env_flag(name: str, default: bool = False) -> bool:
    """
    Read a boolean flag from the environment.

    :param name: Environment variable name.
    :param default: Value to use when the variable is unset.
    :return: Parsed boolean value.
    """
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _parse_allowlist(raw: str) -> Set[str]:
    """
    Parse a comma-separated host allowlist into a normalized set.

    Each entry may be ``host`` or ``host:port``; the port is ignored for
    matching and entries are lower-cased.

    :param raw: Raw allowlist string from the environment.
    :return: Set of normalized hostnames.
    """
    hosts: Set[str] = set()
    for entry in raw.split(","):
        entry = entry.strip().lower()
        if not entry:
            continue
        # Strip an optional port component.
        host = entry.rsplit(":", 1)[0] if ":" in entry else entry
        hosts.add(host)
    return hosts


@dataclass(frozen=True)
class UrlValidationPolicy:
    """
    Configuration controlling how ``server_url`` values are validated.

    :param allowed_schemes: URL schemes that are permitted.
    :param block_loopback: Reject hosts that resolve to loopback addresses.
    :param block_private: Reject hosts that resolve to private / ULA addresses.
    :param allowlist: When non-empty, only these hostnames are accepted.
    """

    allowed_schemes: Set[str] = field(default_factory=lambda: set(_ALLOWED_SCHEMES))
    block_loopback: bool = True
    block_private: bool = False
    allowlist: Set[str] = field(default_factory=set)

    @classmethod
    def from_env(cls) -> "UrlValidationPolicy":
        """
        Build a policy from environment variables.

        :return: Policy reflecting the current environment configuration.
        """
        return cls(
            allowed_schemes=set(_ALLOWED_SCHEMES),
            block_loopback=not _env_flag("GALAXY_DEVICE_URL_ALLOW_LOOPBACK", False),
            block_private=_env_flag("GALAXY_DEVICE_URL_BLOCK_PRIVATE", False),
            allowlist=_parse_allowlist(
                os.environ.get("GALAXY_DEVICE_URL_ALLOWLIST", "")
            ),
        )


def _resolve_addresses(hostname: str) -> List[ipaddress._BaseAddress]:
    """
    Resolve a hostname to all of its IP addresses.

    If the hostname is already a literal IP address it is returned directly.

    :param hostname: Hostname or IP literal to resolve.
    :return: List of resolved IP address objects.
    :raises ServerUrlValidationError: If the hostname cannot be resolved.
    """
    try:
        return [ipaddress.ip_address(hostname)]
    except ValueError:
        pass

    try:
        infos = socket.getaddrinfo(hostname, None)
    except socket.gaierror as exc:
        raise ServerUrlValidationError(
            f"Could not resolve host '{hostname}'"
        ) from exc

    addresses: List[ipaddress._BaseAddress] = []
    for info in infos:
        sockaddr = info[4]
        ip_str = sockaddr[0]
        try:
            addresses.append(ipaddress.ip_address(ip_str))
        except ValueError:
            continue

    if not addresses:
        raise ServerUrlValidationError(
            f"Could not resolve host '{hostname}' to a usable address"
        )
    return addresses


def _check_address(
    address: ipaddress._BaseAddress, policy: UrlValidationPolicy
) -> None:
    """
    Validate a single resolved IP address against the policy.

    :param address: Resolved IP address to inspect.
    :param policy: Active validation policy.
    :raises ServerUrlValidationError: If the address is disallowed.
    """
    # Normalize IPv4-mapped IPv6 addresses (e.g. ::ffff:169.254.169.254).
    mapped = getattr(address, "ipv4_mapped", None)
    if mapped is not None:
        address = mapped

    # Link-local addresses include cloud metadata endpoints (169.254.169.254,
    # fd00:ec2::254, fe80::/10). These are never a valid device endpoint and are
    # always blocked, regardless of configuration.
    if address.is_link_local:
        raise ServerUrlValidationError(
            "server_url resolves to a link-local / metadata address, "
            "which is not allowed"
        )

    if address.is_multicast or address.is_unspecified or address.is_reserved:
        raise ServerUrlValidationError(
            "server_url resolves to a reserved or non-routable address, "
            "which is not allowed"
        )

    if policy.block_loopback and address.is_loopback:
        raise ServerUrlValidationError(
            "server_url resolves to a loopback address, which is not allowed"
        )

    if policy.block_private and address.is_private and not address.is_loopback:
        raise ServerUrlValidationError(
            "server_url resolves to a private address, which is not allowed"
        )


def validate_server_url(url: str, policy: UrlValidationPolicy = None) -> str:
    """
    Validate a device ``server_url`` to mitigate SSRF.

    :param url: The candidate server URL supplied by an API client.
    :param policy: Validation policy to apply; loaded from the environment when
        omitted.
    :return: The original URL when validation succeeds.
    :raises ServerUrlValidationError: If the URL is malformed or disallowed.
    """
    if policy is None:
        policy = UrlValidationPolicy.from_env()

    if not isinstance(url, str) or not url.strip():
        raise ServerUrlValidationError("server_url must be a non-empty string")

    parsed = urlsplit(url.strip())

    scheme = parsed.scheme.lower()
    if scheme not in policy.allowed_schemes:
        allowed = ", ".join(sorted(policy.allowed_schemes))
        raise ServerUrlValidationError(
            f"server_url scheme '{parsed.scheme}' is not allowed; "
            f"use one of: {allowed}"
        )

    hostname = parsed.hostname
    if not hostname:
        raise ServerUrlValidationError("server_url must include a host")

    hostname_lower = hostname.lower()

    # Strict allowlist mode: only explicitly permitted hosts are accepted.
    if policy.allowlist:
        if hostname_lower not in policy.allowlist:
            raise ServerUrlValidationError(
                f"server_url host '{hostname}' is not in the configured allowlist"
            )
        return url

    # Treat textual loopback aliases as loopback even before DNS resolution.
    if policy.block_loopback and hostname_lower in _LOOPBACK_HOSTNAMES:
        raise ServerUrlValidationError(
            "server_url resolves to a loopback address, which is not allowed"
        )

    for address in _resolve_addresses(hostname):
        _check_address(address, policy)

    return url
