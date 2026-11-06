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

__all__ = ["BlockedTarget", "blocked_reason", "target_policy"]

Resolver = Callable[[str], list[str]]

# Characters that make URL parsers disagree about which host a URL points to.
_AMBIGUOUS_URL = re.compile(r"[\\\s\x00-\x1f\x7f]")


class BlockedTarget(Exception):
    """A fetch (or one of its redirects) pointed at a target that is not allowed."""


_IPV4_TRANSLATION_NETWORKS = tuple(
    ipaddress.ip_network(network) for network in ("::/96", "64:ff9b::/96", "::ffff:0:0:0/96")
)


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
    if not ip.is_global:
        return False
    return all(embedded.is_global for embedded in _embedded_ipv4(ip))


def _embedded_ipv4(ip: ipaddress.IPv4Address | ipaddress.IPv6Address) -> list:
    """IPv4 addresses that an IPv6 address can reach on hosts with translation."""
    if ip.version == 4:
        return []
    found = [ip.ipv4_mapped, ip.sixtofour, ip.teredo[1] if ip.teredo else None]
    if any(ip in network for network in _IPV4_TRANSLATION_NETWORKS):
        found.append(ipaddress.IPv4Address(int(ip) & 0xFFFFFFFF))
    return [address for address in found if address is not None]


def blocked_reason(
    url: str, resolve: Resolver = _resolve, allow_private: bool = False
) -> str | None:
    """Why ``url`` must not be fetched, or None if it may be. Never raises on bad input."""
    try:
        return _check(url, resolve, allow_private)
    except ValueError:  # Includes UnicodeError from an over-long or empty DNS label.
        return "invalid URL"


def _check(url: str, resolve: Resolver, allow_private: bool) -> str | None:
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
    if allow_private:
        return None
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


def target_policy(allow_private_urls: bool = False) -> Callable[[str], str | None]:
    """The check to use for a run. Opting in to private addresses keeps the other rules."""
    return lambda url: blocked_reason(url, allow_private=allow_private_urls)
