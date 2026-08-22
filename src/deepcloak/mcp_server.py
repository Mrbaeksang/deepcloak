"""DeepCloak MCP server.

Its own entry point (not LDR's ldr-mcp) so the in-process stealth shim applies
and every research call produces a Bypass + Evidence. Tool bodies are plain
functions so they're testable without the MCP runtime installed.
"""

from __future__ import annotations

import itertools
import json
import os
from collections import OrderedDict

from .providers import ProviderError, detect, get, list_models

__all__ = [
    "tool_deep_research",
    "tool_quick_summary",
    "tool_get_evidence",
    "tool_list_models",
    "build_server",
    "serve",
]

# Evidence stores are capped so a long-lived server can't leak without bound.
_MAX_STORED_RUNS = 50
_RUNS: OrderedDict[str, str] = OrderedDict()
_LAST: str | None = None
_COUNTER = itertools.count(1)


def _store_run(run_id: str, evidence_json: str) -> None:
    global _LAST
    _RUNS[run_id] = evidence_json
    _LAST = evidence_json
    while len(_RUNS) > _MAX_STORED_RUNS:
        _RUNS.popitem(last=False)


def tool_deep_research(
    query: str, depth: str = "detailed", provider: str | None = None, model: str | None = None
) -> str:
    """Run a Deep Research with stealth fetch and return the cited report."""
    from .research_core import research

    opts: dict[str, str] = {"depth": depth}
    if provider:
        opts["provider"] = provider
    if model:
        opts["model"] = model
    result = research(query, cli=opts)
    run_id = str(next(_COUNTER))
    _store_run(run_id, result.evidence_json)
    return result.report


def tool_quick_summary(query: str, provider: str | None = None, model: str | None = None) -> str:
    """Fast, shallow answer for a query."""
    return tool_deep_research(query, depth="quick", provider=provider, model=model)


def tool_get_evidence(run_id: str = "last") -> str:
    """Return the Evidence Records (JSON) of a prior run; 'last' for the latest."""
    if run_id == "last":
        return _LAST or "{}"
    return _RUNS.get(run_id, "{}")


def tool_list_models(provider: str | None = None) -> str:
    """List model ids for an LLM provider as JSON; omit provider to auto-detect."""
    try:
        name = provider or detect(dict(os.environ))
        spec = get(name)
        api_key = os.environ.get(spec.env_key) if spec.env_key else None
        return json.dumps(list_models(name, api_key=api_key))
    except ProviderError as exc:
        return json.dumps({"error": str(exc)})


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
    server.tool(name="list_models")(tool_list_models)
    return server


def serve() -> None:  # pragma: no cover - exercised live, not in unit tests
    build_server().run()
