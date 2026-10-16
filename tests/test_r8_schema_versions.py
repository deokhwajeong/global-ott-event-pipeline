"""R8: schema changes are versioned and backward compatible across firmware in the field."""

import pytest

from conftest import make_batch, make_event


def test_r8_v1_envelope_from_older_firmware_is_still_accepted(eu, device):
    device_id, version = device
    result = eu.ingest.handle_batch(make_batch(device_id, version, version=1))
    assert result.accepted == 1
    assert eu.stream.events[0].envelope_version == 1


def test_r8_v2_adds_session_id_without_breaking_v1(eu, device):
    device_id, version = device
    v2 = make_batch(device_id, version, [make_event(session_id="s-1")], version=2)
    v1 = make_batch(device_id, version, [make_event(session_id="s-2")], version=1)

    eu.ingest.handle_batch(v2)
    eu.ingest.handle_batch(v1)

    # v1 does not declare session_id, so it is ignored rather than trusted.
    assert [e.session_id for e in eu.stream.events] == ["s-1", None]


def test_r8_unknown_fields_are_ignored_and_never_stored(eu, device):
    device_id, version = device
    event = make_event(future_field="x")
    batch = make_batch(device_id, version, [event])
    batch["future_top_level"] = {"anything": 1}

    result = eu.ingest.handle_batch(batch)

    assert result.accepted == 1
    assert "future_field" not in repr(eu.stream.events[0])


@pytest.mark.parametrize("bad_version", [0, 3, 99])
def test_r8_unsupported_envelope_version_is_rejected(eu, device, bad_version):
    device_id, version = device
    result = eu.ingest.handle_batch(make_batch(device_id, version, version=bad_version))
    assert result.batch_rejection == "unsupported_envelope_version"


def test_r8_missing_envelope_version_is_rejected(eu, device):
    device_id, version = device
    batch = make_batch(device_id, version)
    del batch["envelope_version"]
    assert eu.ingest.handle_batch(batch).batch_rejection == "missing_envelope_version"


def test_r8_non_object_payload_is_rejected_cleanly(eu):
    assert eu.ingest.handle_batch(["not", "an", "envelope"]).batch_rejection == (
        "envelope_not_object"
    )
