"""Limit concurrent requests to one host during a research run."""

from __future__ import annotations

import threading
from collections.abc import Iterator
from contextlib import contextmanager
from urllib.parse import urlsplit

__all__ = ["HostLimiter"]


class HostLimiter:
    def __init__(self, max_per_host: int = 2) -> None:
        self._max_per_host = max_per_host
        self._lock = threading.Lock()
        self._slots: dict[str, threading.Semaphore] = {}

    @contextmanager
    def slot(self, url: str) -> Iterator[None]:
        host = (urlsplit(url).hostname or "").lower()
        with self._lock:
            semaphore = self._slots.setdefault(host, threading.Semaphore(self._max_per_host))
        with semaphore:
            yield
