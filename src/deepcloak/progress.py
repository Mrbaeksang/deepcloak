"""Human-readable live progress for a research run.

Two event streams reach the CLI's stderr:

- ``format_event`` turns one Evidence Record into a status line (a fetch that
  hit a Bot Wall, Escalated, or Bypassed).
- ``format_phase`` / ``make_phase_printer`` render the research loop's own
  phase callbacks (LDR's ``progress_callback``), tolerating whatever payload
  shape upstream passes.
"""

from __future__ import annotations

import sys
from collections.abc import Mapping
from typing import Any

from .evidence import EvidenceRecord

__all__ = [
    "ProgressReporter",
    "format_event",
    "format_phase",
    "make_phase_printer",
    "stderr_printer",
]


def _host(url: str) -> str:
    try:
        return url.split("/")[2] if "://" in url else url
    except Exception:
        return url


def format_event(rec: EvidenceRecord) -> str:
    host = _host(rec.url)
    ms = f"{rec.elapsed_ms} ms"
    if rec.bypassed:
        return f"  🛡️  {host}  🧱 {rec.bot_wall} → ✅ bypassed   {ms}"
    if rec.escalated:
        return f"  ⚠️  {host}  🧱 {rec.bot_wall} → escalation failed   {ms}"
    if rec.bot_wall:
        return f"  •  {host}  🧱 {rec.bot_wall} (kept plain)   {ms}"
    return f"  ✓  {host}  open page   {ms}"


def stderr_printer(rec: EvidenceRecord) -> None:
    print(format_event(rec), file=sys.stderr, flush=True)


def format_phase(payload: Mapping) -> str:
    """Render one research-phase callback payload as a status line.

    Upstream payloads vary; pick the first descriptive key and any numeric
    progress indicator, and never fail on a sparse dict.
    """
    desc = next(
        (
            str(payload[k]).strip()
            for k in ("description", "message", "status", "phase")
            if payload.get(k)
        ),
        "working…",
    )
    pct = next(
        (
            v
            for k in ("percent", "progress")
            for v in [payload.get(k)]
            if isinstance(v, (int, float)) and not isinstance(v, bool)
        ),
        None,
    )
    dots = "" if desc.endswith("…") else "…"
    if pct is None:
        return f"  ▸ {desc}{dots}"
    return f"  ▸ {desc}{dots} {pct}%"


def make_phase_printer() -> Any:
    """Build a callable matching LDR's ``progress_callback`` signature."""

    def printer(status: Any = "", percent: Any = None, data: Any = None) -> None:
        merged: dict[str, Any] = {"status": status}
        if isinstance(data, Mapping):
            merged.update(data)
        if percent is not None:
            merged.setdefault("percent", percent)
        print(format_phase(merged), file=sys.stderr, flush=True)

    return printer


class ProgressReporter:
    """Verbose-mode sink for Evidence Records and research phases.

    With ``rich`` installed it renders a live status line that follows the
    research loop's phases; without it, plain stderr lines (exactly like the
    pre-rich CLI). Callable with an EvidenceRecord — the shim and retriever
    report events through ``reporter(rec)`` — and its ``phase`` method matches
    LDR's ``progress_callback`` signature. Use as a context manager spanning
    the research call so the status line starts/stops cleanly.
    """

    def __init__(self, stream: Any = None) -> None:
        self.stream = stream or sys.stderr
        try:
            from rich.console import Console  # type: ignore[import-not-found]

            self._console: Any = Console(file=self.stream, highlight=False)
        except ImportError:
            self._console = None
        self._status: Any = None

    def __enter__(self) -> ProgressReporter:
        if self._console is not None:
            self._status = self._console.status("🔎 researching…")
            self._status.start()
        return self

    def __exit__(self, *exc: Any) -> bool:
        if self._status is not None:
            self._status.stop()
            self._status = None
        return False

    def _write(self, text: str) -> None:
        print(text, file=self.stream, flush=True)

    def evidence_line(self, text: str) -> None:
        if self._console is not None:
            self._console.print(text)
        else:
            self._write(text)

    def __call__(self, rec: EvidenceRecord) -> None:
        """Receive one Evidence Record (the shim/retriever event seam)."""
        self.evidence_line(format_event(rec))

    def phase(self, status: Any = "", percent: Any = None, data: Any = None) -> None:
        """Receive one research-phase callback (LDR's progress_callback seam)."""
        merged: dict[str, Any] = {"status": status}
        if isinstance(data, Mapping):
            merged.update(data)
        if percent is not None:
            merged.setdefault("percent", percent)
        line = format_phase(merged)
        if self._status is not None:
            self._status.update(line.strip())
        else:
            self.evidence_line(line)
