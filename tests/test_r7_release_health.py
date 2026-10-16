"""R7: release health per partner, model, and country, ranked by affected devices."""

from conftest import make_batch, make_event, new_device_id
from ott_ingest.health import release_health


def _send(region, consent, events, **device):
    d = new_device_id()
    region.ingest.handle_batch(make_batch(d, consent.grant(d), events, **device))


def test_r7_ranks_by_affected_devices_not_event_volume(eu, consent):
    # One TV crashing 50 times is loud. Ten TVs crashing once each is larger.
    _send(eu, consent, [make_event(type="crash") for _ in range(50)], model="TV-65Z")
    for _ in range(10):
        _send(eu, consent, [make_event(type="crash")], model="TV-43S")

    top = release_health(eu.stream.events)[0]

    assert top.model == "TV-43S"
    assert top.crash_devices == 10


def test_r7_slices_by_partner_app_version_model_firmware_and_country(eu, consent):
    _send(eu, consent, [make_event(type="crash", app_version="5.3.0")], firmware="8.2.0")
    _send(eu, consent, [make_event(app_version="5.2.0")], firmware="8.1.3", market="FR")

    keys = {(r.app_version, r.firmware, r.market) for r in release_health(eu.stream.events)}

    assert keys == {("5.3.0", "8.2.0", "DE"), ("5.2.0", "8.1.3", "FR")}


def test_r7_crash_rate_uses_distinct_devices(eu, consent):
    _send(eu, consent, [make_event(), make_event(type="crash"), make_event(type="crash")])
    _send(eu, consent, [make_event()])

    (row,) = release_health(eu.stream.events)

    assert (row.active_devices, row.crash_devices, row.crash_rate) == (2, 1, 0.5)


def test_r7_partner_report_is_scoped_to_that_partners_app(eu, consent):
    _send(eu, consent, [make_event(app_id="streamco.player"), make_event(app_id="othertv.app")])

    report = release_health(eu.stream.events, app_id="othertv.app")

    assert {r.app_id for r in report} == {"othertv.app"}
