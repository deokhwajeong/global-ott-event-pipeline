"""Consent-enforcing regional ingest (ADR-002).

One ``RegionalIngest`` instance stands for one region's ingest endpoint.
``handle_batch`` validates and filters before anything is persisted. Dropped
batches and events are never stored; only their counts are recorded, by reason.
"""

from __future__ import annotations

import time
from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from ott_ingest.consent import InMemoryConsentStore, check_consent
from ott_ingest.delivery import DedupeWindow, correct_timestamp
from ott_ingest.partner import PartnerRegistry, sanitize_extensions
from ott_ingest.privacy import find_forbidden_identifier, is_pseudonymous_device_id
from ott_ingest.routing import region_for_market
from ott_ingest.schema import Envelope, SchemaError, parse_envelope, parse_event
from ott_ingest.stream import RegionalStream, StoredEvent


@dataclass
class BatchResult:
    accepted: int = 0
    duplicates: int = 0
    rejected: Counter[str] = field(default_factory=Counter)  # reason -> events dropped
    stripped_extensions: Counter[str] = field(default_factory=Counter)  # reason -> fields
    batch_rejection: str | None = None
    home_region: str | None = None  # set when the device posted to the wrong region


@dataclass
class IngestMetrics:
    """Operational counters. Counts only; no payload is ever kept for a drop."""

    accepted: int = 0
    duplicates: int = 0
    rejected_events: Counter[str] = field(default_factory=Counter)
    rejected_batches: Counter[str] = field(default_factory=Counter)
    stripped_extensions: Counter[str] = field(default_factory=Counter)


def _now_ms() -> int:
    return int(time.time() * 1000)


class RegionalIngest:
    def __init__(
        self,
        region: str,
        *,
        consent_store: InMemoryConsentStore,
        stream: RegionalStream,
        partners: PartnerRegistry | None = None,
        dedupe: DedupeWindow | None = None,
        clock: Callable[[], int] = _now_ms,
    ) -> None:
        if stream.region != region:
            raise ValueError("stream must belong to the same region")
        self.region = region
        self.consent_store = consent_store
        self.stream = stream
        self.partners = partners or PartnerRegistry()
        self.dedupe = dedupe or DedupeWindow()
        self.clock = clock
        self.metrics = IngestMetrics()

    def handle_batch(self, raw: Any) -> BatchResult:
        received_at = self.clock()
        result = BatchResult()

        reason, envelope = self._check_batch(raw, result)
        if reason is not None:
            events = raw.get("events") if isinstance(raw, dict) else None
            dropped = len(events) if isinstance(events, list) else 0
            result.batch_rejection = reason
            result.rejected[reason] += dropped
            self.metrics.rejected_batches[reason] += 1
            self.metrics.rejected_events[reason] += dropped
            return result

        assert envelope is not None
        for raw_event in envelope.events:
            self._ingest_event(raw_event, envelope, received_at, result)

        self.metrics.accepted += result.accepted
        self.metrics.duplicates += result.duplicates
        self.metrics.rejected_events.update(result.rejected)
        self.metrics.stripped_extensions.update(result.stripped_extensions)
        return result

    def _check_batch(self, raw: Any, result: BatchResult) -> tuple[str | None, Envelope | None]:
        """Batch-level gates, in order. Any failure drops the whole batch."""
        try:
            envelope = parse_envelope(raw)
        except SchemaError as err:
            return err.reason, None

        # Partner extensions are handled per event and may never block ingest,
        # so only the core envelope is scanned here.
        if find_forbidden_identifier(raw, skip_keys=frozenset({"ext"})):
            return "forbidden_identifier", None
        device = envelope.device
        if not is_pseudonymous_device_id(device.device_id):
            return "non_pseudonymous_device_id", None

        home = region_for_market(device.market)
        if home is None:
            return "unknown_market", None
        if home != self.region:
            # Raw events never cross regions; tell the client where it belongs.
            result.home_region = home
            return "wrong_region", None

        consent_reason = check_consent(
            self.consent_store, device.device_id, envelope.consent_version
        )
        if consent_reason is not None:
            return consent_reason, None
        return None, envelope

    def _ingest_event(
        self, raw_event: Any, envelope: Envelope, received_at: int, result: BatchResult
    ) -> None:
        try:
            event = parse_event(raw_event, envelope.version)
        except SchemaError as err:
            result.rejected[err.reason] += 1
            return

        if event.event_id in self.dedupe:
            result.duplicates += 1
            return

        ext, stripped = sanitize_extensions(event.ext, event.app_id, self.partners)
        result.stripped_extensions.update(stripped)

        device = envelope.device
        self.stream.append(
            StoredEvent(
                event_id=event.event_id,
                device_id=device.device_id,
                region=self.region,
                market=device.market.upper(),
                model=device.model,
                model_year=device.model_year,
                firmware=device.firmware,
                sdk=device.sdk,
                app_id=event.app_id,
                app_version=event.app_version,
                type=event.type,
                client_ts=event.client_ts,
                received_at=received_at,
                corrected_ts=correct_timestamp(event.client_ts, envelope.sent_at, received_at),
                envelope_version=envelope.version,
                error_code=event.error_code,
                session_id=event.session_id,
                ext=ext,
            )
        )
        self.dedupe.add(event.event_id)
        result.accepted += 1
