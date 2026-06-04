"""The Escalation policy: plain fetch first, Stealth Fetch on a detected Bot Wall.

Deep module. ``fetch()`` takes injectable ``plain_fetch`` / ``stealth_fetch``
callables so the policy is fully testable with fakes — no network, no browser.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from .bot_wall_detector import BotWall, from_response
from .evidence import EvidenceRecord

__all__ = ["FetchResult", "fetch"]

PlainFetch = Callable[[str], Any]
StealthFetch = Callable[[str], str]
Detector = Callable[[Any], "BotWall | None"]
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
    respect_robots: bool = False,
    robots_ok: RobotsOk | None = None,
) -> FetchResult:
    start = time.monotonic()

    def ms() -> int:
        return int((time.monotonic() - start) * 1000)

    def record(**kw) -> EvidenceRecord:
        kw.setdefault("plain_status", None)
        return EvidenceRecord(url=url, elapsed_ms=ms(), **kw)

    if respect_robots and robots_ok is not None and not robots_ok(url):
        return FetchResult(
            None,
            record(bot_wall=None, escalated=False, bypassed=False,
                   signal="skipped: robots.txt disallow"),
        )

    if mode == "always":
        try:
            return FetchResult(
                stealth_fetch(url),
                record(bot_wall="forced", escalated=True, bypassed=True,
                       signal="stealth fetch (mode=always)"),
            )
        except Exception as exc:
            return FetchResult(
                None,
                record(bot_wall="forced", escalated=True, bypassed=False,
                       signal=f"stealth failed: {exc}"),
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
            plain_content,
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
        return FetchResult(
            stealth_fetch(url),
            record(bot_wall=wall.kind, escalated=True, bypassed=True, plain_status=plain_status,
                   signal=f"bypassed {wall.kind}: {wall.signal}"),
        )
    except Exception as exc:
        return FetchResult(
            plain_content,
            record(bot_wall=wall.kind, escalated=True, bypassed=False, plain_status=plain_status,
                   signal=f"escalation failed: {exc}"),
        )
