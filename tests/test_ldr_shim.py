"""Tests for the shim wiring — verified against a fake LDR downloader class."""

from types import SimpleNamespace

import pytest

from deepcloak import ldr_shim
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


def test_on_event_called_per_fetch():
    log = EvidenceLog()
    seen = []
    cls = install(
        evidence_log=log, mode="auto", target_cls=FakeDownloader,
        plain_fetch=lambda u: FakeResp(status_code=403),
        stealth_fetch=lambda u: "BYPASSED",
        on_event=seen.append,
    )
    cls._fetch_html(FakeDownloader(), "http://walled.example")
    assert len(seen) == 1 and seen[0].bypassed
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


def _local_fetch_results(**install_kwargs):
    class Downloader:
        pass

    calls = []

    def stealth(url):
        calls.append(url)
        return "<p>page</p>"

    def plain(url):
        calls.append(url)
        return FakeResp()

    log = EvidenceLog()
    cls = install(evidence_log=log, target_cls=Downloader, plain_fetch=plain,
                  stealth_fetch=stealth, **install_kwargs)
    cls._fetch_html(Downloader(), "http://127.0.0.1:9/")
    return calls, log.records[0]


def test_install_blocks_private_targets_by_default():
    calls, record = _local_fetch_results()
    assert calls == []
    assert "private network target" in record.signal


def test_install_allows_private_targets_when_asked():
    calls, record = _local_fetch_results(allow_private_urls=True)
    assert calls == ["http://127.0.0.1:9/"]
    assert record.signal == "plain ok, no wall"


def test_default_fetchers_receive_the_target_check(monkeypatch):
    requests = pytest.importorskip("requests")

    class Downloader:
        pass

    def redirect_to_local(url, **_kw):
        return SimpleNamespace(
            is_redirect=True, headers={"location": "http://127.0.0.1:9/"}, status_code=302, text=""
        )

    seen = {}

    def fake_stealth(url, proxy=None, target_check=None):
        seen["stealth"] = target_check
        return "<p>page</p>"

    monkeypatch.setattr(requests, "get", redirect_to_local)
    monkeypatch.setattr(ldr_shim, "stealth_get", fake_stealth)
    log = EvidenceLog()
    cls = install(evidence_log=log, target_cls=Downloader)
    assert cls._fetch_html(Downloader(), "https://93.184.216.34/") is None
    assert "redirect to private network target" in log.records[0].signal

    install(evidence_log=EvidenceLog(), target_cls=Downloader, plain_fetch=lambda _u: FakeResp(403))
    cls._fetch_html(Downloader(), "https://93.184.216.34/")
    assert seen["stealth"]("http://127.0.0.1/") is not None
