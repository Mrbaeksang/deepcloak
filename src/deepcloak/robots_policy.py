"""Honor robots.txt, following RFC 9309 when the file can't be read.

A 4xx response means there are no rules, so fetching is allowed. A server or network
error means the rules are unknown, so fetching is not. Each host's file is read once
per run.
"""

from __future__ import annotations

import threading
from collections.abc import Callable
from typing import Any
from urllib.parse import urlsplit
from urllib.robotparser import RobotFileParser

from .stealth_downloader import plain_get
from .url_policy import blocked_reason

__all__ = ["make_robots_check"]

_AGENT = "DeepCloak"
_TIMEOUT_SECONDS = 10


def _read_rules(robots_url: str, get: Callable[..., Any]) -> RobotFileParser | bool:
    """The host's rules, or a blanket allow (True) or deny (False)."""
    if blocked_reason(robots_url):
        return True  # Private hosts only pass with --allow-private-urls; there's no policy to read.
    try:
        resp = get(robots_url, timeout=_TIMEOUT_SECONDS, target_check=blocked_reason)
    except Exception:
        return False
    if 400 <= resp.status_code < 500:
        return True
    if resp.status_code != 200:
        return False
    rules = RobotFileParser()
    rules.parse(resp.text.splitlines())
    return rules


def make_robots_check(get: Callable[..., Any] = plain_get) -> Callable[[str], bool]:
    """A check for one run: returns True when robots.txt allows fetching the URL."""
    cache: dict[str, RobotFileParser | bool] = {}
    lock = threading.Lock()

    def robots_ok(url: str) -> bool:
        parts = urlsplit(url)
        robots_url = f"{parts.scheme}://{parts.netloc}/robots.txt"
        with lock:
            cached = cache.get(robots_url)
        if cached is None:
            cached = _read_rules(robots_url, get)
            with lock:
                cache[robots_url] = cached
        return cached if isinstance(cached, bool) else cached.can_fetch(_AGENT, url)

    return robots_ok
