"""Behavior tests for fetch_router.fetch() — Escalation policy with fakes."""

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from deepcloak.bot_wall_detector import BotWall
from deepcloak.evidence import EvidenceLog
from deepcloak.fetch_router import fetch
from deepcloak.url_policy import BlockedTarget


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


CHALLENGE_HTML = "<html><title>Just a moment...</title><script src='/x.js'></script></html>"
ARTICLE_HTML = (
    Path(__file__).parent / "fixtures/pages/article_about_bot_walls.html"
).read_text(encoding="utf-8")


def _walled(_url):
    return SimpleNamespace(status_code=403, headers={}, text="denied")


def _stealth_returning(html):
    return lambda _url: html


@pytest.mark.parametrize("mode", ["auto", "always"])
def test_challenge_page_from_stealth_is_not_a_bypass(mode):
    r = fetch("https://x.test", mode=mode, plain_fetch=_walled,
              stealth_fetch=_stealth_returning(CHALLENGE_HTML))
    assert r.evidence.bypassed is False
    assert r.content is None
    assert "re-check failed" in r.evidence.signal


@pytest.mark.parametrize("mode", ["auto", "always"])
@pytest.mark.parametrize("html", ["", "   \n"])
def test_empty_page_from_stealth_is_not_a_bypass(mode, html):
    r = fetch("https://x.test", mode=mode, plain_fetch=_walled,
              stealth_fetch=_stealth_returning(html))
    assert r.evidence.bypassed is False
    assert r.content is None
    assert "empty" in r.evidence.signal


@pytest.mark.parametrize("mode", ["auto", "always"])
def test_real_content_from_stealth_is_a_bypass(mode):
    r = fetch("https://x.test", mode=mode, plain_fetch=_walled,
              stealth_fetch=_stealth_returning("<html><p>real content</p></html>"))
    assert r.evidence.bypassed is True
    assert r.content == "<html><p>real content</p></html>"


def test_article_discussing_bot_walls_is_not_a_challenge():
    r = fetch("https://x.test", plain_fetch=_walled,
              stealth_fetch=_stealth_returning(ARTICLE_HTML))
    assert r.evidence.bypassed is True
    assert r.content == ARTICLE_HTML


def test_stealth_exception_keeps_the_run_going():
    def boom(_url):
        raise RuntimeError("browser crashed")

    r = fetch("https://x.test", plain_fetch=_walled, stealth_fetch=boom)
    assert r.evidence.bypassed is False
    assert r.content == "denied"
    assert "browser crashed" in r.evidence.signal


def test_report_badge_count_matches_sidecar():
    log = EvidenceLog()
    for html in ("<p>real</p>", CHALLENGE_HTML, "", "<p>also real</p>"):
        log.add(fetch("https://x.test", plain_fetch=_walled,
                      stealth_fetch=_stealth_returning(html)).evidence)
    sidecar = json.loads(log.to_json())
    assert sum(r["bypassed"] for r in sidecar["records"]) == 2
    assert sidecar["summary"]["bypassed"] == 2
    assert "Bypassed 2 bot-walled sources" in log.badge()


def test_blocked_target_sends_no_request():
    calls = []

    def must_not_run(url):
        calls.append(url)
        raise AssertionError("request sent")

    for mode in ("auto", "always", "off"):
        r = fetch("http://127.0.0.1/", mode=mode, plain_fetch=must_not_run,
                  stealth_fetch=must_not_run, target_check=lambda _u: "private network target x")
        assert r.content is None
        assert r.evidence.bypassed is False
        assert r.evidence.escalated is False
        assert r.evidence.signal == "skipped: private network target x"
    assert calls == []


def test_blocked_redirect_does_not_escalate():
    def redirected(_url):
        raise BlockedTarget("redirect to private network target x")

    def must_not_run(_url):
        raise AssertionError("escalated")

    r = fetch("https://public.test/", plain_fetch=redirected, stealth_fetch=must_not_run)
    assert r.content is None
    assert r.evidence.escalated is False
    assert "redirect to private network target x" in r.evidence.signal


def _challenge_plain(_url):
    return SimpleNamespace(status_code=403, headers={}, text=CHALLENGE_HTML)


def test_plain_challenge_is_dropped_when_escalation_fails():
    def boom(_url):
        raise RuntimeError("browser crashed")

    r = fetch("https://x.test", plain_fetch=_challenge_plain, stealth_fetch=boom)
    assert r.content is None
    assert r.evidence.bypassed is False


def test_plain_challenge_is_dropped_when_stealth_is_off():
    r = fetch("https://x.test", mode="off", plain_fetch=_challenge_plain,
              stealth_fetch=_stealth_returning("unused"))
    assert r.content is None
    assert r.evidence.bot_wall == "cloudflare"
