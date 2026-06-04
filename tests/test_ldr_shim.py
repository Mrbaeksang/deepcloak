"""Tests for the shim wiring — verified against a fake LDR downloader class."""

from deepcloak.evidence import EvidenceLog
from deepcloak.ldr_shim import install, uninstall
from deepcloak.stealth_downloader import stealth_get


class FakeResp:
    def __init__(self, status_code=200, text="ok", headers=None):
        self.status_code = status_code
        self.text = text
        self.headers = headers or {}


class FakeDownloader:
    """Stands in for LDR's AutoHTMLDownloader."""


def test_install_routes_html_through_fetch_router_and_records_evidence():
    log = EvidenceLog()
    cls = install(
        evidence_log=log,
        mode="auto",
        target_cls=FakeDownloader,
        plain_fetch=lambda u: FakeResp(status_code=403),  # 403 -> Bot Wall
        stealth_fetch=lambda u: "BYPASSED",
    )
    html = cls._fetch_html(FakeDownloader(), "http://walled.example")
    assert html == "BYPASSED"
    assert len(log.records) == 1
    rec = log.records[0]
    assert rec.escalated and rec.bypassed and rec.bot_wall == "blocked"
    uninstall(cls)
    assert not hasattr(cls, "_fetch_html")


def test_repeated_fetch_same_url_records_once_and_caches():
    log = EvidenceLog()
    calls = {"plain": 0, "stealth": 0}

    def plain(u):
        calls["plain"] += 1
        return FakeResp(status_code=403)

    def stealth(u):
        calls["stealth"] += 1
        return "BYPASSED"

    cls = install(
        evidence_log=log, mode="auto", target_cls=FakeDownloader,
        plain_fetch=plain, stealth_fetch=stealth,
    )
    inst = FakeDownloader()
    a = cls._fetch_html(inst, "http://walled")
    b = cls._fetch_html(inst, "http://walled")  # LDR's second call
    assert a == b == "BYPASSED"
    assert calls["stealth"] == 1  # stealth fetched once, not twice
    assert len(log.records) == 1  # recorded once
    uninstall(cls)


def test_install_off_mode_records_without_stealth():
    log = EvidenceLog()
    called = {"stealth": False}

    def stealth(u):
        called["stealth"] = True
        return "S"

    cls = install(
        evidence_log=log,
        mode="off",
        target_cls=FakeDownloader,
        plain_fetch=lambda u: FakeResp(status_code=403, text="blocked"),
        stealth_fetch=stealth,
    )
    html = cls._fetch_html(FakeDownloader(), "http://x")
    assert called["stealth"] is False
    assert html == "blocked"
    assert log.records[0].escalated is False
    uninstall(cls)


def test_stealth_get_raises_helpful_error_when_cloakbrowser_missing(monkeypatch):
    import sys

    import pytest

    # Force `import cloakbrowser` to fail regardless of whether it's installed.
    monkeypatch.setitem(sys.modules, "cloakbrowser", None)
    with pytest.raises(RuntimeError, match="deepcloak setup"):
        stealth_get("http://example.com")
