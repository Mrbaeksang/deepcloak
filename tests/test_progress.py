"""Tests for live progress formatting."""

from deepcloak.evidence import EvidenceRecord
from deepcloak.progress import (
    ProgressReporter,
    format_event,
    format_phase,
    make_phase_printer,
)


def _rec(**kw):
    base = dict(url="https://nowsecure.nl/", bot_wall=None, escalated=False,
               bypassed=False, plain_status=200, elapsed_ms=42, signal="x")
    base.update(kw)
    return EvidenceRecord(**base)


def test_format_bypassed():
    line = format_event(_rec(bot_wall="turnstile", escalated=True, bypassed=True))
    assert "nowsecure.nl" in line and "bypassed" in line and "turnstile" in line


def test_format_open_page():
    line = format_event(_rec())
    assert "open page" in line


def test_format_escalation_failed():
    line = format_event(_rec(bot_wall="cloudflare", escalated=True, bypassed=False))
    assert "escalation failed" in line


def test_format_uses_host_only():
    line = format_event(_rec(url="https://example.com/a/b/c?q=1"))
    assert "example.com" in line and "/a/b/c" not in line


def test_format_phase_renders_description_and_percent():
    assert "Searching" in format_phase({"status": "Searching sources", "percent": 30})
    assert "30%" in format_phase({"status": "Searching sources", "percent": 30})


def test_format_phase_tolerates_upstream_payload_variants():
    assert "Analyzing" in format_phase({"message": "Analyzing", "progress": 45})
    line = format_phase({})
    assert isinstance(line, str) and line  # never crashes, always a usable line


def test_phase_printer_writes_to_stderr(capsys):
    printer = make_phase_printer()
    printer("planning", 10, {"description": "Planning searches"})
    err = capsys.readouterr().err
    assert "Planning searches" in err and "10%" in err


# --- ProgressReporter -------------------------------------------------------


def test_reporter_plain_fallback_streams_lines_without_rich(monkeypatch):
    import io

    monkeypatch.delitem(__import__("sys").modules, "rich", raising=False)
    r = ProgressReporter(stream=io.StringIO())
    with r:
        r.phase("searching", 25, {"description": "Reading pages"})
        r(_rec())
    out = r.stream.getvalue()
    assert "Reading pages" in out and "25%" in out
    assert "nowsecure.nl" in out  # Evidence Record line went through the same sink


def test_reporter_uses_rich_status_when_available(monkeypatch):
    import io
    import sys
    import types

    updates, printed = [], []

    class FakeStatus:
        def __init__(self, text):
            self.text = text

        def start(self):
            pass

        def stop(self):
            pass

        def update(self, text):
            updates.append(text)

    class FakeConsole:
        def __init__(self, file=None, highlight=False):
            pass

        def status(self, text):
            return FakeStatus(text)

        def print(self, text):
            printed.append(text)

    rich_mod = types.ModuleType("rich")
    console_mod = types.ModuleType("rich.console")
    console_mod.Console = FakeConsole
    rich_mod.console = console_mod
    monkeypatch.setitem(sys.modules, "rich", rich_mod)
    monkeypatch.setitem(sys.modules, "rich.console", console_mod)

    r = ProgressReporter(stream=io.StringIO())
    with r:
        r.phase("searching", 25, {"description": "Reading pages"})
    assert updates == ["▸ Reading pages… 25%"]
