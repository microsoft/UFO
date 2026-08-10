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
