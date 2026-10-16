"""Per-device deletion with an SLA and audit trail (ADR-002 rule 2; R5).

Because only pseudonymous IDs are stored and raw data never leaves its region,
deletion is: remove the consent mapping, then remove the device's events from
its home region. Nothing needs to be searched for elsewhere.
"""

from __future__ import annotations

from dataclasses import dataclass

from ott_ingest.consent import InMemoryConsentStore
from ott_ingest.stream import DeletionAuditEntry, RegionalStream

DAY_MS = 24 * 60 * 60 * 1000
DELETION_SLA_MS = 30 * DAY_MS  # illustrative; the real window is set per regulation


@dataclass(frozen=True)
class DeletionReceipt:
    requested_at: int
    completed_at: int
    audit: DeletionAuditEntry
    consent_record_removed: bool

    @property
    def within_sla(self) -> bool:
        return self.completed_at - self.requested_at <= DELETION_SLA_MS


def delete_device(
    device_id: str,
    *,
    consent_store: InMemoryConsentStore,
    home_stream: RegionalStream,
    requested_at: int,
    now: int,
) -> DeletionReceipt:
    removed = consent_store.forget(device_id)
    audit = home_stream.delete_device(device_id, now=now)
    return DeletionReceipt(
        requested_at=requested_at,
        completed_at=now,
        audit=audit,
        consent_record_removed=removed,
    )
