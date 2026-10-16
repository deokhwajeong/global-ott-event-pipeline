"""Consent store and the ingest-time consent check (ADR-002 rule 1; R3, R5).

In production this is a regional, cached read replica of the consent and
deletion service. Here it is an in-memory dictionary keyed by pseudonymous
device ID. Every change to a viewer's choices bumps the record version, and
the client echoes the version it last saw in each envelope.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ConsentStatus(Enum):
    GRANTED = "granted"
    REVOKED = "revoked"


@dataclass(frozen=True)
class ConsentRecord:
    version: int
    status: ConsentStatus


class ConsentUnavailableError(RuntimeError):
    """The consent read path could not answer. Ingest must treat this as a drop."""


class InMemoryConsentStore:
    def __init__(self) -> None:
        self._records: dict[str, ConsentRecord] = {}
        self.available = True  # flip to False to simulate an outage

    def grant(self, device_id: str) -> int:
        return self._set(device_id, ConsentStatus.GRANTED)

    def revoke(self, device_id: str) -> int:
        return self._set(device_id, ConsentStatus.REVOKED)

    def forget(self, device_id: str) -> bool:
        """Remove the record entirely (deletion workflow)."""
        return self._records.pop(device_id, None) is not None

    def get(self, device_id: str) -> ConsentRecord | None:
        if not self.available:
            raise ConsentUnavailableError
        return self._records.get(device_id)

    def _set(self, device_id: str, status: ConsentStatus) -> int:
        current = self._records.get(device_id)
        version = (current.version if current else 0) + 1
        self._records[device_id] = ConsentRecord(version=version, status=status)
        return version


def check_consent(store: InMemoryConsentStore, device_id: str, claimed_version: int) -> str | None:
    """Return a rejection reason, or None when the batch may be stored.

    Safe default: anything other than a current, granted record is a drop.
    """
    try:
        record = store.get(device_id)
    except ConsentUnavailableError:
        return "consent_unavailable"
    if record is None:
        return "consent_unknown_device"
    if record.status is not ConsentStatus.GRANTED:
        return "consent_revoked"
    if record.version != claimed_version:
        return "consent_version_mismatch"
    return None
