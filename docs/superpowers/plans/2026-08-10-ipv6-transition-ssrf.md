# IPv6 Transition Address SSRF Guard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reject NAT64, 6to4, and Teredo URLs deterministically and defensively re-check their unambiguous embedded IPv4 destinations.

**Architecture:** Keep `ufo.utils.url_security._is_blocked_ip` as the single outbound-address policy boundary. Add explicit transition networks for stable categorical denial, then decode embedded IPv4 destinations in a small iterator and feed them back through the existing policy.

**Tech Stack:** Python standard library `ipaddress`, pytest

## Global Constraints

- Block all NAT64, 6to4, and Teredo transition prefixes, including addresses that embed public IPv4.
- Decode only unambiguous layouts: IPv4-mapped IPv6, NAT64 well-known `/96`, 6to4, and the Teredo client address.
- Do not infer one embedding layout for the RFC 8215 local-use `/48`; deny the full range explicitly.
- Add no external dependencies and do not change the public URL-validation API.
- Do not create git commits unless the user explicitly requests them.

## File Structure

- Create `tests/test_url_security.py`: focused public-behavior and embedded-address regression coverage.
- Modify `ufo/utils/url_security.py`: transition network policy and embedded IPv4 decoding.

---

### Task 1: Explicit Transition Prefix Denial

**Files:**
- Create: `tests/test_url_security.py`
- Modify: `ufo/utils/url_security.py`

**Interfaces:**
- Consumes: `validate_url(url: str) -> None`
- Produces: explicit `ipaddress.IPv6Network` constants used by `_BLOCKED_IP_NETWORKS`

- [ ] **Step 1: Write failing URL validation regressions**

Create `tests/test_url_security.py` with literal addresses so the tests do not depend on DNS:

```python
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Tests for SSRF-safe URL validation."""

import pytest

from ufo.utils.url_security import validate_url


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
        validate_url(url)


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
        validate_url(url)


@pytest.mark.parametrize(
    "url",
    [
        "http://8.8.8.8/",
        "http://[2606:4700:4700::1111]/",
    ],
)
def test_validate_url_allows_public_literal_addresses(url):
    validate_url(url)
```

- [ ] **Step 2: Run the regressions and verify the 6to4 cases fail**

Run: `python -m pytest tests/test_url_security.py -v`

Expected: both tests containing `2002::/16` cases fail because the current guard accepts those URLs; the public literal control test passes.

- [ ] **Step 3: Add explicit transition network constants**

In `ufo/utils/url_security.py`, define named networks above `_BLOCKED_IP_NETWORKS` and append them to its IPv6 section:

```python
_NAT64_WELL_KNOWN_NETWORK = ipaddress.ip_network("64:ff9b::/96")
_NAT64_LOCAL_USE_NETWORK = ipaddress.ip_network("64:ff9b:1::/48")
_SIX_TO_FOUR_NETWORK = ipaddress.ip_network("2002::/16")
_TEREDO_NETWORK = ipaddress.ip_network("2001::/32")
```

```python
    _NAT64_WELL_KNOWN_NETWORK,  # NAT64 well-known prefix (RFC 6052)
    _NAT64_LOCAL_USE_NETWORK,  # NAT64 local-use prefix (RFC 8215)
    _SIX_TO_FOUR_NETWORK,  # 6to4 (RFC 3056)
    _TEREDO_NETWORK,  # Teredo (RFC 4380)
```

- [ ] **Step 4: Run the focused module and verify it passes**

Run: `python -m pytest tests/test_url_security.py -v`

Expected: all URL rejection and public control cases pass.

### Task 2: Embedded IPv4 Re-check

**Files:**
- Modify: `tests/test_url_security.py`
- Modify: `ufo/utils/url_security.py`

**Interfaces:**
- Consumes: named transition network constants from Task 1
- Produces: `_iter_embedded_ipv4(ip: ipaddress._BaseAddress) -> Iterable[ipaddress.IPv4Address]`

- [ ] **Step 1: Write failing extraction tests**

Replace the direct function import in `tests/test_url_security.py` with module imports:

```python
import ipaddress

import pytest

from ufo.utils import url_security
```

Change existing calls to `url_security.validate_url(url)`, then add:

```python
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
```

- [ ] **Step 2: Run the extraction test and verify it fails**

Run: `python -m pytest tests/test_url_security.py::test_iter_embedded_ipv4_extracts_transition_destination -v`

Expected: FAIL with `AttributeError` because `_iter_embedded_ipv4` does not exist.

- [ ] **Step 3: Implement unambiguous transition decoding**

Add this helper above `_is_blocked_ip` in `ufo/utils/url_security.py`:

```python
def _iter_embedded_ipv4(
    ip: ipaddress._BaseAddress,
) -> Iterable[ipaddress.IPv4Address]:
    """Yield unambiguous IPv4 destinations embedded in an IPv6 address."""
    if not isinstance(ip, ipaddress.IPv6Address):
        return

    if ip.ipv4_mapped is not None:
        yield ip.ipv4_mapped

    if ip in _NAT64_WELL_KNOWN_NETWORK:
        yield ipaddress.IPv4Address(int(ip) & 0xFFFFFFFF)

    if ip.sixtofour is not None:
        yield ip.sixtofour

    if ip.teredo is not None:
        _, client = ip.teredo
        yield client
```

At the start of `_is_blocked_ip`, before generic `ipaddress` flags, re-check each extracted destination:

```python
    for embedded_ip in _iter_embedded_ipv4(ip):
        if _is_blocked_ip(embedded_ip):
            return True
```

- [ ] **Step 4: Run the focused extraction test**

Run: `python -m pytest tests/test_url_security.py::test_iter_embedded_ipv4_extracts_transition_destination -v`

Expected: all four extraction cases pass.

- [ ] **Step 5: Run all URL-security regressions**

Run: `python -m pytest tests/test_url_security.py -v`

Expected: all transition rejection, extraction, and public control tests pass without warnings.

- [ ] **Step 6: Run static diagnostics on touched Python files**

Check `ufo/utils/url_security.py` and `tests/test_url_security.py` with the editor diagnostics provider.

Expected: no new errors in either file.