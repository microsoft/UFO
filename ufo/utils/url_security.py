# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
URL validation helpers used to mitigate Server-Side Request Forgery (SSRF)
attacks when the application performs outbound HTTP requests to URLs that
may be influenced by untrusted input (e.g. LLM-chosen URLs, user queries,
or URLs returned by third-party search APIs).

The helpers in this module enforce:
- Allow-listed URL schemes (only ``http`` and ``https``)
- Hostname presence
- Blocking of private, loopback, link-local, multicast, reserved and
  cloud-metadata IP ranges (both IPv4 and IPv6)

Callers should validate URLs *before* issuing a request, and should also
pass ``allow_redirects=False`` (or otherwise revalidate redirect targets)
so that an attacker cannot bypass the check by serving a 30x redirect to
an internal address.
"""

from __future__ import annotations

import ipaddress
import socket
from typing import Any, Iterable, Optional
from urllib.parse import urljoin, urlparse

import requests


# Private/reserved IP networks that should be blocked for SSRF protection.
_BLOCKED_IP_NETWORKS = (
    # IPv4
    ipaddress.ip_network("0.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("100.64.0.0/10"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),  # Link-local / cloud metadata
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.0.0.0/24"),
    ipaddress.ip_network("192.0.2.0/24"),
    ipaddress.ip_network("192.88.99.0/24"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("198.18.0.0/15"),
    ipaddress.ip_network("198.51.100.0/24"),
    ipaddress.ip_network("203.0.113.0/24"),
    ipaddress.ip_network("224.0.0.0/4"),
    ipaddress.ip_network("240.0.0.0/4"),
    ipaddress.ip_network("255.255.255.255/32"),
    # IPv6
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
    ipaddress.ip_network("fe80::/10"),
    ipaddress.ip_network("ff00::/8"),  # multicast
    ipaddress.ip_network("::ffff:0:0/96"),  # IPv4-mapped IPv6
)

# Only allow http and https schemes.
_ALLOWED_SCHEMES = frozenset({"http", "https"})


def _iter_resolved_ips(hostname: str) -> Iterable[ipaddress._BaseAddress]:
    """
    Resolve ``hostname`` and yield every associated IP address.

    :param hostname: The hostname to resolve.
    :raises ValueError: If the hostname cannot be resolved.
    """
    try:
        addr_infos = socket.getaddrinfo(hostname, None)
    except socket.gaierror as exc:
        raise ValueError(f"Cannot resolve hostname: {hostname}") from exc

    for addr_info in addr_infos:
        yield ipaddress.ip_address(addr_info[4][0])


def _is_blocked_ip(ip: ipaddress._BaseAddress) -> bool:
    """
    Return ``True`` if ``ip`` falls in any of the blocked networks or is
    otherwise considered unsafe for outbound requests.
    """
    if (
        ip.is_private
        or ip.is_loopback
        or ip.is_link_local
        or ip.is_multicast
        or ip.is_reserved
        or ip.is_unspecified
    ):
        return True
    for network in _BLOCKED_IP_NETWORKS:
        if ip in network:
            return True
    return False


def validate_url(url: str) -> None:
    """
    Validate a URL to prevent SSRF attacks.

    Blocks requests to:

    - Non-HTTP(S) schemes (e.g., ``file://``, ``ftp://``, ``gopher://``)
    - Private, loopback, link-local, multicast and reserved IP addresses
    - Cloud metadata endpoints (e.g., ``169.254.169.254``)

    The URL's hostname is resolved and *every* returned address is checked,
    so DNS names that resolve to internal addresses are also blocked.

    :param url: The URL to validate.
    :raises ValueError: If the URL is empty, malformed, uses a disallowed
        scheme, has no hostname, cannot be resolved, or resolves to a
        blocked address.
    """
    if not url or not isinstance(url, str):
        raise ValueError("URL must be a non-empty string")

    parsed = urlparse(url)

    scheme = (parsed.scheme or "").lower()
    if scheme not in _ALLOWED_SCHEMES:
        raise ValueError(
            f"URL scheme '{parsed.scheme}' is not allowed. "
            f"Only {sorted(_ALLOWED_SCHEMES)} are permitted."
        )

    hostname = parsed.hostname
    if not hostname:
        raise ValueError("URL must contain a valid hostname")

    # If the hostname is itself a literal IP address, validate it directly
    # so we don't rely on DNS resolution.
    try:
        literal_ip = ipaddress.ip_address(hostname)
    except ValueError:
        literal_ip = None

    if literal_ip is not None:
        if _is_blocked_ip(literal_ip):
            raise ValueError(
                f"Access to private/internal address {literal_ip} is blocked"
            )
        return

    for ip in _iter_resolved_ips(hostname):
        if _is_blocked_ip(ip):
            raise ValueError(
                f"Access to private/internal address {ip} "
                f"(resolved from {hostname}) is blocked"
            )


def is_url_safe(url: str) -> bool:
    """
    Convenience wrapper around :func:`validate_url` that returns a boolean
    instead of raising.

    :param url: The URL to validate.
    :return: ``True`` if the URL passes SSRF validation, ``False`` otherwise.
    """
    try:
        validate_url(url)
    except ValueError:
        return False
    return True


# Maximum number of redirects to follow when using :func:`safe_get`.
_MAX_REDIRECTS = 5


def safe_get(
    url: str,
    *,
    headers: Optional[dict] = None,
    timeout: Optional[float] = 30.0,
    max_redirects: int = _MAX_REDIRECTS,
    session: Optional[requests.Session] = None,
    **kwargs: Any,
) -> requests.Response:
    """
    Perform an HTTP GET that is hardened against SSRF.

    The initial URL and every redirect target are revalidated with
    :func:`validate_url` before the request is issued, which prevents an
    attacker from bypassing the check by serving a 30x redirect to an
    internal address.

    :param url: The URL to fetch.
    :param headers: Optional HTTP headers to send with the request.
    :param timeout: Per-request timeout in seconds.
    :param max_redirects: Maximum number of redirects to follow.
    :param session: Optional :class:`requests.Session` to use.
    :param kwargs: Additional keyword arguments forwarded to ``requests.get``.
        ``allow_redirects`` is always forced to ``False`` to keep redirect
        handling under the control of this function.
    :return: The final :class:`requests.Response`.
    :raises ValueError: If ``url`` (or any redirect target) fails validation,
        or if ``max_redirects`` is exceeded.
    """
    kwargs.pop("allow_redirects", None)
    requester = session if session is not None else requests

    current_url = url
    for _ in range(max_redirects + 1):
        validate_url(current_url)
        response = requester.get(
            current_url,
            headers=headers,
            timeout=timeout,
            allow_redirects=False,
            **kwargs,
        )
        if response.is_redirect or response.is_permanent_redirect:
            location = response.headers.get("Location")
            if not location:
                return response
            current_url = urljoin(current_url, location)
            continue
        return response

    raise ValueError(f"Exceeded maximum redirects ({max_redirects}) for URL: {url}")
