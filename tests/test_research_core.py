"""Smoke tests for research_core — the path is exercised with LDR stubbed."""

import deepcloak.research_core as rc


def test_research_applies_ldr_env_and_returns_report(monkeypatch):
    captured = {}

    def fake_run_ldr(query, settings, **kw):
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
    monkeypatch.setattr(rc, "_run_ldr", lambda q, s, **kw: "BODY")

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


def test_research_reads_config_file_layer(monkeypatch, tmp_path):
    cfg = tmp_path / "config.toml"
    cfg.write_text('depth = "report"\nmodel = "from-file"\n')
    monkeypatch.setenv("DEEPCLOAK_CONFIG", str(cfg))
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    seen = {}

    def fake_run_ldr(query, settings, **kw):
        seen["settings"] = settings
        return "R"

    monkeypatch.setattr(rc, "_run_ldr", fake_run_ldr)
    result = rc.research("q", cli={"provider": "ollama"}, env={})
    assert result.report == "R"
    assert seen["settings"].depth == "report"
    assert seen["settings"].model == "from-file"


def test_shim_install_failure_warns_instead_of_dying_silently(monkeypatch, capsys):
    def broken(*, evidence_log, **kw):
        raise RuntimeError("seam moved")

    monkeypatch.setattr(rc.ldr_shim, "install", broken)
    monkeypatch.setattr(rc, "_run_ldr", lambda q, s, **kw: "BODY")

    result = rc.research("q", cli={}, env={"OPENAI_API_KEY": "x"}, verbose=True)

    assert result.report == "BODY"  # run continues, degraded
    err = capsys.readouterr().err
    assert "Stealth Fetch" in err
    assert "seam moved" in err


def test_snapshot_failure_warns_and_run_continues(monkeypatch, capsys):
    import sys
    import types

    # Fake just enough of the LDR package so _run_ldr takes its real branch.
    ldr = types.ModuleType("local_deep_research")
    api = types.ModuleType("local_deep_research.api")
    rf_mod = types.ModuleType("local_deep_research.api.research_functions")
    rf_mod.detailed_research = staticmethod(lambda query, **kw: "ok")
    ldr.api = api
    api.research_functions = rf_mod
    monkeypatch.setitem(sys.modules, "local_deep_research", ldr)
    monkeypatch.setitem(sys.modules, "local_deep_research.api", api)
    monkeypatch.setitem(sys.modules, "local_deep_research.api.research_functions", rf_mod)

    def broken(_overrides):
        raise RuntimeError("ldr missing")

    monkeypatch.setattr(rc, "_create_snapshot", broken)
    from deepcloak.config import resolve

    settings = resolve(cli={"depth": "detailed"}, env={"OPENAI_API_KEY": "x"})
    out = rc._run_ldr("q", settings)
    assert out == "ok"
    assert "settings snapshot" in capsys.readouterr().err


def test_progress_callback_attached_when_supported_and_verbose(monkeypatch, capsys):
    import sys
    import types

    captured = {}

    def fake_detailed(query, progress_callback=None, **kw):
        captured["cb"] = progress_callback
        if progress_callback:
            progress_callback("searching", 25, {"description": "Reading pages"})
        return "ok"

    ldr = types.ModuleType("local_deep_research")
    api = types.ModuleType("local_deep_research.api")
    rf_mod = types.ModuleType("local_deep_research.api.research_functions")
    rf_mod.detailed_research = staticmethod(fake_detailed)
    ldr.api = api
    api.research_functions = rf_mod
    monkeypatch.setitem(sys.modules, "local_deep_research", ldr)
    monkeypatch.setitem(sys.modules, "local_deep_research.api", api)
    monkeypatch.setitem(sys.modules, "local_deep_research.api.research_functions", rf_mod)
    monkeypatch.setattr(rc.ldr_shim, "install", lambda **kw: None)

    out = rc.research("q", cli={"depth": "detailed"}, env={"OPENAI_API_KEY": "x"}, verbose=True)
    assert out.report == "ok"
    err = capsys.readouterr().err
    assert callable(captured["cb"])
    assert "Reading pages" in err and "25%" in err
