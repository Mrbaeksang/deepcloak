"""Local run history — every CLI Deep Research is kept on disk.

One directory per run under ``$DEEPCLOAK_RUNS_DIR`` (default
``~/.local/share/deepcloak/runs``) holding ``report.md``, ``evidence.json``
and ``run.json`` metadata. Pure module: paths in, data out; the caller owns
where the base directory comes from.
"""

from __future__ import annotations

import itertools
import json
import os
import pathlib
import uuid
from datetime import UTC, datetime

__all__ = ["default_dir", "save_run", "list_runs", "load_run"]

# Monotonic-per-process suffix so runs saved within the same second still
# sort newest-first by name alone.
_SEQ = itertools.count(1)


def default_dir() -> pathlib.Path:
    return pathlib.Path(
        os.environ.get("DEEPCLOAK_RUNS_DIR") or "~/.local/share/deepcloak/runs"
    ).expanduser()


def _root(base: str | None) -> pathlib.Path:
    return pathlib.Path(base) if base else default_dir()


def save_run(
    *,
    query: str,
    report: str,
    evidence_json: str,
    provider: str | None = None,
    model: str | None = None,
    depth: str | None = None,
    base: str | None = None,
) -> pathlib.Path:
    """Persist one finished run; returns its directory."""
    root = _root(base)
    run_id = (
        f"{datetime.now(UTC).strftime('%Y%m%d-%H%M%S')}"
        f"-{next(_SEQ):04d}-{uuid.uuid4().hex[:4]}"
    )
    d = root / run_id
    d.mkdir(parents=True)
    (d / "report.md").write_text(report, encoding="utf-8")
    (d / "evidence.json").write_text(evidence_json, encoding="utf-8")
    meta = {
        "id": run_id,
        "when": datetime.now(UTC).isoformat(timespec="seconds"),
        "query": query,
        "provider": provider,
        "model": model,
        "depth": depth,
    }
    (d / "run.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return d


def _read_meta(d: pathlib.Path) -> dict:
    try:
        return json.loads((d / "run.json").read_text(encoding="utf-8"))
    except Exception:
        return {}


def list_runs(base: str | None = None) -> list[dict]:
    """Summarize stored runs, newest first."""
    root = _root(base)
    if not root.is_dir():
        return []
    out = []
    for d in sorted((p for p in root.iterdir() if p.is_dir()), reverse=True):
        meta = _read_meta(d)
        out.append(
            {
                "id": d.name,
                "when": meta.get("when"),
                "query": meta.get("query", ""),
                "provider": meta.get("provider"),
                "model": meta.get("model"),
            }
        )
    return out


def load_run(run_id_prefix: str, base: str | None = None) -> dict | None:
    """Load one run by exact id or unique prefix; None if missing/ambiguous."""
    root = _root(base)
    if not root.is_dir():
        return None
    matches = sorted(d for d in root.iterdir() if d.is_dir() and d.name.startswith(run_id_prefix))
    if len(matches) != 1:
        return None
    d = matches[0]
    try:
        report = (d / "report.md").read_text(encoding="utf-8")
    except OSError:
        return None
    try:
        evidence = (d / "evidence.json").read_text(encoding="utf-8")
    except OSError:
        evidence = "{}"
    return {"id": d.name, "meta": _read_meta(d), "report": report, "evidence": evidence}
