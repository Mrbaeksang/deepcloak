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
    monkeypatch.setattr(rc, "research", lambda q, cli=None, verbose=False: _fake_result())

    code = cli.main(["why is the sky blue", "--depth", "quick"])
    out = capsys.readouterr().out
    assert code == 0
    assert "Report" in out


def test_cli_writes_out_file(monkeypatch, tmp_path):
    monkeypatch.setattr(rc, "research", lambda q, cli=None, verbose=False: _fake_result("REPORT"))
    target = tmp_path / "r.md"

    code = cli.main(["q", "--out", str(target)])
    assert code == 0
    assert target.read_text() == "REPORT"
    assert (tmp_path / "r.md.evidence.json").exists()


def test_cli_no_query_prints_help():
    assert cli.main([]) == 2


def test_cli_passes_flags_through(monkeypatch):
    seen = {}

    def fake(q, cli=None, verbose=False):
        seen.update(cli or {})
        return _fake_result()

    monkeypatch.setattr(rc, "research", fake)
    cli.main(["q", "--engine", "searxng", "--stealth", "off", "--respect-robots"])
    assert seen["engine"] == "searxng"
    assert seen["stealth"] == "off"
    assert seen["respect_robots"] is True


def test_cli_models_prints_ids_one_per_line(monkeypatch, capsys):
    seen = {}

    def fake_list(provider, api_key=None, base_url=None, fetch=None, **_kw):
        seen.update(provider=provider, api_key=api_key, base_url=base_url)
        return ["zeta-model", "alpha-model"]

    monkeypatch.setattr(cli, "list_models", fake_list)
    code = cli.main(
        ["models", "--provider", "openai-endpoint", "--base-url", "http://localhost:8080/v1"]
    )
    out = capsys.readouterr().out.strip().splitlines()
    assert code == 0
    assert out == ["zeta-model", "alpha-model"]
    assert seen["provider"] == "openai-endpoint"
    assert seen["base_url"] == "http://localhost:8080/v1"


def test_cli_models_autodetects_provider_and_passes_key(monkeypatch, capsys):
    seen = {}

    def fake_list(provider, api_key=None, base_url=None, fetch=None, **_kw):
        seen.update(provider=provider, api_key=api_key)
        return ["gpt-4.1"]

    monkeypatch.setattr(cli, "list_models", fake_list)
    monkeypatch.setenv("OPENROUTER_API_KEY", "or-123")
    code = cli.main(["models"])
    assert code == 0
    assert seen["provider"] == "openrouter"
    assert seen["api_key"] == "or-123"


def test_cli_models_error_is_clean_exit_1(monkeypatch, capsys):
    from deepcloak.providers import ProviderError

    def boom(provider, **kw):
        raise ProviderError("could not list models for openrouter: 401")

    monkeypatch.setattr(cli, "list_models", boom)
    monkeypatch.setenv("OPENROUTER_API_KEY", "or-123")
    code = cli.main(["models"])
    err = capsys.readouterr().err
    assert code == 1
    assert "401" in err


def test_cli_json_mode_prints_machine_readable_result(monkeypatch, capsys):
    import json

    settings = Settings(
        provider="openai", model="gpt-4.1", api_key="sk-secret",
        search_engine="duckduckgo", stealth_mode="auto", depth="detailed",
        respect_robots=False, out=None, proxy=None, searxng_url=None,
    )
    result = rc.Result(
        report="REPORT", settings=settings,
        evidence=[{"url": "https://walled.example/"}], evidence_json='{"summary": {}}',
    )
    monkeypatch.setattr(rc, "research", lambda q, cli=None, verbose=False: result)

    code = cli.main(["why is the sky blue", "--json"])
    captured = capsys.readouterr()
    parsed = json.loads(captured.out)

    assert code == 0
    assert parsed["query"] == "why is the sky blue"
    assert parsed["report"] == "REPORT"
    assert parsed["evidence"] == [{"url": "https://walled.example/"}]
    assert parsed["settings"]["provider"] == "openai"
    assert "sk-secret" not in captured.out
