# Trade-offs

The main trade-offs across the design, in one place. Each links to the ADR where it is argued in full.

| Trade-off | Chose | Gave up | Why | ADR |
|---|---|---|---|---|
| Privacy vs. completeness | Drop batches without valid consent, including when consent cannot be checked | Some legitimate telemetry during consent outages | Data that should not exist is never written; nothing to purge later | [ADR-002](03-decision-records/ADR-002-event-ingest-pattern.md) |
| Residency vs. availability | Regional cells, no cross-region failover | Telemetry during a full regional outage, beyond what client buffers hold | A short gap is tolerable; raw data crossing residency boundaries is not | [ADR-001](03-decision-records/ADR-001-multi-region-strategy.md) |
| Global insight vs. data movement | Global view built only from suppressed aggregates | Raw cross-region joins and small-slice detail globally | Keeps the global layer free of device-level data | [ADR-001](03-decision-records/ADR-001-multi-region-strategy.md) |
| Cost vs. isolation | Three complete regional stacks | Economies of a single stack | Fault and compliance isolation per region | [ADR-001](03-decision-records/ADR-001-multi-region-strategy.md) |
| Partner richness vs. platform independence | Platform-defined core plus optional declared extensions | Deep in-app detail from partners who do not adopt extensions | Every app has baseline health on day one without partner work | [ADR-003](03-decision-records/ADR-003-partner-integration-pattern.md) |
| Partner flexibility vs. safety | Extensions declared, budgeted, strippable | Free-form partner fields | One partner's mistake cannot block ingest or leak identifiers | [ADR-003](03-decision-records/ADR-003-partner-integration-pattern.md) |
| Schema agility vs. field longevity | Additive-only, versioned envelope | Freedom to rename or remove fields | Firmware stays in homes for years | [ADR-002](03-decision-records/ADR-002-event-ingest-pattern.md) |
| Precision vs. simplicity in time | Clock correction from batch send time | Sub-second accuracy (network latency is ignored) | Release health is an hours-scale question | [ADR-002](03-decision-records/ADR-002-event-ingest-pattern.md) |
