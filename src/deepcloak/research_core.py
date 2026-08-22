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
from .config import Settings, load_config_file, resolve
from .evidence import EvidenceLog

__all__ = ["Result", "research"]

# Maps our depth to the LDR api.research_functions callable name.
_LDR_FUNCTION = {
    "quick": "quick_summary",
    "detailed": "detailed_research",
    "report": "generate_report",
}


def _warn(message: str) -> None:
    import sys

    print(f"⚠️  {message}", file=sys.stderr, flush=True)


def _create_snapshot(overrides: dict) -> Any:
    from local_deep_research.api.settings_utils import (  # type: ignore
        create_settings_snapshot,
    )

    return create_settings_snapshot(overrides=overrides)


@dataclass
class Result:
    report: str
    settings: Settings
    evidence: list[dict[str, Any]] = field(default_factory=list)
    evidence_json: str = "{}"


def _run_ldr(
    query: str,
    settings: Settings,
    evidence_log: Any = None,
    on_event: Any = None,
    rf: Any | None = None,
) -> str:
    """Call local-deep-research's programmatic API. Imported lazily so the
    package (and its pure modules) load without the heavy upstream installed.
    ``rf`` may be injected in tests."""
    fn_kwargs: dict[str, Any] = {}
    if rf is None:
        from local_deep_research.api import research_functions as rf  # type: ignore

        overrides = settings.to_ldr_overrides()

        # Real integration: hand LDR a StealthRetriever so it synthesises over
        # full pages we fetched through the stealth path (Bypassing walls),
        # instead of search snippets. This is what makes a research run actually
        # read bot-walled sources.
        if settings.searxng_url:
            try:
                from .retriever import build_stealth_retriever

                fn_kwargs["retrievers"] = {
                    "stealth": build_stealth_retriever(
                        searxng_url=settings.searxng_url,
                        mode=settings.stealth_mode,
                        evidence_log=evidence_log,
                        on_event=on_event,
                        respect_robots=settings.respect_robots,
                        proxy=settings.proxy,
                    )
                }
                overrides["search.tool"] = "stealth"
            except Exception as exc:
                _warn(
                    f"SearXNG Stealth retriever unavailable — continuing without it: {exc}"
                )

        try:
            # Without this snapshot, search.snippets_only stays true upstream and
            # no page ever routes through the stealth shim — say so loudly.
            fn_kwargs["settings_snapshot"] = _create_snapshot(overrides)
        except Exception as exc:
            _warn(
                f"could not build LDR settings snapshot ({exc}) — falling back to "
                "environment variables; full-page fetch / Bot Wall Bypass may not apply"
            )

    fn = getattr(rf, _LDR_FUNCTION[settings.depth])
    if on_event is not None:
        import inspect

        try:
            params = inspect.signature(fn).parameters
            supported = "progress_callback" in params or any(
                p.kind is inspect.Parameter.VAR_KEYWORD for p in params.values()
            )
        except (TypeError, ValueError):
            supported = False
        if supported:
            from .progress import make_phase_printer

            fn_kwargs["progress_callback"] = (
                getattr(on_event, "phase", None)
                or make_phase_printer()
            )
    result = fn(query, **fn_kwargs)
    # LDR functions return either a string or a dict with a summary/report field.
    if isinstance(result, Mapping):
        return str(result.get("summary") or result.get("report") or result)
    return str(result)


def research(
    query: str,
    cli: Mapping | None = None,
    env: Mapping | None = None,
    verbose: bool = False,
) -> Result:
    """Run a Deep Research and return the report plus Evidence Records.

    ``verbose=True`` streams live progress to stderr (used by the CLI)."""
    import sys

    settings = resolve(
        cli or {},
        env if env is not None else os.environ,
        file=load_config_file(),
    )
    os.environ.update(settings.to_ldr_env())

    reporter = None
    if verbose:
        from .progress import ProgressReporter

        reporter = ProgressReporter()
        reporter.evidence_line(f"🔎 researching: {query}")

    evidence_log = EvidenceLog()

    import contextlib

    with contextlib.nullcontext() if reporter is None else reporter:
        try:
            ldr_shim.install(
                evidence_log=evidence_log,
                mode=settings.stealth_mode,
                respect_robots=settings.respect_robots,
                proxy=settings.proxy,
                on_event=reporter,
            )
        except Exception as exc:
            # LDR not importable yet / seam moved — proceed without Stealth Fetch,
            # but never silently: a run without the shim cannot Bypass any Bot Wall.
            _warn(
                f"Stealth Fetch shim not installed ({exc}) — bot-walled pages "
                "will NOT be bypassed this run (degraded mode)"
            )

        report = _run_ldr(
            query, settings, evidence_log=evidence_log, on_event=reporter
        )
    badge = evidence_log.badge()
    if badge:
        report = f"{report}\n\n{badge}"
    if verbose:
        s = evidence_log.summary()
        print(
            f"✅ done — {s['total']} sources, {s['bypassed']} bot wall(s) bypassed",
            file=sys.stderr,
            flush=True,
        )
    return Result(
        report=report,
        settings=settings,
        evidence=[r.as_dict() for r in evidence_log.records],
        evidence_json=evidence_log.to_json(),
    )
