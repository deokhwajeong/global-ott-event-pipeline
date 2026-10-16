"""R1: every event carries model, model year, firmware, SDK, app, app version, country."""

import pytest

from conftest import make_batch, make_event


def test_r1_stored_event_carries_full_device_and_app_context(eu, device):
    device_id, version = device
    eu.ingest.handle_batch(make_batch(device_id, version))

    (stored,) = eu.stream.events
    assert (stored.model, stored.model_year, stored.firmware, stored.sdk) == (
        "TV-55X",
        2025,
        "8.1.3",
        "8.1",
    )
    assert (stored.app_id, stored.app_version, stored.market) == ("streamco.player", "5.2.0", "DE")


@pytest.mark.parametrize("missing", ["model", "model_year", "firmware", "sdk", "market"])
def test_r1_batch_without_device_context_is_dropped(eu, device, missing):
    device_id, version = device
    batch = make_batch(device_id, version)
    del batch["device"][missing]

    result = eu.ingest.handle_batch(batch)

    assert result.batch_rejection == f"invalid_device_{missing}"
    assert eu.stream.events == []


def test_r1_event_without_app_version_is_dropped_alone(eu, device):
    device_id, version = device
    bad = make_event()
    del bad["app_version"]

    result = eu.ingest.handle_batch(make_batch(device_id, version, [bad, make_event()]))

    assert result.accepted == 1
    assert result.rejected == {"invalid_event_app_version": 1}


def test_r1_model_year_must_be_an_integer_not_a_bool(eu, device):
    device_id, version = device
    result = eu.ingest.handle_batch(make_batch(device_id, version, model_year=True))
    assert result.batch_rejection == "invalid_device_model_year"
