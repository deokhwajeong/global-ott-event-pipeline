# Global OTT Event Pipeline

Reference architecture for ingesting and processing telemetry events from OTT streaming clients across multiple AWS regions.

This repository documents the architectural decisions, trade-offs, and implementation patterns I would apply when designing a global OTT event pipeline today, drawing on a decade of experience operating a Smart TV streaming platform across 50+ countries.

## What this repository is

A work-in-progress portfolio project. It is organized around architectural decisions rather than a single polished application. The value here is in the documentation: the problem framing, the Architecture Decision Records, and the trade-off analysis.

## What this repository is not

Not a production system, not a benchmark of enterprise throughput, and not a drop-in template. Code samples are development-scale illustrations of specific patterns.

## Structure

- `docs/` - architectural documentation, ADRs, and trade-off analysis
- `diagrams/` - system context, container, and deployment diagrams
- `infrastructure/terraform/` - infrastructure-as-code modules for AWS
- `src/` - focused code samples demonstrating specific patterns
- `examples/` - walkthroughs tying the pieces together

## Current status

Work in progress. See `docs/02-architecture-overview.md` for the current scope of what is documented and what is still pending.

## About

Written by Deokhwa (Deka) Jeong as part of a Solutions Architect portfolio. Prior background: 10+ years at LG Electronics on a global Smart TV OTT platform spanning 20+ partner integrations and 50+ markets.

## License

MIT. See LICENSE.
