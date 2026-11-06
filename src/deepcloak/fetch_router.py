"""The Escalation policy: plain fetch first, Stealth Fetch on a detected Bot Wall.

Deep module. ``fetch()`` takes injectable ``plain_fetch`` / ``stealth_fetch``
callables so the policy is fully testable with fakes — no network, no browser.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from .bot_wall_detector import BotWall, classify_html, from_response
from .evidence import EvidenceRecord

__all__ = ["FetchResult", "fetch"]

PlainFetch = Callable[[str], Any]
StealthFetch = Callable[[str], str]
Detector = Callable[[Any], "BotWall | None"]
HtmlDetector = Callable[[str], "BotWall | None"]
RobotsOk = Callable[[str], bool]


@dataclass
class FetchResult:
    content: str | None
    evidence: EvidenceRecord


def fetch(
    url: str,
    *,
    mode: str = "auto",
    plain_fetch: PlainFetch,
    stealth_fetch: StealthFetch,
    detector: Detector = from_response,
    html_detector: HtmlDetector = classify_html,
    respect_robots: bool = False,
    robots_ok: RobotsOk | None = None,
) -> FetchResult:
    start = time.monotonic()

    def ms() -> int:
        return int((time.monotonic() - start) * 1000)

    def record(**kw) -> EvidenceRecord:
        kw.setdefault("plain_status", None)
        return EvidenceRecord(url=url, elapsed_ms=ms(), **kw)

    def failed_recheck(html: str | None) -> str | None:
        """Why a Stealth Fetch result can't count as a Bypass, or None if it can."""
        if not html or not html.strip():
            return "stealth fetch returned an empty page"
        wall = html_detector(html)
        return f"re-check failed: {wall.signal}" if wall else None

    def usable_plain(html: str | None) -> str | None:
        """Plain content for a walled page, unless it is only the challenge itself."""
        return None if html and html_detector(html) else html

    if respect_robots and robots_ok is not None and not robots_ok(url):
        return FetchResult(
            None,
            record(bot_wall=None, escalated=False, bypassed=False,
                   signal="skipped: robots.txt disallow"),
        )

    if mode == "always":
        try:
            html = stealth_fetch(url)
        except Exception as exc:
            return FetchResult(
                None,
                record(bot_wall="forced", escalated=True, bypassed=False,
                       signal=f"stealth failed: {exc}"),
            )
        failure = failed_recheck(html)
        if failure:
            return FetchResult(
                None, record(bot_wall="forced", escalated=True, bypassed=False, signal=failure)
            )
        return FetchResult(
            html,
            record(bot_wall="forced", escalated=True, bypassed=True,
                   signal="stealth fetch (mode=always)"),
        )

    # mode "auto" or "off": try plain first.
    plain_status: int | None = None
    plain_content: str | None = None
    wall: BotWall | None = None
    try:
        resp = plain_fetch(url)
        plain_status = getattr(resp, "status_code", None)
        plain_content = getattr(resp, "text", None)
        wall = detector(resp)
    except Exception as exc:
        wall = BotWall("blocked", f"plain fetch failed: {exc}")

    if mode == "off":
        return FetchResult(
            usable_plain(plain_content) if wall else plain_content,
            record(bot_wall=wall.kind if wall else None, escalated=False, bypassed=False,
                   plain_status=plain_status, signal=wall.signal if wall else "plain ok"),
        )

    # mode "auto"
    if wall is None:
        return FetchResult(
            plain_content,
            record(bot_wall=None, escalated=False, bypassed=False,
                   plain_status=plain_status, signal="plain ok, no wall"),
        )

    try:
        html = stealth_fetch(url)
    except Exception as exc:
        return FetchResult(
            usable_plain(plain_content),
            record(bot_wall=wall.kind, escalated=True, bypassed=False, plain_status=plain_status,
                   signal=f"escalation failed: {exc}"),
        )
    failure = failed_recheck(html)
    if failure:
        return FetchResult(
            None,
            record(bot_wall=wall.kind, escalated=True, bypassed=False, plain_status=plain_status,
                   signal=failure),
        )
    return FetchResult(
        html,
        record(bot_wall=wall.kind, escalated=True, bypassed=True, plain_status=plain_status,
               signal=f"bypassed {wall.kind}: {wall.signal}"),
    )
