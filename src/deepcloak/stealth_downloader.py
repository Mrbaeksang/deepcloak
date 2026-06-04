"""Concrete plain and stealth fetchers used by the shim.

- ``plain_get`` is an ordinary HTTP GET (cheap, tried first).
- ``stealth_get`` drives CloakBrowser's stealth Chromium to Bypass a Bot Wall.

Both lazy-import their heavy dependency so the package imports without it.
"""

from __future__ import annotations

from typing import Any

__all__ = ["plain_get", "stealth_get"]

_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0 Safari/537.36"
)


def plain_get(url: str, timeout: int = 20) -> Any:
    """Plain HTTP GET, returning a requests.Response."""
    try:
        import requests
    except ImportError as exc:  # pragma: no cover - requests is a hard dep
        raise RuntimeError("requests not installed") from exc
    return requests.get(url, timeout=timeout, headers={"User-Agent": _UA})


def stealth_get(url: str, proxy: str | None = None, wait_ms: int = 3000) -> str:
    """Fetch a page through CloakBrowser's stealth Chromium and return its HTML."""
    try:
        import cloakbrowser
    except ImportError as exc:
        raise RuntimeError(
            "cloakbrowser is not installed or the stealth browser is missing — "
            "run `deepcloak setup`."
        ) from exc

    kwargs: dict[str, Any] = {}
    if proxy:
        kwargs["proxy"] = proxy
    with cloakbrowser.launch_context(**kwargs) as ctx:
        page = ctx.new_page()
        page.goto(url, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(wait_ms)
        return page.content()
