"""Decide whether a URL may be fetched: only public http(s) targets by default.

Search results are untrusted input, and an agent may drive DeepCloak over MCP, so a
result must not reach this machine or its private network. Pure apart from DNS,
which is injectable for tests.
"""

from __future__ import annotations

import ipaddress
import re
import socket
from collections.abc import Callable
from urllib.parse import urlsplit

__all__ = ["BlockedTarget", "blocked_reason"]

Resolver = Callable[[str], list[str]]

# Characters that make URL parsers disagree about which host a URL points to.
_AMBIGUOUS_URL = re.compile(r"[\\\s\x00-\x1f\x7f]")


class BlockedTarget(Exception):
    """A fetch (or one of its redirects) pointed at a target that is not allowed."""


def _resolve(host: str) -> list[str]:
    return [info[4][0] for info in socket.getaddrinfo(host, None)]


def _numeric_host(host: str) -> str | None:
    """A host's address when it is written as an IP, in any form a socket API accepts."""
    try:
        return str(ipaddress.ip_address(host))
    except ValueError:
        pass
    try:
        return socket.inet_ntoa(socket.inet_aton(host))  # 0177.0.0.1, 0x7f.1, 2130706433
    except OSError:
        return None


def _is_public(address: str) -> bool:
    ip = ipaddress.ip_address(address.split("%", 1)[0])
    mapped = getattr(ip, "ipv4_mapped", None)
    return (mapped or ip).is_global


def blocked_reason(url: str, resolve: Resolver = _resolve) -> str | None:
    """Why ``url`` must not be fetched, or None if it may be."""
    if _AMBIGUOUS_URL.search(url):
        return "URL contains ambiguous characters"
    parts = urlsplit(url)
    if parts.scheme not in ("http", "https"):
        return f"scheme {parts.scheme or '(none)'} is not allowed"
    if "%" in parts.netloc or "@" in parts.netloc:
        return "URL host is ambiguous"
    host = parts.hostname
    if not host:
        return "URL has no host"
    # IDNA folds lookalikes such as fullwidth digits, the same way the HTTP client does.
    host = host.encode("idna").decode("ascii").rstrip(".")
    numeric = _numeric_host(host)
    if numeric:
        addresses = [numeric]
    else:
        try:
            addresses = resolve(host)
        except OSError:
            return None  # Unresolvable: the fetch itself fails and is recorded as such.
    for address in addresses:
        if not _is_public(address):
            return f"private network target {host}"
    return None
