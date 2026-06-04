"""DeepCloak MCP server.

Its own entry point (not LDR's ldr-mcp) so the in-process stealth shim applies
and every research call produces a Bypass + Evidence. Tool bodies are plain
functions so they're testable without the MCP runtime installed.
"""

from __future__ import annotations

import itertools

__all__ = ["tool_deep_research", "tool_quick_summary", "tool_get_evidence", "build_server", "serve"]

_RUNS: dict[str, str] = {}
_COUNTER = itertools.count(1)


def tool_deep_research(query: str, depth: str = "detailed") -> str:
    """Run a Deep Research with stealth fetch and return the cited report."""
    from .research_core import research

    result = research(query, cli={"depth": depth})
    run_id = str(next(_COUNTER))
    _RUNS[run_id] = result.evidence_json
    _RUNS["last"] = result.evidence_json
    return result.report


def tool_quick_summary(query: str) -> str:
    """Fast, shallow answer for a query."""
    return tool_deep_research(query, depth="quick")


def tool_get_evidence(run_id: str = "last") -> str:
    """Return the Evidence Records (JSON) of a prior run; 'last' for the latest."""
    return _RUNS.get(run_id, "{}")


def build_server():
    """Build the FastMCP server. Requires the optional `mcp` dependency."""
    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("The MCP server needs `pip install deepcloak[mcp]`.") from exc

    server = FastMCP("deepcloak")
    server.tool(name="deep_research")(tool_deep_research)
    server.tool(name="quick_summary")(tool_quick_summary)
    server.tool(name="get_evidence")(tool_get_evidence)
    return server


def serve() -> None:  # pragma: no cover - exercised live, not in unit tests
    build_server().run()
