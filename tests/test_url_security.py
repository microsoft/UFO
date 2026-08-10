# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Tests for SSRF-safe URL validation."""

import ipaddress

import pytest

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
