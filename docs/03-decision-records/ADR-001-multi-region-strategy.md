# ADR-001: Regional Cells with Aggregate-Only Global View

## Status

Accepted (2026-10-16)

## Context

The platform serves viewers in 53 countries. [Problem Space](../01-problem-space.md) sets the constraints, and [ADR-002](ADR-002-event-ingest-pattern.md) already commits to ingest in the viewer's own region. This ADR decides what "region" means for everything behind ingest: storage, processing, consent, deletion, and the views people actually read.

Five forces shape it:

- **Residency (R4).** Raw events should stay in the viewer's region. Some jurisdictions expect it; for others it is the cleanest answer to an auditor.
- **Deletion (R5).** A deletion request has to complete within a fixed window. Every extra copy of raw data is another place to find and purge.
- **Consent on the hot path (R3).** Ingest checks consent for every batch, so the consent read path must be close to ingest and must not depend on another region being up.
- **Global decisions still exist (R7).** A go / no-go for a worldwide partner launch needs one view across all regions, within hours.
- **Long-lived clients (R6, R8).** A region's endpoint address is effectively baked into firmware for years. Whatever we choose has to survive firmware we cannot update quickly.

## Decision

Run **three independent regional cells (EU, US, APAC)** and a thin **global control plane**. Raw, device-level data never leaves its cell. The only data that crosses regions is aggregated, non-personal release-health metrics.

```
                  Global control plane (no device-level data)
          schema registry | partner registry | deploy pipeline | global health view
                     ^ config down to cells        ^ suppressed aggregates up
                     |                             |
   +-----------------+------------+---------------+-------------+-----------------+
   |  EU cell                     |  US cell                    |  APAC cell      |
   |  ingest -> stream -> raw     |  ingest -> stream -> raw    |  (same shape)   |
   |  consent read replica        |  consent read replica       |                 |
   |  deletion worker             |  deletion worker            |                 |
   |  regional health jobs        |  regional health jobs       |                 |
   +------------------------------+-----------------------------+-----------------+
```

Key rules:

1. **Home region is set by the device's registered market.** A versioned market-to-region table, reviewed with privacy counsel, maps each of the 53 markets to one cell. Moving a market between cells is a planned migration with its own deletion and cutover plan, not a config edit.
2. **Each cell is complete.** Ingest, durable stream, raw storage, processing, the consent read replica, and the deletion worker all run inside the cell. A cell keeps working when the other two, or the global plane, are down.
3. **Availability comes from zones, not from other regions.** Each cell spans multiple availability zones. If a whole cell is unavailable, clients keep buffering within their bounded memory and retry with backoff (R6). Traffic is **not** failed over to another region, because that would move raw events out of residency. Some telemetry loss during a full regional outage is an accepted cost.
4. **The global view is built from suppressed aggregates.** Each cell exports release-health rows (partner, app version, model, firmware, country, device counts, rates) on a short schedule. Rows below a minimum device count are suppressed before export so no slice can point at a household.
5. **Same code, same schema, every cell.** All cells deploy from one pipeline and one set of infrastructure modules. Schema and envelope changes roll out one cell at a time, with the smallest-traffic cell first as the canary, and every cell accepts every envelope version still in the field.

## Consequences

**Easier**

- Residency and deletion are properties of the layout, not procedures people must remember. A deletion touches one consent mapping and one cell (R5).
- A regional incident stays regional. An outage or bad deploy in one cell does not take down telemetry for the other two.
- Auditors and regional counsel can be shown one cell's boundary and the single, aggregate-only export path out of it.
- The global launch dashboard is cheap and safe to share widely, because it holds no device-level data.

**Harder**

- Three stacks cost more than one, and baseline cost does not shrink in low-traffic regions. Development-scale defaults and right-sizing per cell are needed.
- Cross-region investigations ("is this crash the same in Germany and Korea?") must work from aggregates, or be run separately inside each cell and compared. Raw cross-region joins are not available by design.
- The market-to-region table becomes a governed artifact with an owner, a review step, and change history.
- Operational discipline is needed to keep cells identical: config drift between regions is a real risk and needs automated checks.
- No cross-region failover means a full cell outage creates a telemetry gap for that region, bounded by client buffer size.

## Alternatives Considered

**Single global region, filter later.** Cheapest and simplest to operate. Rejected for the same reasons as in ADR-002: raw events leave their region before anyone decides whether they may be kept, which breaks R3 and R4 by design and turns deletion into a search.

**Active-active multi-region with cross-region replication.** Best availability and allows failover. Rejected because replication copies raw events across residency boundaries and multiplies the places a deletion must reach. The availability gain is not worth it for telemetry, where a short gap is tolerable and a compliance breach is not.

**One stack per country.** Strictest residency. Rejected as the default because 53 stacks would be costly and hard to keep consistent, and most markets do not require it. If a specific market later requires in-country storage, it becomes a fourth cell using the same modules, which this design already supports.

**Regional ingest, global storage.** Keeps ingest latency low while centralizing analytics. Rejected because the expensive compliance question is where data is stored, not where it is received. It would satisfy the letter of "regional ingest" while missing the point of R4.
