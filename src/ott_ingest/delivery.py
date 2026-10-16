"""At-least-once delivery helpers: dedupe and clock correction (ADR-002 rule 4; R6)."""

from __future__ import annotations

from collections import OrderedDict


class DedupeWindow:
    """Remembers recently accepted event IDs.

    Bounded so memory stays flat. In production this is a regional keyed store
    with a retention longer than the client's maximum retry horizon.
    """

    def __init__(self, max_entries: int = 100_000) -> None:
        self._seen: OrderedDict[str, None] = OrderedDict()
        self._max = max_entries

    def __contains__(self, event_id: str) -> bool:
        return event_id in self._seen

    def add(self, event_id: str) -> None:
        self._seen[event_id] = None
        self._seen.move_to_end(event_id)
        while len(self._seen) > self._max:
            self._seen.popitem(last=False)


def correct_timestamp(client_ts: int, sent_at: int, received_at: int) -> int:
    """Map a client-clock timestamp onto server time.

    The batch carries the client's clock reading at send time. The difference
    between that and the server's receive time is the client's clock error
    (plus network latency, which is small next to the hours-scale questions
    this pipeline answers). Applying it to each event fixes TVs whose clock
    has not synced yet. Nothing can happen after the server received it, so the
    result is clamped to receive time.
    """
    offset = received_at - sent_at
    return min(client_ts + offset, received_at)
