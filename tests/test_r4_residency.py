"""R4: ingest and raw storage stay in the viewer's region (EU, US, APAC)."""

from conftest import make_batch, make_event, new_device_id
from ott_ingest.health import export_aggregates, release_health
from ott_ingest.routing import MARKET_TO_REGION, REGIONS


def test_r4_eu_device_is_stored_in_eu(eu, device):
    device_id, version = device
    eu.ingest.handle_batch(make_batch(device_id, version, market="FR"))
    assert [e.region for e in eu.stream.events] == ["EU"]


def test_r4_eu_device_posting_to_us_is_refused_and_told_its_home_region(us):
    device_id = new_device_id()
    version = us.consent.grant(device_id)

    result = us.ingest.handle_batch(make_batch(device_id, version, market="DE"))

    assert result.batch_rejection == "wrong_region"
    assert result.home_region == "EU"
    assert us.stream.events == []


def test_r4_region_follows_registered_market_not_location(eu, device):
    """A German-registered TV taken abroad still reports its home market, so it stays in EU."""
    device_id, version = device
    result = eu.ingest.handle_batch(make_batch(device_id, version, market="de"))
    assert result.accepted == 1


def test_r4_unknown_market_is_dropped(eu, device):
    device_id, version = device
    result = eu.ingest.handle_batch(make_batch(device_id, version, market="ZZ"))
    assert result.batch_rejection == "unknown_market"


def test_r4_every_market_maps_to_a_known_region():
    assert set(MARKET_TO_REGION.values()) <= set(REGIONS)


def test_r4_stream_refuses_events_from_another_region(eu, us, device):
    device_id, version = device
    eu.ingest.handle_batch(make_batch(device_id, version))
    try:
        us.stream.append(eu.stream.events[0])
    except ValueError:
        pass
    else:
        raise AssertionError("cross-region append must fail")


def test_r4_only_suppressed_aggregates_leave_the_region(eu, consent):
    big, small = [], []
    for _ in range(25):
        d = new_device_id()
        eu.ingest.handle_batch(make_batch(d, consent.grant(d), [make_event()]))
        big.append(d)
    d = new_device_id()
    eu.ingest.handle_batch(make_batch(d, consent.grant(d), [make_event()], model="TV-43S"))
    small.append(d)

    exported = export_aggregates(release_health(eu.stream.events), min_devices=20)

    assert [row["model"] for row in exported] == ["TV-55X"]
    assert not any(d in repr(exported) for d in big + small)
