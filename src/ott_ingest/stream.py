"""Regional durable stream stand-in, plus per-device deletion (R4, R5)."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class StoredEvent:
    event_id: str
    device_id: str
    region: str
    market: str
    model: str
    model_year: int
    firmware: str
    sdk: str
    app_id: str
    app_version: str
    type: str
    client_ts: int
    received_at: int
    corrected_ts: int
    envelope_version: int
    error_code: str | None = None
    session_id: str | None = None
    ext: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class DeletionAuditEntry:
    """Audit trail for one deletion. Holds a one-way reference, not the device ID."""

    device_ref: str
    region: str
    events_removed: int
    completed_at: int


def device_ref(device_id: str) -> str:
    return hashlib.sha256(device_id.encode()).hexdigest()[:16]


class RegionalStream:
    """In-memory list standing in for a region's durable stream and raw storage."""

    def __init__(self, region: str) -> None:
        self.region = region
        self.events: list[StoredEvent] = []
        self.audit_log: list[DeletionAuditEntry] = []

    def append(self, event: StoredEvent) -> None:
        if event.region != self.region:  # defense in depth for R4
            raise ValueError("event does not belong to this region")
        self.events.append(event)

    def delete_device(self, device_id: str, now: int) -> DeletionAuditEntry:
        before = len(self.events)
        self.events = [e for e in self.events if e.device_id != device_id]
        entry = DeletionAuditEntry(
            device_ref=device_ref(device_id),
            region=self.region,
            events_removed=before - len(self.events),
            completed_at=now,
        )
        self.audit_log.append(entry)
        return entry
