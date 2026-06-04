"""Evidence Records — the per-URL facts captured during a research run.

Slice 3 defines the record and a collector. Slice 4 adds the report badge and
the JSON sidecar rendering on top of the same data.
"""

from __future__ import annotations

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
