"""R6: bounded client batching; server accepts late, duplicate, and out-of-order events."""

from conftest import NOW, make_batch, make_event
from ott_ingest.client import BoundedEventBuffer, backoff_seconds
from ott_ingest.delivery import DedupeWindow, correct_timestamp
from ott_ingest.schema import MAX_EVENTS_PER_BATCH

HOUR = 3_600_000


def test_r6_retried_batch_is_not_double_counted(eu, device):
    device_id, version = device
    batch = make_batch(device_id, version, [make_event(), make_event()])

    first = eu.ingest.handle_batch(batch)
    retry = eu.ingest.handle_batch(batch)

    assert (first.accepted, retry.accepted, retry.duplicates) == (2, 0, 2)
    assert len(eu.stream.events) == 2


def test_r6_duplicate_inside_one_batch_is_stored_once(eu, device):
    device_id, version = device
    event = make_event()
    result = eu.ingest.handle_batch(make_batch(device_id, version, [event, dict(event)]))
    assert (result.accepted, result.duplicates) == (1, 1)


def test_r6_out_of_order_events_are_all_accepted(eu, device):
    device_id, version = device
    events = [make_event(client_ts=NOW - 1000), make_event(client_ts=NOW - 5000)]
    assert eu.ingest.handle_batch(make_batch(device_id, version, events)).accepted == 2


def test_r6_late_events_from_a_tv_that_was_offline_are_accepted(eu, device):
    device_id, version = device
    old = make_event(client_ts=NOW - 72 * HOUR)
    result = eu.ingest.handle_batch(make_batch(device_id, version, [old]))
    assert result.accepted == 1
    assert eu.stream.events[0].corrected_ts == NOW - 72 * HOUR


def test_r6_clock_corrected_from_batch_send_time(eu, device):
    """TV clock is 2 hours behind: it says it sent at NOW - 2h; server receives at NOW."""
    device_id, version = device
    skewed_sent = NOW - 2 * HOUR
    event = make_event(client_ts=skewed_sent - 60_000)

    eu.ingest.handle_batch(make_batch(device_id, version, [event], sent_at=skewed_sent))

    stored = eu.stream.events[0]
    assert stored.client_ts == skewed_sent - 60_000
    assert stored.received_at == NOW
    assert stored.corrected_ts == NOW - 60_000


def test_r6_corrected_time_never_exceeds_receive_time():
    assert correct_timestamp(client_ts=500, sent_at=100, received_at=200) == 200


def test_r6_oversized_batch_is_rejected(eu, device):
    device_id, version = device
    events = [make_event() for _ in range(MAX_EVENTS_PER_BATCH + 1)]
    result = eu.ingest.handle_batch(make_batch(device_id, version, events))
    assert result.batch_rejection == "batch_too_large"


def test_r6_dedupe_window_memory_is_bounded():
    window = DedupeWindow(max_entries=3)
    for event_id in "abcd":
        window.add(event_id)
    assert "a" not in window
    assert all(e in window for e in "bcd")


def test_r6_client_buffer_is_bounded_and_drops_oldest():
    buffer = BoundedEventBuffer(max_events=3, max_batch=2)
    for i in range(5):
        buffer.add({"n": i})
    assert len(buffer) == 3
    assert buffer.dropped == 2
    assert buffer.next_batch() == [{"n": 2}, {"n": 3}]


def test_r6_client_keeps_events_until_acknowledged():
    buffer = BoundedEventBuffer(max_events=10, max_batch=2)
    for i in range(3):
        buffer.add({"n": i})
    buffer.next_batch()  # send fails: nothing acknowledged
    assert len(buffer) == 3
    buffer.ack(2)
    assert buffer.next_batch() == [{"n": 2}]


def test_r6_backoff_grows_and_is_capped():
    no_jitter = lambda: 1.0  # noqa: E731
    assert backoff_seconds(0, rand=no_jitter) == 2.0
    assert backoff_seconds(3, rand=no_jitter) == 16.0
    assert backoff_seconds(30, rand=no_jitter) == 900.0
