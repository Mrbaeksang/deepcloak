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


def test_stealth_get_raises_helpful_error_when_cloakbrowser_missing():
    # cloakbrowser is not installed in the test venv.
    import pytest

    with pytest.raises(RuntimeError, match="deepcloak setup"):
        stealth_get("http://example.com")
