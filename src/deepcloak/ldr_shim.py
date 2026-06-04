"""Install the Stealth Fetch into local-deep-research (ADR-0001).

We override the narrowest seam — ``AutoHTMLDownloader._fetch_html``, the method
that returns a page's raw HTML — so every HTML fetch in LDR's pipeline runs
through ``fetch_router`` (plain → Escalate → Stealth Fetch) and records an
Evidence Record. LDR's own text extraction (justext) still runs on the HTML we
return, so we reuse it rather than reimplementing it.

The seam is an internal LDR symbol, so the LDR version is pinned (==) and the
seam must be re-verified on upgrade.
"""

from __future__ import annotations

from functools import partial
from typing import Any
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

from .evidence import EvidenceLog
from .fetch_router import fetch
from .stealth_downloader import plain_get, stealth_get

__all__ = ["install", "uninstall", "default_robots_ok", "make_fetch_html"]


def default_robots_ok(url: str) -> bool:
    """Best-effort robots.txt check; on any error, allow (fail-open)."""
    try:
        parts = urlparse(url)
        rp = RobotFileParser()
        rp.set_url(f"{parts.scheme}://{parts.netloc}/robots.txt")
        rp.read()
        return rp.can_fetch("*", url)
    except Exception:
        return True


def _load_ldr_downloader() -> type:
    from local_deep_research.research_library.downloaders.playwright_html import (  # type: ignore
        AutoHTMLDownloader,
    )

    return AutoHTMLDownloader


def make_fetch_html(*, mode, respect_robots, evidence_log, plain_fetch, stealth_fetch, robots_ok):
    # LDR may call _fetch_html more than once per URL (download / download_with_result).
    # Cache per run so we Stealth Fetch once and record exactly one Evidence Record.
    cache: dict[str, str | None] = {}

    def _fetch_html(self, url: str) -> str | None:
        if url in cache:
            return cache[url]
        result = fetch(
            url,
            mode=mode,
            plain_fetch=plain_fetch,
            stealth_fetch=stealth_fetch,
            respect_robots=respect_robots,
            robots_ok=robots_ok,
        )
        evidence_log.add(result.evidence)
        cache[url] = result.content
        return result.content

    return _fetch_html


def install(
    *,
    evidence_log: EvidenceLog,
    mode: str = "auto",
    respect_robots: bool = False,
    proxy: str | None = None,
    target_cls: type | None = None,
    plain_fetch: Any = plain_get,
    stealth_fetch: Any = None,
    robots_ok: Any = None,
) -> type:
    """Patch LDR's HTML downloader to route through DeepCloak. Returns the class."""
    cls = target_cls or _load_ldr_downloader()
    if stealth_fetch is None:
        stealth_fetch = partial(stealth_get, proxy=proxy)
    if respect_robots and robots_ok is None:
        robots_ok = default_robots_ok

    if not hasattr(cls, "_deepcloak_orig_fetch_html"):
        cls._deepcloak_orig_fetch_html = getattr(cls, "_fetch_html", None)
    cls._fetch_html = make_fetch_html(
        mode=mode,
        respect_robots=respect_robots,
        evidence_log=evidence_log,
        plain_fetch=plain_fetch,
        stealth_fetch=stealth_fetch,
        robots_ok=robots_ok,
    )
    return cls


def uninstall(cls: type) -> None:
    """Restore the original ``_fetch_html`` (used in tests / teardown)."""
    orig = getattr(cls, "_deepcloak_orig_fetch_html", None)
    if orig is not None:
        cls._fetch_html = orig
    elif hasattr(cls, "_fetch_html"):
        delattr(cls, "_fetch_html")
    if hasattr(cls, "_deepcloak_orig_fetch_html"):
        delattr(cls, "_deepcloak_orig_fetch_html")
