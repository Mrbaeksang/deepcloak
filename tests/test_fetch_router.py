"""Behavior tests for fetch_router.fetch() — Escalation policy with fakes."""

from deepcloak.bot_wall_detector import BotWall
from deepcloak.fetch_router import fetch


class FakeResp:
    def __init__(self, status_code=200, text="ok", headers=None):
        self.status_code = status_code
        self.text = text
        self.headers = headers or {}


def _plain(resp=None, exc=None):
    def f(url):
        if exc:
            raise exc
        return resp or FakeResp()
    return f


def _stealth(content="STEALTH", exc=None):
    def f(url):
        if exc:
            raise exc
        return content
    return f


WALL = lambda resp: BotWall("cloudflare", "challenge")  # noqa: E731
NOWALL = lambda resp: None  # noqa: E731


def test_auto_no_wall_returns_plain_without_escalating():
    r = fetch("u", mode="auto", plain_fetch=_plain(FakeResp(text="PLAIN")),
              stealth_fetch=_stealth(), detector=NOWALL)
    assert r.content == "PLAIN"
    assert r.evidence.escalated is False
    assert r.evidence.bypassed is False
    assert r.evidence.bot_wall is None


def test_auto_wall_escalates_and_bypasses():
    r = fetch("u", mode="auto", plain_fetch=_plain(FakeResp(status_code=403)),
              stealth_fetch=_stealth("CONTENT"), detector=WALL)
    assert r.content == "CONTENT"
    assert r.evidence.escalated is True
    assert r.evidence.bypassed is True
    assert r.evidence.bot_wall == "cloudflare"
    assert r.evidence.plain_status == 403


def test_auto_wall_stealth_failure_degrades_to_plain():
    r = fetch("u", mode="auto", plain_fetch=_plain(FakeResp(text="PARTIAL")),
              stealth_fetch=_stealth(exc=RuntimeError("no chromium")), detector=WALL)
    assert r.content == "PARTIAL"
    assert r.evidence.escalated is True
    assert r.evidence.bypassed is False


def test_always_mode_skips_plain():
    called = {"plain": False}

    def plain(url):
        called["plain"] = True
        return FakeResp()

    r = fetch("u", mode="always", plain_fetch=plain, stealth_fetch=_stealth("S"), detector=WALL)
    assert r.content == "S"
    assert called["plain"] is False
    assert r.evidence.escalated is True


def test_off_mode_never_escalates_even_with_wall():
    called = {"stealth": False}

    def stealth(url):
        called["stealth"] = True
        return "S"

    r = fetch("u", mode="off", plain_fetch=_plain(FakeResp(text="PLAIN")),
              stealth_fetch=stealth, detector=WALL)
    assert r.content == "PLAIN"
    assert called["stealth"] is False
    assert r.evidence.escalated is False
    assert r.evidence.bot_wall == "cloudflare"  # still recorded


def test_respect_robots_disallow_skips_fetch():
    called = {"plain": False}

    def plain(url):
        called["plain"] = True
        return FakeResp()

    r = fetch("u", mode="auto", plain_fetch=plain, stealth_fetch=_stealth(),
              detector=WALL, respect_robots=True, robots_ok=lambda u: False)
    assert r.content is None
    assert called["plain"] is False
    assert "robots" in r.evidence.signal


def test_plain_failure_escalates_to_stealth():
    r = fetch("u", mode="auto", plain_fetch=_plain(exc=ConnectionError("boom")),
              stealth_fetch=_stealth("RECOVERED"), detector=NOWALL)
    assert r.content == "RECOVERED"
    assert r.evidence.escalated is True
    assert r.evidence.bypassed is True
