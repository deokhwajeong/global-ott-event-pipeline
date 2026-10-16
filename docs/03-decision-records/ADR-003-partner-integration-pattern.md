# ADR-003: Platform-First Partner Integration with Declared Extensions

## Status

Accepted (2026-10-16)

## Context

The platform hosts 20+ partner streaming apps. Each partner is a separate company with its own engineering team, release cadence, telemetry stack, and opinions about what it needs. See [Problem Space](../01-problem-space.md), especially R2 and R7, and [Lessons from the Field](../05-lessons-from-field.md), lessons 2 and 4.

Four forces shape how partners plug into the pipeline:

- **The platform cannot wait for partners (R2).** If health signals depend on every partner adopting an SDK or changing code, the slowest partner sets the schedule, and certification decisions run blind until then.
- **Partners legitimately need more.** A partner debugging startup time or DRM errors on one model needs fields the platform does not define. Saying "no" to everything pushes partners back to their own analytics, where the platform loses visibility.
- **One partner's mistake must not hurt the platform or other partners.** A malformed field, an oversized payload, or an identifier that should never be collected cannot be allowed to stop core telemetry, or to leak into storage.
- **Go / no-go needs a shared yardstick (R7).** The certification gate and the partner's own view of its release must use the same metric definitions, or every launch review becomes a debate about whose numbers are right.

## Decision

Partners integrate in three layers. Only the first is required, and it needs no partner work.

```
Layer 1: Platform core (required, no partner code)
  Platform runtime emits app_launch, playback_start, error, crash, store_install
  around every app's lifecycle, with full device context (R1, R2).

Layer 2: Declared extensions (optional, per partner)
  Partner adds fields under partner.<partner_id>.<field>, declared in a partner
  registry and reviewed during certification. Strippable; never blocks ingest.

Layer 3: Partner health report (outbound)
  Each partner receives release health for its own apps only, computed with the
  same definitions the certification gate uses.
```

Key rules:

1. **The platform owns the core.** Core events and their meanings are defined once by the platform and emitted by the platform runtime. Partners do not instrument them and cannot change them.
2. **Extensions are declared, owned, and budgeted.** A partner declares each extension field (name and scalar type) in the partner registry. A partner may only annotate events from apps it owns. Each event's extension block has a fixed size and field-count budget.
3. **Extensions can never block ingest.** An undeclared field, wrong type, wrong owner, over-budget block, or forbidden identifier is stripped and counted. The core event is stored regardless. Even an unexpected failure in extension handling results in the extension being dropped, not the event.
4. **Extension review is part of certification.** New or changed extension fields are reviewed at the same gate as the app release, including a privacy check. A field the platform cannot support on older models is rejected early, in writing, with the limit stated.
5. **Partners see their own data, aggregated.** Partner reports are scoped to the partner's apps and built from the same release-health rows as the go / no-go review. Partners do not receive raw device-level events, and never see other partners' data.

## Consequences

**Easier**

- Every partner app has baseline health from day one, including partners who never touch the integration. Certification sees the same signals before launch and in the field.
- Partners who want more detail have a sanctioned path that does not require a platform release or a schema change.
- Strip counts per partner and reason give the partner team concrete, early feedback ("your startup_ms field is arriving as a string on firmware 8.1") instead of silent data loss.
- Launch reviews argue about the issue, not the numbers, because both sides read the same definitions.

**Harder**

- The partner registry is a new governed artifact: someone owns approvals, versioning, and cleanup of fields no partner uses any more.
- Extension data is best-effort by design. Partners must accept that a field may be stripped, and dashboards built on extensions must show coverage.
- Core events only see what the platform runtime can observe. Deep in-app detail (for example, which screen a player error happened on) depends on partners adopting extensions.
- Scoped partner reports need access control and a small amount of product work, which competes with platform priorities.

## Alternatives Considered

**Mandatory platform SDK inside every partner app.** Gives rich, uniform data. Rejected as the primary path because it makes platform health depend on every partner integrating and upgrading the SDK, which in practice takes years and leaves older app versions dark. Consent enforcement would also depend on each partner getting it right.

**Server-to-server adapters that pull each partner's own telemetry.** Reuses what partners already collect. Rejected because it means one custom adapter per partner, each with different definitions, delays, and data locations, and it brings partner-held data into scope for residency and deletion without platform control at collection time.

**Free-form partner payload.** Easiest for partners. Rejected because unbounded, undeclared fields are a privacy risk (identifiers slip in unnoticed), a cost risk, and a schema risk: whatever is accepted once becomes something partners depend on.

**No partner extensions at all.** Simplest and safest. Rejected because partners would route around the platform to their own analytics for anything the core lacks, and the platform would lose the chance to see partner detail during triage.
