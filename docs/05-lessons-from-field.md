# Lessons from the Field

Observations from eight years running partner integration, app store operations, and privacy compliance on a global Smart TV platform. They explain why the requirements in [Problem Space](01-problem-space.md) look the way they do. No proprietary designs or data are described.

## 1. The loudest issue is rarely the largest one

Customer complaints and escalations surface the problems that are easiest to notice, not the ones affecting the most viewers. Building monitoring from raw customer data, and ranking issues by how many devices they touched, changed which fixes went first and reduced complaints. **Design consequence:** release health is ranked by affected-device count per model and country (R7), not by ticket volume.

## 2. A certification gate is only as good as what it can see

Holding go / no-go authority for partner apps across 100+ TV models meant deciding with whatever evidence existed at the time. Lab QA catches what it was told to look for; the field finds the rest within days. **Design consequence:** the same small set of platform-level signals is used before launch (in certification) and after (in the field), so a pass and a regression are measured the same way.

## 3. Platform migrations reset everyone's assumptions

Moving the app ecosystem from NetCast to webOS, and every SDK release after it, required every partner app to be revalidated. Problems clustered on specific firmware and SoC combinations that no single partner could see on its own. **Design consequence:** every event carries model, model year, firmware, and SDK version (R1), and the schema has to outlive several firmware generations (R8).

## 4. Say no early, in writing, with the platform limit attached

Partner specs regularly asked for more than the platform could deliver on older models. Rejecting or renegotiating a requirement before commitment, with the specific limit stated, cost far less than discovering it in certification. **Design consequence:** the platform defines the core event set; partner-specific fields are optional extensions that cannot block ingest.

## 5. Privacy built after the fact is twice the work

Retrofitting consent and deletion onto data that was already collected meant finding every copy. Designing user controls to halt collection, and an audit-ready deletion workflow with SLAs, worked when they were part of the specification from the start. **Design consequence:** consent is enforced at ingest, before storage (ADR-002).

## 6. New tools are adopted when someone makes them useful

Analytics first looked like extra work to an operations team. It was adopted once dashboards and automated log monitoring answered questions people already had in their daily work. **Design consequence:** a few agreed release-health metrics, defined once and shared by QA, partner management, privacy, and leadership, before any long tail of raw data.
