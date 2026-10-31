"""Addresses a phone could use to reach this computer, for the line `office serve` prints when it is open to the network."""

from __future__ import annotations

import ipaddress
import socket

TAILSCALE = ipaddress.ip_network("100.64.0.0/10")


def classify(address: str) -> str:
    """"Tailscale", "區網" (a home or office network) or "" for anything a phone should not be told to use."""
    try:
        ip = ipaddress.ip_address(address)
    except ValueError:
        return ""
    if ip.version != 4 or ip.is_loopback or ip.is_link_local:
        return ""
    if ip in TAILSCALE:
        return "Tailscale"
    return "區網" if ip.is_private else ""


def _route_to(target: str) -> str:
    """The address this computer would use to reach `target` (a UDP "connect" sends nothing)."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as probe:
            probe.settimeout(0.5)
            probe.connect((target, 9))
            return probe.getsockname()[0]
    except OSError:
        return ""


def phone_addresses() -> list[tuple[str, str]]:
    """[(address, kind)] with Tailscale first: it works away from home as well."""
    found = [_route_to("100.100.100.100"), _route_to("8.8.8.8")]
    try:
        found += [info[4][0] for info in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET)]
    except OSError:
        pass
    seen, rows = set(), []
    for address in found:
        kind = classify(address)
        if kind and address not in seen:
            seen.add(address)
            rows.append((address, kind))
    return sorted(rows, key=lambda row: row[1] != "Tailscale")
