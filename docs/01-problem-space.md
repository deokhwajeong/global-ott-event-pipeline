# Problem Space

## The question this pipeline answers

When a streaming partner ships a new app version, or the platform ships a firmware or SDK update, is anything breaking, on which TV models, in which countries, and how many viewers does it affect?

On a Smart TV platform that question is the input to two decisions a program manager owns:

1. **Go / no-go.** Before a partner app or platform release reaches the fleet, does it pass certification on every supported model?
2. **Post-launch triage.** After it ships, which issues are the most widespread, so engineering fixes those first?

Without telemetry, both decisions run on partner self-reports, QA sampling, and customer complaints, all of which arrive late and describe the loudest problem rather than the largest one.

## Why a generic event pipeline is not enough

### 1. Many apps, many models, many years of firmware

A TV platform does not have one client. It has 20+ partner apps, each built by a different company with its own release cadence, running on 100+ TV models per annual lineup, across several model years still in homes. An OS migration (for example, NetCast to webOS) or a new SDK release means every app must be revalidated. The same bug can appear only on one SoC, one firmware branch, or one country's app build.

**Implication:** every event must carry enough device context (model, model year, firmware, SDK, app version, country) to slice by any of them, and the schema must stay stable while the fleet underneath it changes.

### 2. Partners emit telemetry differently, or not at all

Each partner instruments its own app. Some send rich logs, some send none, and their field names and semantics differ. Waiting for every partner to adopt one SDK would take years.

**Implication:** the platform needs its own minimal, consistent signal (launch, playback start, error, crash, store install) collected at the platform layer, with partner-specific detail as optional, namespaced extensions.

### 3. Privacy rules decide what may be collected, where it may live, and when it must disappear

Viewers can switch collection off. GDPR and CCPA give them the right to have data deleted within a fixed time. Some jurisdictions expect certain data to stay in region. The storefront and apps run in 53 countries, so these rules differ by market and change over time.

**Implication:** consent has to be enforced before data is stored, not filtered afterward. Deletion must be a first-class workflow with an SLA. Data residency shapes where ingest and storage live, which is why this design is multi-region from the start.

### 4. The device is constrained and the network is unreliable

TVs have limited CPU and memory reserved for the app and video pipeline, sit on home Wi-Fi that drops, are switched off at the wall, and often have wrong clocks until they sync.

**Implication:** the client must batch, cap its buffer, retry with backoff, and never compete with playback. The server must tolerate late, duplicated, and out-of-order events and correct timestamps.

### 5. The people reading the data are not only engineers

The same signal has to serve a QA lead deciding whether a build passes, a partner manager explaining a regression to an external company, a privacy lead answering an auditor, and an executive asking whether a launch is healthy.

**Implication:** a small set of agreed metrics per release (crash rate, playback start failure rate, install failure rate, by model and country), defined once and used by everyone, matters more than raw volume.

## Requirements

| # | Requirement | Driven by |
|---|---|---|
| R1 | Every event carries device context: model, model year, firmware, SDK, app and app version, country | Fleet diversity |
| R2 | A minimal platform-level event set that works for every partner app without partner code changes | Partner heterogeneity |
| R3 | Consent state checked at ingest; events without valid consent are dropped, not stored | Privacy |
| R4 | Ingest and raw storage stay in the viewer's region (EU, US, APAC) | Data residency |
| R5 | Per-device deletion completes within the regulatory SLA, with an audit trail | GDPR / CCPA |
| R6 | Client batching with bounded memory; server accepts late, duplicate, and out-of-order events | Device and network limits |
| R7 | Release health visible per partner, model, and country within hours of a rollout, not days | Go / no-go and triage |
| R8 | Schema changes are versioned and backward compatible across firmware still in the field | Long device lifetimes |

## Out of scope

- Video quality-of-experience analytics at the CDN or player-bitrate level
- Advertising measurement and attribution
- Personalization and recommendations

## How we would know it works

- **Time to detect** a regression after a partner release or firmware update (target: same day)
- **Consent coverage:** share of stored events with a valid, current consent state (target: 100%)
- **Deletion SLA:** share of deletion requests completed within the regulatory window (target: 100%)
- **Triage accuracy:** the issue ranked first by affected-device count matches the one engineering fixes first

## Field context

These requirements come from eight years running partner integration, app store operations, and privacy compliance for LG's webOS Smart TV platform (100M+ devices during that time): holding certification authority for 20+ streaming partners across 100+ TV models, steering partner apps through the NetCast to webOS migration, operating the LG Content Store in 53 countries, building the GDPR and CCPA program with European and U.S. counsel, and building issue monitoring from raw customer data in Google Analytics and Tableau. This repository describes how that system would be designed today. It contains no proprietary LG designs or data.
