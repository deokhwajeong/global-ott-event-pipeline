"""Shared builders. All data is synthetic."""

from __future__ import annotations

import uuid
from typing import Any

import pytest

from ott_ingest import InMemoryConsentStore, PartnerRegistry, RegionalIngest, RegionalStream

NOW = 1_760_000_000_000  # fixed server clock (epoch ms)


def new_device_id() -> str:
    return "pd_" + uuid.uuid4().hex


def make_event(**overrides: Any) -> dict[str, Any]:
    event = {
        "event_id": str(uuid.uuid4()),
        "type": "app_launch",
        "app_id": "streamco.player",
        "app_version": "5.2.0",
        "client_ts": NOW - 60_000,
    }
    event.update(overrides)
    return event


def make_batch(
    device_id: str,
    consent_version: int,
    events: list[dict[str, Any]] | None = None,
    *,
    market: str = "DE",
    version: int = 2,
    sent_at: int = NOW,
    **device_overrides: Any,
) -> dict[str, Any]:
    device = {
        "device_id": device_id,
        "model": "TV-55X",
        "model_year": 2025,
        "firmware": "8.1.3",
        "sdk": "8.1",
        "market": market,
    }
    device.update(device_overrides)
    return {
        "envelope_version": version,
        "device": device,
        "consent_version": consent_version,
        "sent_at": sent_at,
        "events": events if events is not None else [make_event()],
    }


class Region:
    """One region's ingest, stream, and consent store, wired together."""

    def __init__(self, name: str, consent: InMemoryConsentStore, partners: PartnerRegistry):
        self.stream = RegionalStream(name)
        self.consent = consent
        self.ingest = RegionalIngest(
            name, consent_store=consent, stream=self.stream, partners=partners, clock=lambda: NOW
        )


@pytest.fixture
def partners() -> PartnerRegistry:
    registry = PartnerRegistry()
    registry.register(
        "streamco",
        ["streamco.player"],
        {"cdn_pop": "str", "startup_ms": "int", "drm.level": "str"},
    )
    registry.register("othertv", ["othertv.app"], {"tier": "str"})
    return registry


@pytest.fixture
def consent() -> InMemoryConsentStore:
    return InMemoryConsentStore()


@pytest.fixture
def eu(consent: InMemoryConsentStore, partners: PartnerRegistry) -> Region:
    return Region("EU", consent, partners)


@pytest.fixture
def us(partners: PartnerRegistry) -> Region:
    return Region("US", InMemoryConsentStore(), partners)


@pytest.fixture
def device(consent: InMemoryConsentStore) -> tuple[str, int]:
    """An EU-registered device with consent granted. Returns (device_id, consent_version)."""
    device_id = new_device_id()
    return device_id, consent.grant(device_id)
