"""Behavior tests for the local run-history store."""

import json

from deepcloak.history import list_runs, load_run, save_run


def _save(base, i=0):
    return save_run(
        query=f"query {i}",
        report=f"# Report {i}",
        evidence_json=json.dumps({"summary": {"bypassed": i}}),
        provider="openai",
        model="gpt-4.1",
        depth="detailed",
        base=str(base),
    )


def test_save_run_writes_report_evidence_and_meta(tmp_path):
    d = _save(tmp_path, 2)
    assert (d / "report.md").read_text(encoding="utf-8") == "# Report 2"
    evidence = json.loads((d / "evidence.json").read_text(encoding="utf-8"))
    assert evidence["summary"]["bypassed"] == 2
    meta = json.loads((d / "run.json").read_text(encoding="utf-8"))
    assert meta["query"] == "query 2"
    assert meta["provider"] == "openai"
    assert meta["when"]


def test_list_runs_is_newest_first(tmp_path):
    older = _save(tmp_path, 0)
    newer = _save(tmp_path, 1)
    runs = list_runs(str(tmp_path))
    assert [r["id"] for r in runs] == [newer.name, older.name]
    assert runs[0]["query"] == "query 1"


def test_list_runs_missing_dir_is_empty(tmp_path):
    assert list_runs(str(tmp_path / "nope")) == []


def test_load_run_accepts_unique_prefix(tmp_path):
    saved = _save(tmp_path, 7)
    got = load_run(saved.name[:10], base=str(tmp_path))
    assert got["report"] == "# Report 7"
    assert got["meta"]["query"] == "query 7"
    assert '"summary"' in got["evidence"]


def test_load_run_unknown_or_ambiguous_returns_none(tmp_path):
    _save(tmp_path, 0)
    assert load_run("zzz", base=str(tmp_path)) is None


def test_default_dir_respects_env(monkeypatch, tmp_path):
    import deepcloak.history as h

    monkeypatch.setenv("DEEPCLOAK_RUNS_DIR", str(tmp_path / "runs"))
    assert h.default_dir() == tmp_path / "runs"
