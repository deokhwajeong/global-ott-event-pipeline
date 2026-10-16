# Global OTT Event Pipeline

Reference architecture for ingesting and processing telemetry events from OTT streaming clients across multiple AWS regions.

The design draws on my time at LG Electronics on the webOS Smart TV platform (100M+ devices during my tenure), where I integrated 20+ OTT partner services and ran the LG Content Store across 53 countries.

## What this repository is

A portfolio project organized around architectural decisions rather than a single polished application. The value is in the documentation: the problem framing, the Architecture Decision Records (ADRs), and the trade-off analysis.

## What this repository is not

Not a production system, not a benchmark of enterprise throughput, and not a drop-in template. Code samples, when added, are development-scale illustrations of specific patterns.

## Structure

- `docs/` - problem framing, architecture overview, ADRs, and trade-off analysis
- `diagrams/` - system context, container, and deployment diagrams (planned)
- `infrastructure/terraform/` - AWS infrastructure-as-code modules (planned)
- `src/` - focused code samples for specific patterns (planned)
- `examples/` - walkthroughs tying the pieces together (planned)

## Status

Design in progress. Start here:

1. [Problem Space](docs/01-problem-space.md): the question the pipeline answers, why a generic event pipeline falls short on a Smart TV platform, and requirements R1 to R8
2. [ADR-002: Consent-Enforcing Regional Ingest](docs/03-decision-records/ADR-002-event-ingest-pattern.md): the first accepted decision
3. [Lessons from the Field](docs/05-lessons-from-field.md): the operating experience behind the requirements

Planned next: ADR-001 (multi-region strategy), ADR-003 (partner integration pattern), the architecture overview, and diagrams.

## About

Written by Deokhwa Jeong.

- LG Electronics, 2011 to 2021: Software Engineer (embedded, Smart TV) 2011 to 2013, then Senior Technical Program Manager for the webOS Smart TV platform 2013 to 2021
- Integrated 20+ OTT partner services; ran the LG Content Store across 53 countries
- M.S. Software Management, Carnegie Mellon University (expected December 2027)

## License

MIT. See LICENSE.
