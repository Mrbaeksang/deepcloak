"""Evidence Records — the per-URL facts captured during a research run.

Slice 3 defines the record and a collector. Slice 4 adds the report badge and
the JSON sidecar rendering on top of the same data.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field

__all__ = ["EvidenceRecord", "EvidenceLog"]


@dataclass(frozen=True)
class EvidenceRecord:
    url: str
    bot_wall: str | None  # detected Bot Wall kind, or None
    escalated: bool  # did we switch plain -> Stealth Fetch?
    bypassed: bool  # did the Stealth Fetch succeed after Escalation?
    plain_status: int | None
    elapsed_ms: int
    signal: str | None = None  # human-readable reason

    def as_dict(self) -> dict:
        return asdict(self)


@dataclass
class EvidenceLog:
    records: list[EvidenceRecord] = field(default_factory=list)

    def add(self, record: EvidenceRecord) -> None:
        self.records.append(record)

    def summary(self) -> dict:
        walls: dict[str, int] = {}
        escalated = bypassed = 0
        for r in self.records:
            escalated += int(r.escalated)
            bypassed += int(r.bypassed)
            if r.bot_wall:
                walls[r.bot_wall] = walls.get(r.bot_wall, 0) + 1
        return {
            "total": len(self.records),
            "escalated": escalated,
            "bypassed": bypassed,
            "walls": walls,
        }

    def badge(self) -> str:
        """Markdown section appended to the report. Empty when nothing was bypassed."""
        s = self.summary()
        if not s["bypassed"]:
            return ""
        plural = "s" if s["bypassed"] != 1 else ""
        lines = [f"## 🛡️ Bypassed {s['bypassed']} bot-walled source{plural}"]
        if s["walls"]:
            parts = ", ".join(f"{k} ×{v}" for k, v in sorted(s["walls"].items()))
            lines += ["", f"Bot Walls encountered — {parts}."]
        return "\n".join(lines)

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(
            {"summary": self.summary(), "records": [r.as_dict() for r in self.records]},
            indent=indent,
        )
