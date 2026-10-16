"""ADR-002 rule 2: pseudonymous, platform-issued device IDs only."""

import pytest

from conftest import make_batch, make_event


@pytest.mark.parametrize(
    "device_id",
    ["SN-1234567890", "aa:bb:cc:dd:ee:ff", "viewer@example.com", "pd_SHORT", "192.168.0.10"],
)
def test_adr002_non_pseudonymous_device_id_is_dropped(eu, consent, device_id):
    version = consent.grant(device_id)
    result = eu.ingest.handle_batch(make_batch(device_id, version))
    assert result.batch_rejection == "non_pseudonymous_device_id"
    assert eu.stream.events == []


@pytest.mark.parametrize("where", ["device", "event", "top"])
@pytest.mark.parametrize("key", ["serial_number", "account_id", "ip_address", "MAC"])
def test_adr002_real_identifiers_anywhere_in_core_drop_the_batch(eu, device, where, key):
    device_id, version = device
    batch = make_batch(device_id, version)
    target = {"device": batch["device"], "event": batch["events"][0], "top": batch}[where]
    target[key] = "value"

    result = eu.ingest.handle_batch(batch)

    assert result.batch_rejection == "forbidden_identifier"
    assert eu.stream.events == []


def test_adr002_identifier_inside_partner_extension_is_stripped_not_blocking(eu, device):
    device_id, version = device
    event = make_event(ext={"partner.streamco.account_id": "acct-1"})

    result = eu.ingest.handle_batch(make_batch(device_id, version, [event]))

    assert result.accepted == 1
    assert result.stripped_extensions == {"ext_forbidden_identifier": 1}
    assert eu.stream.events[0].ext == {}
