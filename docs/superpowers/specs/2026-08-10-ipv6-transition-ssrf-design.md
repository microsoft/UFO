# IPv6 Transition Address SSRF Guard Design

## Goal

Prevent IPv6 transition addresses from bypassing outbound URL validation and
reaching private, loopback, link-local, or cloud metadata IPv4 destinations.

## Policy

The SSRF guard will categorically reject these transition address ranges:

- `64:ff9b::/96` (NAT64 well-known prefix, RFC 6052)
- `64:ff9b:1::/48` (NAT64 local-use prefix, RFC 8215)
- `2002::/16` (6to4, RFC 3056)
- `2001::/32` (Teredo, RFC 4380)

This policy applies even when a transition address embeds a public IPv4
address. Explicit networks make the behavior deterministic across Python
versions instead of relying on changing `ipaddress` classification tables.

## Implementation

Keep `_is_blocked_ip` as the single decision point. Add the four transition
networks to `_BLOCKED_IP_NETWORKS` and defensively extract embedded IPv4
destinations before applying the network deny list. Re-check IPv4-mapped IPv6,
the NAT64 well-known `/96`, 6to4, and the Teredo client address through the same
IPv4 safety policy.

The entire RFC 8215 `/48` is explicitly denied but is not decoded as one fixed
layout. Operators may select different RFC 6052 prefix lengths beneath that
allocation, so the IPv6 address alone does not identify one unambiguous local
NAT64 embedding layout.

## Validation

Add focused pytest regressions that:

- reject the reported NAT64 metadata, 6to4 localhost, and Teredo private-client
  URL literals through `validate_url`;
- reject each transition prefix even when it carries a public IPv4 address;
- verify unambiguous embedded IPv4 values directly at the extraction helper;
  and
- retain public IPv4 and native IPv6 controls to guard against overblocking
  outside the transition prefixes.

The focused tests must fail against the current implementation for the missing
explicit policy, pass after the implementation, and be followed by the broader
URL-security test module run.