"""Decide whether a URL may be fetched: only public http(s) targets by default.

Search results are untrusted input, and an agent may drive DeepCloak over MCP, so a
result must not reach this machine or its private network. Pure apart from DNS,
which is injectable for tests.
"""

from __future__ import annotations

import ipaddress
import socket
from collections.abc import Callable
from urllib.parse import urlsplit

__all__ = ["BlockedTarget", "blocked_reason"]

Resolver = Callable[[str], list[str]]


class BlockedTarget(Exception):
    """A fetch (or one of its redirects) pointed at a target that is not allowed."""


def _resolve(host: str) -> list[str]:
    return [info[4][0] for info in socket.getaddrinfo(host, None)]


def _is_public(address: str) -> bool:
    ip = ipaddress.ip_address(address.split("%", 1)[0])
    mapped = getattr(ip, "ipv4_mapped", None)
    return (mapped or ip).is_global


def blocked_reason(url: str, resolve: Resolver = _resolve) -> str | None:
    """Why ``url`` must not be fetched, or None if it may be."""
    parts = urlsplit(url)
    if parts.scheme not in ("http", "https"):
        return f"scheme {parts.scheme or '(none)'} is not allowed"
    host = parts.hostname
    if not host:
        return "URL has no host"
    try:
        addresses = [str(ipaddress.ip_address(host))]
    except ValueError:
        try:
            addresses = resolve(host)
        except OSError:
            return None  # Unresolvable: the fetch itself fails and is recorded as such.
    for address in addresses:
        if not _is_public(address):
            return f"private network target {host}"
    return None
