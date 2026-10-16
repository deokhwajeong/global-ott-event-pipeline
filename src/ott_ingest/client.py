"""Client-side batching with bounded memory (R6).

A sketch of what the TV runtime does: buffer events up to a hard cap, drop the
oldest when full (telemetry must never compete with playback for memory), send
in batches, and back off on failure. Only acknowledged events leave the buffer.
"""

from __future__ import annotations

import random
from collections import deque
from collections.abc import Callable
from typing import Any


class BoundedEventBuffer:
    def __init__(self, max_events: int = 1000, max_batch: int = 100) -> None:
        self._events: deque[dict[str, Any]] = deque(maxlen=max_events)
        self.max_batch = max_batch
        self.dropped = 0

    def __len__(self) -> int:
        return len(self._events)

    def add(self, event: dict[str, Any]) -> None:
        if len(self._events) == self._events.maxlen:
            self.dropped += 1  # deque evicts the oldest
        self._events.append(event)

    def next_batch(self) -> list[dict[str, Any]]:
        return [self._events[i] for i in range(min(self.max_batch, len(self._events)))]

    def ack(self, count: int) -> None:
        for _ in range(min(count, len(self._events))):
            self._events.popleft()


def backoff_seconds(
    attempt: int,
    *,
    base: float = 2.0,
    cap: float = 900.0,
    rand: Callable[[], float] = random.random,
) -> float:
    """Capped exponential backoff with full jitter, so a fleet does not retry in lockstep."""
    return rand() * min(cap, base * (2**attempt))
