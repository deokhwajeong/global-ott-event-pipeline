# Rollout Plan

How this pipeline would be brought into service on a live platform. Written as a program plan: each phase has a goal, scope, and exit criteria that must be met before the next phase starts. Durations are indicative and depend on firmware release windows, which are the real constraint on a TV platform.

Success metrics come from [Problem Space](01-problem-space.md#how-we-would-know-it-works):

| Metric | Target |
|---|---|
| Time to detect a regression after a partner release or firmware update | Same day |
| Consent coverage: share of stored events with a valid, current consent state | 100% |
| Deletion SLA: share of deletion requests completed within the regulatory window | 100% |
| Triage accuracy: top issue by affected devices matches what engineering fixes first | Agreed by QA and engineering at each review |

## Phases

### Phase 0: Foundations (about 6 weeks)

**Goal:** lock the parts that are hard to change later.

- Freeze envelope v1 (ADR-002) with platform, firmware, and privacy sign-off. It will live in firmware for years.
- Agree the release-health metric definitions with QA, partner management, privacy, and leadership before building dashboards (lesson 6).
- Stand up one regional cell in a non-production account; connect to the consent service's read path.
- Approve the market-to-region table with privacy counsel (ADR-001).

**Exit criteria:** envelope v1 and metric definitions signed off in writing; consent read path tested for the drop-on-unavailable behavior; market table approved.

### Phase 1: Internal pilot, one region (about 6 to 8 weeks)

**Goal:** prove the pipeline end to end on devices the platform controls.

- Ship the platform runtime emitter in an internal or beta firmware build, core events only.
- Run on lab and employee devices in one region.
- Run the first deletion drills and an internal consent audit.

**Exit criteria:** consent coverage 100% in audit sampling; deletion drills complete inside the SLA with audit entries; zero raw events found outside the pilot region; a lab-injected crash is visible on the health view the same day.

### Phase 2: Certification integration (about 8 weeks)

**Goal:** make the signal part of go / no-go, not a side dashboard.

- Use the same core metrics in the certification lab for partner app releases (lesson 2).
- Onboard two or three partner apps to the partner health report, chosen for different release cadences.
- Hold the first launch reviews using the shared metrics.

**Exit criteria:** at least one go / no-go decision made with the pipeline's metrics as evidence; partner teams confirm the report matches their own view or the gap is explained; triage ranking reviewed against what engineering chose to fix.

### Phase 3: Regional expansion and fleet rollout (about 12 weeks)

**Goal:** all three cells live, production firmware, staged by market.

- Bring up the remaining cells from the same modules, smallest-traffic cell first.
- Enable collection in production firmware in waves by market and model year, watching rejection counts by reason after each wave.
- Turn on the global health view from suppressed aggregates.

**Exit criteria:** all cells live with identical config (automated drift check passing); time to detect at same day for releases during the phase; consent coverage and deletion SLA at 100% in every region.

### Phase 4: Partner extensions (ongoing)

**Goal:** give partners the sanctioned path for more detail (ADR-003).

- Open the partner registry; review extension fields as part of certification.
- Publish strip counts back to each partner as integration feedback.

**Exit criteria:** extension review is a standard step in the certification checklist; stripped-field rate per partner is tracked and trending down after feedback.

## Risks and mitigations

| Risk | Likelihood / impact | Mitigation | Owner |
|---|---|---|---|
| Envelope v1 has a mistake that ships in firmware | Medium / high | Minimal v1, additive-only rule, multi-version parsing from day one, firmware and privacy sign-off in Phase 0 | Platform TPM, firmware lead |
| Consent service slowness or outage drops too much telemetry | Medium / medium | Regional cached read replica; drop is the safe default and is visible in rejection counts; alert on `consent_unavailable` rate | Ingest owner, consent service owner |
| Partners see the platform signal as surveillance of their app quality | Medium / medium | Core events need no partner work; partners get their own report with the same definitions; review terms in partner agreements | Partner management |
| Three regional stacks cost more than planned | High / medium | Development-scale defaults, right-size each cell, review cost per region at each phase exit | Program manager, finance partner |
| Config drift between cells | Medium / high | One deploy pipeline, automated config diff between cells, canary cell first | Platform engineering |
| Device clocks or flaky networks distort time-to-detect | Medium / low | Clock correction from send time; dedupe on `event_id`; metrics use corrected time | Ingest owner |
| Teams do not use the dashboards | Medium / high | Metric definitions agreed with users first; use them in real go / no-go and triage meetings from Phase 2 | Program manager |

## Operating metrics to watch during rollout

- Rejected events per reason per region (schema, consent, region, identifier), as a share of received events
- Stripped extension fields per partner and reason
- Duplicate rate and clock-correction offset distribution, by firmware version
- Deletion requests open versus completed, and time to complete
- Time from a partner release to first visible health row for it
