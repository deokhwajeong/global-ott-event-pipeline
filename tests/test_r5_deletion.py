"""R5: per-device deletion completes within the SLA, with an audit trail."""

from conftest import NOW, make_batch, new_device_id
from ott_ingest.deletion import DAY_MS, delete_device


def test_r5_deletion_removes_device_events_and_consent_mapping(eu, consent, device):
    device_id, version = device
    other = new_device_id()
    eu.ingest.handle_batch(make_batch(device_id, version))
    eu.ingest.handle_batch(make_batch(other, consent.grant(other)))

    receipt = delete_device(
        device_id, consent_store=consent, home_stream=eu.stream, requested_at=NOW, now=NOW + DAY_MS
    )

    assert receipt.audit.events_removed == 1
    assert receipt.consent_record_removed
    assert [e.device_id for e in eu.stream.events] == [other]


def test_r5_after_deletion_new_batches_from_that_device_are_dropped(eu, consent, device):
    device_id, version = device
    delete_device(
        device_id, consent_store=consent, home_stream=eu.stream, requested_at=NOW, now=NOW
    )

    result = eu.ingest.handle_batch(make_batch(device_id, version))

    assert result.batch_rejection == "consent_unknown_device"


def test_r5_receipt_reports_sla_compliance(eu, consent, device):
    device_id, _ = device
    on_time = delete_device(
        device_id, consent_store=consent, home_stream=eu.stream, requested_at=NOW, now=NOW + DAY_MS
    )
    late = delete_device(
        device_id,
        consent_store=consent,
        home_stream=eu.stream,
        requested_at=NOW,
        now=NOW + 31 * DAY_MS,
    )
    assert on_time.within_sla
    assert not late.within_sla


def test_r5_audit_trail_does_not_hold_the_device_id(eu, consent, device):
    device_id, version = device
    eu.ingest.handle_batch(make_batch(device_id, version))
    delete_device(
        device_id, consent_store=consent, home_stream=eu.stream, requested_at=NOW, now=NOW
    )

    (entry,) = eu.stream.audit_log
    assert device_id not in repr(entry)
    assert entry.region == "EU"
