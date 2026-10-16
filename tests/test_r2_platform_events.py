"""R2: a minimal platform event set that works for every partner app without partner code."""

import pytest

from conftest import make_batch, make_event
from ott_ingest.schema import CORE_EVENT_TYPES


@pytest.mark.parametrize("event_type", sorted(CORE_EVENT_TYPES))
def test_r2_core_event_accepted_without_any_partner_fields(eu, device, event_type):
    device_id, version = device
    result = eu.ingest.handle_batch(make_batch(device_id, version, [make_event(type=event_type)]))
    assert result.accepted == 1
    assert eu.stream.events[0].ext == {}


def test_r2_core_set_is_exactly_the_five_platform_events():
    assert {"app_launch", "playback_start", "error", "crash", "store_install"} == CORE_EVENT_TYPES


def test_r2_unknown_event_type_is_dropped_without_blocking_the_batch(eu, device):
    device_id, version = device
    events = [make_event(type="partner_custom_thing"), make_event(type="crash")]

    result = eu.ingest.handle_batch(make_batch(device_id, version, events))

    assert result.accepted == 1
    assert result.rejected == {"unknown_event_type": 1}
    assert [e.type for e in eu.stream.events] == ["crash"]


def test_r2_same_event_shape_for_every_partner_app(eu, device):
    device_id, version = device
    events = [make_event(app_id="streamco.player"), make_event(app_id="othertv.app")]
    eu.ingest.handle_batch(make_batch(device_id, version, events))
    assert {e.app_id for e in eu.stream.events} == {"streamco.player", "othertv.app"}
