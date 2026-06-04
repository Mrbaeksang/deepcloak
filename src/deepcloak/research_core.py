"""The single entry point every surface (CLI, MCP, skill) goes through.

It resolves settings, applies the LDR environment, runs the research loop, and
attaches Evidence Records. In slice 1 this is the plain path; the stealth shim
is installed here from slice 3 onward.
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from . import ldr_shim
from .config import Settings, resolve
from .evidence import EvidenceLog

__all__ = ["Result", "research"]

# Maps our depth to the LDR api.research_functions callable name.
_LDR_FUNCTION = {
    "quick": "quick_summary",
    "detailed": "detailed_research",
    "report": "generate_report",
}


@dataclass
class Result:
    report: str
    settings: Settings
    evidence: list[dict[str, Any]] = field(default_factory=list)
    evidence_json: str = "{}"


def _run_ldr(query: str, settings: Settings, rf: Any | None = None) -> str:
    """Call local-deep-research's programmatic API. Imported lazily so the
    package (and its pure modules) load without the heavy upstream installed.
    ``rf`` may be injected in tests."""
    if rf is None:
        from local_deep_research.api import research_functions as rf  # type: ignore

    fn = getattr(rf, _LDR_FUNCTION[settings.depth])
    result = fn(query)
    # LDR functions return either a string or a dict with a summary/report field.
    if isinstance(result, Mapping):
        return str(result.get("summary") or result.get("report") or result)
    return str(result)


def research(query: str, cli: Mapping | None = None, env: Mapping | None = None) -> Result:
    """Run a Deep Research and return the report plus Evidence Records."""
    settings = resolve(cli or {}, env if env is not None else os.environ)
    os.environ.update(settings.to_ldr_env())

    evidence_log = EvidenceLog()
    try:
        ldr_shim.install(
            evidence_log=evidence_log,
            mode=settings.stealth_mode,
            respect_robots=settings.respect_robots,
            proxy=settings.proxy,
        )
    except Exception:
        # LDR not importable yet / seam moved — proceed without stealth (degraded).
        pass

    report = _run_ldr(query, settings)
    badge = evidence_log.badge()
    if badge:
        report = f"{report}\n\n{badge}"
    return Result(
        report=report,
        settings=settings,
        evidence=[r.as_dict() for r in evidence_log.records],
        evidence_json=evidence_log.to_json(),
    )
