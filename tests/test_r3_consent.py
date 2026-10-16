"""R3: consent checked at ingest; events without valid consent are dropped, not stored."""

from conftest import make_batch, new_device_id


def test_r3_current_granted_consent_is_accepted(eu, device):
    device_id, version = device
    assert eu.ingest.handle_batch(make_batch(device_id, version)).accepted == 1


def test_r3_revoked_consent_drops_batch_and_stores_nothing(eu, consent, device):
    device_id, _ = device
    new_version = consent.revoke(device_id)

    result = eu.ingest.handle_batch(make_batch(device_id, new_version))

    assert result.batch_rejection == "consent_revoked"
    assert eu.stream.events == []


def test_r3_stale_consent_version_is_dropped(eu, consent, device):
    device_id, old_version = device
    consent.revoke(device_id)
    consent.grant(device_id)  # viewer changed choices; client has not synced yet

    result = eu.ingest.handle_batch(make_batch(device_id, old_version))

    assert result.batch_rejection == "consent_version_mismatch"
    assert eu.stream.events == []


def test_r3_device_without_consent_record_is_dropped(eu):
    result = eu.ingest.handle_batch(make_batch(new_device_id(), 1))
    assert result.batch_rejection == "consent_unknown_device"


def test_r3_consent_outage_fails_closed(eu, consent, device):
    device_id, version = device
    consent.available = False

    result = eu.ingest.handle_batch(make_batch(device_id, version))

    assert result.batch_rejection == "consent_unavailable"
    assert eu.stream.events == []


def test_r3_rejections_are_counted_without_payload(eu, consent, device):
    device_id, _ = device
    version = consent.revoke(device_id)
    batch = make_batch(device_id, version, events=[{"event_id": "a"}, {"event_id": "b"}])

    eu.ingest.handle_batch(batch)

    metrics = eu.ingest.metrics
    assert metrics.rejected_batches == {"consent_revoked": 1}
    assert metrics.rejected_events == {"consent_revoked": 2}
    assert device_id not in repr(metrics)
