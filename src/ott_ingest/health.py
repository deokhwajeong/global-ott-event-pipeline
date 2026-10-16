"""Release health by affected-device count (R7; ADR-001 global export; ADR-003 partner report).

Issues are ranked by how many distinct devices they touched, not by how many
events or tickets they produced: the loudest issue is rarely the largest one.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
from dataclasses import asdict, dataclass

from ott_ingest.stream import StoredEvent


@dataclass(frozen=True)
class HealthRow:
    app_id: str
    app_version: str
    model: str
    firmware: str
    market: str
    active_devices: int
    crash_devices: int
    error_devices: int

    @property
    def crash_rate(self) -> float:
        return self.crash_devices / self.active_devices if self.active_devices else 0.0


def release_health(events: Iterable[StoredEvent], *, app_id: str | None = None) -> list[HealthRow]:
    """Per (app, version, model, firmware, market) slice, worst first by affected devices.

    Passing ``app_id`` scopes the report to one partner's app (ADR-003 outbound report).
    """
    active: dict[tuple, set[str]] = defaultdict(set)
    crashed: dict[tuple, set[str]] = defaultdict(set)
    errored: dict[tuple, set[str]] = defaultdict(set)
    for e in events:
        if app_id is not None and e.app_id != app_id:
            continue
        key = (e.app_id, e.app_version, e.model, e.firmware, e.market)
        active[key].add(e.device_id)
        if e.type == "crash":
            crashed[key].add(e.device_id)
        elif e.type == "error":
            errored[key].add(e.device_id)

    rows = [
        HealthRow(*key, len(devs), len(crashed[key]), len(errored[key]))
        for key, devs in active.items()
    ]
    rows.sort(key=lambda r: (r.crash_devices, r.error_devices), reverse=True)
    return rows


def export_aggregates(rows: Iterable[HealthRow], *, min_devices: int = 20) -> list[dict]:
    """Non-personal aggregates that may leave the region for a global view (ADR-001).

    Rows with fewer active devices than ``min_devices`` are suppressed so small
    slices cannot point at individual households.
    """
    return [
        asdict(r) | {"crash_rate": r.crash_rate} for r in rows if r.active_devices >= min_devices
    ]
