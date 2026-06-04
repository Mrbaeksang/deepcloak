"""Behavior tests for evidence summary / badge / JSON."""

import json

from deepcloak.evidence import EvidenceLog, EvidenceRecord


def _rec(url="u", wall=None, escalated=False, bypassed=False):
    return EvidenceRecord(
        url=url, bot_wall=wall, escalated=escalated, bypassed=bypassed,
        plain_status=200, elapsed_ms=10, signal="x",
    )


def test_summary_counts():
    log = EvidenceLog()
    log.add(_rec(wall="cloudflare", escalated=True, bypassed=True))
    log.add(_rec(wall="datadome", escalated=True, bypassed=False))
    log.add(_rec())  # plain, no wall
    s = log.summary()
    assert s["total"] == 3
    assert s["escalated"] == 2
    assert s["bypassed"] == 1
    assert s["walls"] == {"cloudflare": 1, "datadome": 1}


def test_badge_reports_bypass_count():
    log = EvidenceLog()
    log.add(_rec(wall="cloudflare", escalated=True, bypassed=True))
    log.add(_rec(wall="cloudflare", escalated=True, bypassed=True))
    badge = log.badge()
    assert "Bypassed 2 bot-walled sources" in badge
    assert "cloudflare ×2" in badge


def test_badge_empty_when_nothing_bypassed():
    log = EvidenceLog()
    log.add(_rec())
    assert log.badge() == ""


def test_to_json_has_summary_and_records():
    log = EvidenceLog()
    log.add(_rec(wall="turnstile", escalated=True, bypassed=True))
    data = json.loads(log.to_json())
    assert data["summary"]["bypassed"] == 1
    assert data["records"][0]["bot_wall"] == "turnstile"
