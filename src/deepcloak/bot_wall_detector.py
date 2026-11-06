"""Detect a Bot Wall in a plain HTTP response.

Pure module: ``classify()`` takes a status code, headers, and body and returns a
``BotWall`` (the kind + the signal that triggered it) or ``None``. A detected
Bot Wall is what triggers an Escalation in ``fetch_router``.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from html.parser import HTMLParser
from typing import Any

__all__ = ["BotWall", "classify", "classify_html", "from_response"]


@dataclass(frozen=True)
class BotWall:
    kind: str  # cloudflare | datadome | turnstile | recaptcha | rate_limit | blocked
    signal: str  # human-readable reason, recorded in the Evidence Record


# A challenge page has little readable text. A page with more than this is treated as real
# content even if it embeds a widget or discusses Bot Walls.
_MAX_CHALLENGE_TEXT_CHARS = 1500
# Only this much HTML is scanned, so a huge page can't stall the fetch workers.
_MAX_SCANNED_CHARS = 2_000_000

# Vendor markers checked in the body (lower-cased), strongest signal first.
_TURNSTILE = ("challenges.cloudflare.com/turnstile", "cf-turnstile")
_DATADOME = ("captcha-delivery.com", "protected by datadome", "geo.captcha-delivery")
_RECAPTCHA = ("g-recaptcha", "recaptcha/api.js", "google.com/recaptcha")
_CLOUDFLARE = (
    "just a moment",
    "checking your browser",
    "/cdn-cgi/challenge-platform",
    "attention required! | cloudflare",
)


def classify(status_code: int, headers: Mapping[str, str], body: str) -> BotWall | None:
    body_l = (body or "").lower()
    hdr_l = {str(k).lower(): str(v).lower() for k, v in dict(headers or {}).items()}

    if any(m in body_l for m in _TURNSTILE):
        return BotWall("turnstile", "Cloudflare Turnstile widget present")
    if "datadome" in hdr_l.get("set-cookie", "") or "x-datadome" in hdr_l or any(
        m in body_l for m in _DATADOME
    ):
        return BotWall("datadome", "DataDome challenge present")
    if any(m in body_l for m in _RECAPTCHA):
        return BotWall("recaptcha", "reCAPTCHA widget present")
    if any(m in body_l for m in _CLOUDFLARE):
        return BotWall("cloudflare", "Cloudflare interstitial challenge")
    if hdr_l.get("cf-mitigated") == "challenge":
        return BotWall("cloudflare", "cf-mitigated: challenge header")

    if status_code == 429:
        return BotWall("rate_limit", "HTTP 429 Too Many Requests")
    if status_code == 503 and ("cf-ray" in hdr_l or "cloudflare" in body_l):
        return BotWall("cloudflare", "HTTP 503 from Cloudflare")
    if status_code == 403:
        return BotWall("blocked", "HTTP 403 Forbidden")

    return None


def from_response(resp: Any) -> BotWall | None:
    """Convenience wrapper for a requests-style response object."""
    return classify(
        status_code=getattr(resp, "status_code", 0),
        headers=getattr(resp, "headers", {}) or {},
        body=getattr(resp, "text", "") or "",
    )


class _TextLength(HTMLParser):
    """Count readable characters, skipping script and style content."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.length = 0
        self._skip_depth = 0

    def handle_starttag(self, tag: str, attrs: list) -> None:
        if tag in ("script", "style"):
            self._skip_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag in ("script", "style") and self._skip_depth:
            self._skip_depth -= 1

    def handle_data(self, data: str) -> None:
        if not self._skip_depth:
            self.length += len("".join(data.split()))


def _readable_length(html: str) -> int:
    parser = _TextLength()
    parser.feed(html[:_MAX_SCANNED_CHARS])
    parser.close()
    return parser.length


def classify_html(html: str) -> BotWall | None:
    """Re-check a page returned by a Stealth Fetch, where only the HTML is available."""
    wall = classify(200, {}, html)
    if wall is None:
        return None
    return wall if _readable_length(html) <= _MAX_CHALLENGE_TEXT_CHARS else None
