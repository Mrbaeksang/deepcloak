"""Smoke tests for research_core — the path is exercised with LDR stubbed."""

import deepcloak.research_core as rc


def test_research_applies_ldr_env_and_returns_report(monkeypatch):
    captured = {}

    def fake_run_ldr(query, settings):
        captured["query"] = query
        captured["provider"] = settings.provider
        return "# Report\nbody"

    monkeypatch.setattr(rc, "_run_ldr", fake_run_ldr)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    result = rc.research("why is the sky blue", cli={}, env={"OPENAI_API_KEY": "sk-x"})

    assert result.report == "# Report\nbody"
    assert result.settings.provider == "openai"
    assert captured["query"] == "why is the sky blue"
    # to_ldr_env was applied to the process environment
    import os

    assert os.environ["LDR_LLM_PROVIDER"] == "openai"


def test_depth_selects_ldr_function():
    calls = {}

    class FakeRF:
        @staticmethod
        def quick_summary(query):
            calls["fn"] = "quick_summary"
            return "quick"

        @staticmethod
        def generate_report(query):
            calls["fn"] = "generate_report"
            return "report text"

    from deepcloak.config import resolve

    settings = resolve(cli={"depth": "report"}, env={"OPENAI_API_KEY": "x"})
    out = rc._run_ldr("q", settings, rf=FakeRF)
    assert calls["fn"] == "generate_report"
    assert out == "report text"


def test_badge_appended_to_report_when_sources_bypassed(monkeypatch):
    from deepcloak.evidence import EvidenceRecord

    def fake_install(*, evidence_log, **kw):
        evidence_log.add(
            EvidenceRecord(
                url="http://walled", bot_wall="cloudflare", escalated=True,
                bypassed=True, plain_status=403, elapsed_ms=12, signal="bypassed",
            )
        )

    monkeypatch.setattr(rc.ldr_shim, "install", fake_install)
    monkeypatch.setattr(rc, "_run_ldr", lambda q, s: "BODY")

    result = rc.research("q", cli={}, env={"OPENAI_API_KEY": "x"})
    assert "BODY" in result.report
    assert "Bypassed 1 bot-walled source" in result.report
    assert '"bypassed": 1' in result.evidence_json


def test_run_ldr_extracts_summary_from_dict():
    class FakeRF:
        @staticmethod
        def quick_summary(query):
            return {"summary": "the answer"}

    from deepcloak.config import resolve

    settings = resolve(cli={"depth": "quick"}, env={"OPENAI_API_KEY": "x"})
    assert rc._run_ldr("q", settings, rf=FakeRF) == "the answer"
