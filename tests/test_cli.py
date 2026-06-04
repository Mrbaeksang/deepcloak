"""Smoke tests for the CLI — research_core is stubbed."""

import deepcloak.cli as cli
import deepcloak.research_core as rc
from deepcloak.config import Settings


def _fake_result(report="# Report\nbody"):
    settings = Settings(
        provider="openai", model="gpt-4.1", api_key="x", search_engine="duckduckgo",
        stealth_mode="auto", depth="detailed", respect_robots=False, out=None,
        proxy=None, searxng_url=None,
    )
    return rc.Result(report=report, settings=settings, evidence=[], evidence_json='{"summary": {}}')


def test_cli_prints_report(monkeypatch, capsys):
    # research is imported inside main() from research_core; patch it there.
    monkeypatch.setattr(rc, "research", lambda q, cli=None: _fake_result())

    code = cli.main(["why is the sky blue", "--depth", "quick"])
    out = capsys.readouterr().out
    assert code == 0
    assert "Report" in out


def test_cli_writes_out_file(monkeypatch, tmp_path):
    monkeypatch.setattr(rc, "research", lambda q, cli=None: _fake_result("REPORT"))
    target = tmp_path / "r.md"

    code = cli.main(["q", "--out", str(target)])
    assert code == 0
    assert target.read_text() == "REPORT"
    assert (tmp_path / "r.md.evidence.json").exists()


def test_cli_no_query_prints_help():
    assert cli.main([]) == 2


def test_cli_passes_flags_through(monkeypatch):
    seen = {}

    def fake(q, cli=None):
        seen.update(cli or {})
        return _fake_result()

    monkeypatch.setattr(rc, "research", fake)
    cli.main(["q", "--engine", "searxng", "--stealth", "off", "--respect-robots"])
    assert seen["engine"] == "searxng"
    assert seen["stealth"] == "off"
    assert seen["respect_robots"] is True
