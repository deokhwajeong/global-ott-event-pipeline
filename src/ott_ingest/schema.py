"""Versioned event envelope (ADR-002 rule 3; requirements R1, R2, R8).

The envelope has a fixed, platform-defined core. Fields are only ever added,
never renamed or removed, so every envelope version still in the field keeps
parsing. Fields the schema does not declare are ignored and never stored.

Timestamps are epoch milliseconds to keep client parsing cheap on constrained devices.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

SUPPORTED_ENVELOPE_VERSIONS = frozenset({1, 2})

# R2: the minimal platform-level event set, emitted by the platform runtime
# around the app lifecycle, so no partner code changes are needed.
CORE_EVENT_TYPES = frozenset({"app_launch", "playback_start", "error", "crash", "store_install"})

MAX_EVENTS_PER_BATCH = 500

# R1: device context carried by every envelope.
DEVICE_FIELDS: dict[str, type] = {
    "device_id": str,
    "model": str,
    "model_year": int,
    "firmware": str,
    "sdk": str,
    "market": str,
}

# R1: app context carried by every event, plus the fields every event needs.
EVENT_FIELDS: dict[str, type] = {
    "event_id": str,
    "type": str,
    "app_id": str,
    "app_version": str,
    "client_ts": int,
}

# R8: optional fields by envelope version. Each version is a superset of the last.
OPTIONAL_EVENT_FIELDS: dict[int, dict[str, type]] = {
    1: {"error_code": str},
    2: {"error_code": str, "session_id": str},
}


class SchemaError(ValueError):
    """Raised with a short, payload-free reason code."""

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


def _is_type(value: Any, expected: type) -> bool:
    if expected is int:
        return isinstance(value, int) and not isinstance(value, bool)
    return isinstance(value, expected) and (expected is not str or value != "")


@dataclass(frozen=True)
class Device:
    device_id: str
    model: str
    model_year: int
    firmware: str
    sdk: str
    market: str


@dataclass(frozen=True)
class Event:
    event_id: str
    type: str
    app_id: str
    app_version: str
    client_ts: int
    error_code: str | None = None
    session_id: str | None = None
    ext: Any = None  # raw partner extension block, sanitized later (ADR-003)


@dataclass(frozen=True)
class Envelope:
    version: int
    device: Device
    consent_version: int
    sent_at: int
    events: list[Any] = field(default_factory=list)  # raw events, parsed one by one


def parse_envelope(raw: Any) -> Envelope:
    """Validate the batch-level part of an envelope. Any failure rejects the whole batch."""
    if not isinstance(raw, dict):
        raise SchemaError("envelope_not_object")

    version = raw.get("envelope_version")
    if not _is_type(version, int):
        raise SchemaError("missing_envelope_version")
    if version not in SUPPORTED_ENVELOPE_VERSIONS:
        raise SchemaError("unsupported_envelope_version")

    device_raw = raw.get("device")
    if not isinstance(device_raw, dict):
        raise SchemaError("missing_device")
    for name, expected in DEVICE_FIELDS.items():
        if not _is_type(device_raw.get(name), expected):
            raise SchemaError(f"invalid_device_{name}")
    device = Device(**{name: device_raw[name] for name in DEVICE_FIELDS})

    consent_version = raw.get("consent_version")
    if not _is_type(consent_version, int):
        raise SchemaError("missing_consent_version")

    sent_at = raw.get("sent_at")
    if not _is_type(sent_at, int):
        raise SchemaError("missing_sent_at")

    events = raw.get("events")
    if not isinstance(events, list) or not events:
        raise SchemaError("missing_events")
    if len(events) > MAX_EVENTS_PER_BATCH:
        raise SchemaError("batch_too_large")

    return Envelope(
        version=version,
        device=device,
        consent_version=consent_version,
        sent_at=sent_at,
        events=events,
    )


def parse_event(raw: Any, envelope_version: int) -> Event:
    """Validate one event. A failure drops only this event, not the batch."""
    if not isinstance(raw, dict):
        raise SchemaError("event_not_object")
    for name, expected in EVENT_FIELDS.items():
        if not _is_type(raw.get(name), expected):
            raise SchemaError(f"invalid_event_{name}")
    if raw["type"] not in CORE_EVENT_TYPES:
        raise SchemaError("unknown_event_type")

    optional: dict[str, Any] = {}
    for name, expected in OPTIONAL_EVENT_FIELDS[envelope_version].items():
        value = raw.get(name)
        if value is None:
            continue
        if not _is_type(value, expected):
            raise SchemaError(f"invalid_event_{name}")
        optional[name] = value

    return Event(**{name: raw[name] for name in EVENT_FIELDS}, **optional, ext=raw.get("ext"))
