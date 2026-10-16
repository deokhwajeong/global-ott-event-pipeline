# ADR-002: Consent-Enforcing Regional Ingest

## Status

Accepted (2026-10-16)

## Context

TV clients across 100+ models and several firmware generations need to send telemetry that answers one question quickly: is a partner app or platform release breaking anything, where, and for how many viewers. See [Problem Space](../01-problem-space.md), requirements R1 to R8.

Four forces shape how events get in:

- **Consent and deletion (R3, R5).** A viewer can turn collection off at any time. Data collected after that must never be stored, and stored data must be deletable within a fixed window.
- **Residency (R4).** Raw events should not leave the viewer's region.
- **Constrained, unreliable clients (R6).** TVs batch, buffer, lose power, and report wrong clocks. Delivery is at-least-once at best.
- **Long-lived firmware (R8).** A schema shipped in a TV's firmware stays in the field for years.

The ingest pattern is where all four meet. A decision here is hard to reverse, because whatever the client sends is baked into firmware.

## Decision

Clients send small batched event envelopes over HTTPS to an ingest endpoint **in their own region** (EU, US, APAC). The endpoint validates and filters **before anything is persisted**, then writes accepted events to a regional durable stream.

```
TV client                     Regional ingest (EU | US | APAC)                    Regional stream
---------                     ---------------------------------                    ---------------
batch, cap buffer,   HTTPS    1. authenticate device                  accepted    durable, ordered
retry with backoff  ------>   2. validate envelope against schema  ------------>  per device;
                              3. check consent version for device                  raw storage and
                              4. correct timestamps, dedupe by event_id            processing stay
                              5. drop or accept; never store dropped               in region
                                     |
                                     v
                              rejected counts only (no payload) -> ops metrics
```

Key rules:

1. **Consent travels with the event and is checked against the server.** Each envelope carries the device's consent version. The ingest layer compares it with the latest consent record for that pseudonymous device ID. On a mismatch or a revocation, the batch is dropped and only a count is recorded.
2. **Pseudonymous IDs only.** The client sends a rotating, platform-issued device ID, never a serial number, account ID, or IP-derived ID. The mapping to any real identity stays in the consent and deletion service, so deletion means removing one mapping plus the regional data keyed by it.
3. **Versioned envelope, platform-defined core.** The envelope has a fixed core (device context from R1 plus a small set of platform events: app launch, playback start, error, crash, store install) and an optional, namespaced `partner.<id>.*` extension. New fields are additive; the server accepts every envelope version still in the field.
4. **Idempotent and clock-tolerant.** Every event has a client-generated `event_id`. The server dedupes on it and records both client time and receive time, correcting client time from the batch's send timestamp.
5. **Region is decided by the device's market, not by the nearest endpoint.** A device registered in an EU market always posts to EU ingest, even when travelling.

## Consequences

**Easier**

- Privacy compliance is structural: data that should not exist never gets written, so there is nothing to find and purge later. Audits check one control point.
- Every partner app gets the same baseline health signal on day one, without partner code changes.
- Release health can be sliced by partner, model, firmware, and country from a single consistent schema.
- Retries and duplicates from flaky home networks do not inflate metrics.

**Harder**

- The ingest path now depends on the consent service. It needs a regional, cached, highly available read path; if consent cannot be checked, the safe default is to drop.
- Running three regional stacks costs more than one and needs consistent deployment and schema rollout across regions. See ADR-001.
- Cross-region views (for example, a global launch dashboard) must be built from aggregated, non-personal metrics exported from each region, never from raw events.
- Envelope design must be right early: once firmware ships with a schema, the server has to accept it for the device's lifetime.

## Alternatives Considered

**Third-party analytics SDK in each app (status quo in many TV ecosystems).** Fast to start and familiar to partners. Rejected as the primary path: each partner configures it differently, consent enforcement depends on every partner getting it right, data lands in a vendor's chosen region, and the platform cannot join signals across apps. Still useful as a partner's own product analytics alongside this pipeline.

**Single global ingest, filter later.** Simplest to operate. Rejected because it moves raw events out of region before deciding whether they may be kept, which breaks R3 and R4 by design, and makes deletion a search across everything.

**On-device aggregation only (send counters, not events).** Strongest privacy and smallest payloads. Rejected as the only mode because triage needs the specific model, firmware, and error code behind a spike. Kept as a fallback for markets or viewers that allow only aggregate reporting.

**Partner-reported health metrics.** No platform work needed. Rejected because reports arrive late, use different definitions per partner, and leave the platform unable to verify a partner's claim during a go / no-go decision.
