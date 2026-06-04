"""Smoke tests for the MCP tool functions (research_core stubbed)."""

import deepcloak.mcp_server as mcp
import deepcloak.research_core as rc
from deepcloak.config import Settings


def _result(report="REPORT", evidence_json='{"summary": {"bypassed": 2}}'):
    settings = Settings(
        provider="openai", model="m", api_key="x", search_engine="duckduckgo",
        stealth_mode="auto", depth="detailed", respect_robots=False, out=None,
        proxy=None, searxng_url=None,
    )
    return rc.Result(report=report, settings=settings, evidence=[], evidence_json=evidence_json)


def test_deep_research_returns_report_and_stores_evidence(monkeypatch):
    monkeypatch.setattr(rc, "research", lambda q, cli=None: _result())
    report = mcp.tool_deep_research("why is the sky blue")
    assert report == "REPORT"
    assert mcp.tool_get_evidence("last") == '{"summary": {"bypassed": 2}}'


def test_quick_summary_uses_quick_depth(monkeypatch):
    seen = {}

    def fake(q, cli=None):
        seen.update(cli or {})
        return _result()

    monkeypatch.setattr(rc, "research", fake)
    mcp.tool_quick_summary("q")
    assert seen["depth"] == "quick"


def test_get_evidence_unknown_run_returns_empty():
    assert mcp.tool_get_evidence("does-not-exist") == "{}"


def test_build_server_lists_clean_tool_names():
    import asyncio

    import pytest

    pytest.importorskip("mcp")  # only runs where the optional MCP dep is installed
    server = mcp.build_server()
    names = {t.name for t in asyncio.run(server.list_tools())}
    assert {"deep_research", "quick_summary", "get_evidence"} <= names
