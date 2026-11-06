"""Concrete plain and stealth fetchers used by the shim.

- ``plain_get`` is an ordinary HTTP GET (cheap, tried first).
- ``stealth_get`` drives CloakBrowser's stealth Chromium to Bypass a Bot Wall.

Both lazy-import their heavy dependency so the package imports without it.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any
from urllib.parse import urljoin

from .url_policy import BlockedTarget

__all__ = ["plain_get", "stealth_get"]

TargetCheck = Callable[[str], "str | None"]
_MAX_REDIRECTS = 5

_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0 Safari/537.36"
)


def plain_get(url: str, timeout: int = 20, target_check: TargetCheck | None = None) -> Any:
    """Plain HTTP GET, returning a requests.Response. Checks each redirect when asked to."""
    try:
        import requests
    except ImportError as exc:  # pragma: no cover - requests is a hard dep
        raise RuntimeError("requests not installed") from exc
    headers = {"User-Agent": _UA}
    if target_check is None:
        return requests.get(url, timeout=timeout, headers=headers)
    for _ in range(_MAX_REDIRECTS + 1):
        resp = requests.get(url, timeout=timeout, headers=headers, allow_redirects=False)
        if not resp.is_redirect:
            return resp
        url = urljoin(url, resp.headers["location"])
        reason = target_check(url)
        if reason:
            raise BlockedTarget(f"redirect to {reason}")
    raise RuntimeError(f"more than {_MAX_REDIRECTS} redirects")


def guard_page(page: Any, target_check: TargetCheck) -> None:
    """Abort browser requests, including subresources, to targets that are not allowed."""

    def handle(route: Any) -> None:
        if target_check(route.request.url):
            route.abort()
        else:
            route.continue_()

    page.route("**/*", handle)


def check_redirect_chain(response: Any, target_check: TargetCheck) -> None:
    """Refuse a navigation whose redirect chain passed through a blocked target."""
    request = response.request if response is not None else None
    while request is not None:
        reason = target_check(request.url)
        if reason:
            raise BlockedTarget(f"redirect to {reason}")
        request = request.redirected_from


def stealth_get(
    url: str,
    proxy: str | None = None,
    wait_ms: int = 3000,
    target_check: TargetCheck | None = None,
) -> str:
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
        if target_check is not None:
            guard_page(page, target_check)
        response = page.goto(url, wait_until="domcontentloaded", timeout=60000)
        if target_check is not None:
            check_redirect_chain(response, target_check)
        page.wait_for_timeout(wait_ms)
        return page.content()
