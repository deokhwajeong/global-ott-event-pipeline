# Reference implementation: `ott_ingest`

A small, readable, development-scale implementation of [ADR-002](../docs/03-decision-records/ADR-002-event-ingest-pattern.md), with the parts of ADR-001 and ADR-003 it touches. Plain Python 3.12, standard library only. Not a production service.

| Module | What it shows | Requirement / ADR |
|---|---|---|
| `schema.py` | Versioned envelope; platform core event set; unknown fields ignored, never stored | R1, R2, R8 |
| `privacy.py` | Pseudonymous device IDs only; real identifiers rejected | ADR-002 rule 2 |
| `consent.py` | In-memory consent store; version check; fail closed when unavailable | R3 |
| `routing.py` | Home region by registered market | R4, ADR-001 |
| `delivery.py` | Dedupe by `event_id`; clock correction from batch send time | R6 |
| `partner.py` | `partner.<id>.*` extensions: declared, owned, budgeted, never blocking | ADR-003 |
| `ingest.py` | `RegionalIngest.handle_batch`: the gates in order; drops counted, never stored | ADR-002 |
| `stream.py`, `deletion.py` | Regional stream stand-in; per-device deletion with SLA and audit entry | R4, R5 |
| `health.py` | Release health by affected devices; partner-scoped report; suppressed export | R7, ADR-001, ADR-003 |
| `client.py` | Bounded client buffer and capped backoff | R6 |

## Usage

```python
from ott_ingest import InMemoryConsentStore, RegionalIngest, RegionalStream

consent = InMemoryConsentStore()
ingest = RegionalIngest("EU", consent_store=consent, stream=RegionalStream("EU"))

device_id = "pd_" + "0" * 32
version = consent.grant(device_id)
result = ingest.handle_batch(
    {
        "envelope_version": 2,
        "device": {
            "device_id": device_id,
            "model": "TV-55X",
            "model_year": 2025,
            "firmware": "8.1.3",
            "sdk": "8.1",
            "market": "DE",
        },
        "consent_version": version,
        "sent_at": 1_760_000_000_000,
        "events": [
            {
                "event_id": "e-1",
                "type": "app_launch",
                "app_id": "streamco.player",
                "app_version": "5.2.0",
                "client_ts": 1_759_999_990_000,
            }
        ],
    }
)
assert result.accepted == 1
```

## Running checks

```bash
pip install "pytest>=8" "ruff>=0.6"
ruff check . && ruff format --check .
pytest
```

## Deliberately left out

HTTP framing, device authentication, a real durable stream and store, and the consent service itself. Each would sit behind the same interfaces used here.
