# Architecture Overview

How the pieces fit together. The *why* behind each piece lives in the ADRs; this page is the map.

- [ADR-001](03-decision-records/ADR-001-multi-region-strategy.md): regional cells with an aggregate-only global view
- [ADR-002](03-decision-records/ADR-002-event-ingest-pattern.md): consent-enforcing regional ingest
- [ADR-003](03-decision-records/ADR-003-partner-integration-pattern.md): platform-first partner integration with declared extensions

Diagrams use [C4](https://c4model.com/) levels and are written in Mermaid so they render on GitHub and stay diffable.

## System context (C4 level 1)

Who uses the pipeline, and what it talks to.

```mermaid
flowchart TB
    viewer(["Viewer<br/>watches TV, sets privacy choices"])
    tv["Smart TV client<br/>platform runtime plus partner apps<br/>100+ models, several firmware generations"]
    partner(["Partner engineering team<br/>20+ streaming partners"])
    qa(["Certification / QA lead<br/>go / no-go decisions"])
    pm(["Partner manager, privacy lead, leadership<br/>release health and audits"])

    pipeline[["Global OTT Event Pipeline<br/>regional ingest, storage, release health"]]

    consent["Consent and deletion service<br/>source of truth for viewer choices"]
    registry["Partner registry<br/>apps, owners, declared extension fields"]

    viewer -->|sets consent on| tv
    tv -->|batched telemetry, HTTPS| pipeline
    viewer -->|consent changes, deletion requests| consent
    consent -->|consent versions, deletion jobs| pipeline
    partner -->|declares extension fields at certification| registry
    registry -->|ownership and field rules| pipeline
    pipeline -->|own-app health reports| partner
    pipeline -->|release health by model and country| qa
    pipeline -->|aggregated dashboards, deletion audit| pm
```

## Containers (C4 level 2)

One regional cell in detail, plus the thin global control plane. The EU, US, and APAC cells are identical in shape (ADR-001).

```mermaid
flowchart LR
    subgraph client["Smart TV client"]
        runtime["Platform runtime<br/>emits core events (ADR-003 layer 1)"]
        buffer["Bounded event buffer<br/>batch, retry with backoff (R6)"]
        runtime --> buffer
    end

    subgraph cell["Regional cell: EU (US and APAC identical)"]
        ingest["Ingest API<br/>validate, consent check, dedupe,<br/>clock correction, extension strip (ADR-002)"]
        consentRO[("Consent read replica<br/>cached, regional")]
        stream[("Durable stream<br/>ordered per device")]
        raw[("Raw event store<br/>regional only")]
        jobs["Release health jobs<br/>affected-device counts (R7)"]
        health[("Regional health tables")]
        deleter["Deletion worker<br/>SLA timer, audit log (R5)"]
        ops["Ops metrics<br/>rejection counts only, no payload"]

        ingest -->|check version| consentRO
        ingest -->|accepted events| stream
        ingest -->|drop counts| ops
        stream --> raw
        raw --> jobs --> health
        deleter -->|remove device data| raw
        deleter -->|remove mapping| consentRO
    end

    subgraph global["Global control plane (no device-level data)"]
        schema["Schema registry<br/>envelope versions (R8)"]
        preg["Partner registry<br/>declared extensions (ADR-003)"]
        deploy["Deploy pipeline<br/>one cell at a time"]
        gview["Global health view<br/>suppressed aggregates (ADR-001)"]
        preports["Partner reports<br/>own apps only (ADR-003 layer 3)"]
    end

    buffer -->|HTTPS to home region by market| ingest
    schema -.->|config| ingest
    preg -.->|config| ingest
    deploy -.->|same modules| cell
    health -->|rows above min device count| gview
    health -->|scoped by app owner| preports
```

## Deployment view

Where the cells sit, and the only path data takes between them.

```mermaid
flowchart TB
    subgraph EU["EU cell"]
        eu_az["multi-AZ: ingest, stream, storage, consent replica"]
    end
    subgraph US["US cell"]
        us_az["multi-AZ: ingest, stream, storage, consent replica"]
    end
    subgraph APAC["APAC cell"]
        ap_az["multi-AZ: ingest, stream, storage, consent replica"]
    end
    G["Global control plane<br/>config and aggregates only"]

    EU -->|aggregates| G
    US -->|aggregates| G
    APAC -->|aggregates| G
    G -.->|config and deploys| EU
    G -.->|config and deploys| US
    G -.->|config and deploys| APAC
```

There is deliberately no arrow between cells. Raw events never cross regions, and there is no cross-region failover (ADR-001, rule 3).

## Request path, end to end

1. The platform runtime records a core event and adds it to a bounded buffer. When a batch is ready, the client posts it to its **home region**, which is chosen by registered market.
2. The ingest API runs batch-level gates in order: envelope schema, no real identifiers, pseudonymous device ID, correct region, and consent version. Any failure drops the whole batch and records a count by reason.
3. Each event is then validated on its own. Invalid events are dropped and counted; the rest of the batch continues. Duplicates are skipped by `event_id`. Partner extensions are checked against the registry and stripped if invalid, without affecting the core event. Timestamps are corrected from the batch's send time.
4. Accepted events go to the regional stream and raw store. Release-health jobs compute affected-device counts per partner, app version, model, firmware, and country.
5. Suppressed aggregates flow to the global view and to scoped partner reports. Deletion requests remove the consent mapping and the device's data from its home cell, with an audit entry.

## Requirement coverage

| Req | Where it is handled | Reference implementation |
|---|---|---|
| R1 device context | Envelope core, ingest validation | `src/ott_ingest/schema.py` |
| R2 platform event set | Platform runtime, core event types | `schema.CORE_EVENT_TYPES` |
| R3 consent at ingest | Ingest plus consent read replica | `consent.py`, `ingest.py` |
| R4 residency | Regional cells, market routing, aggregate-only export | `routing.py`, `health.export_aggregates` |
| R5 deletion SLA | Deletion worker, audit log | `deletion.py`, `stream.py` |
| R6 unreliable clients | Client buffer, dedupe, clock correction | `client.py`, `delivery.py` |
| R7 release health | Health jobs, global view, partner reports | `health.py` |
| R8 schema versions | Schema registry, multi-version parsing | `schema.py` |

## Status

| Piece | State |
|---|---|
| Problem space, ADR-001 to ADR-003, this overview, rollout plan | Written |
| Ingest reference implementation and tests (`src/`, `tests/`) | Working, development-scale |
| Deletion, release health, client buffer (as library code) | Working, development-scale |
| HTTP service wrapper, authentication, real stream and storage | Not built; out of scope for the reference |
| Terraform modules (`infrastructure/`) | Planned |
