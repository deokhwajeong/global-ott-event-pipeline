# Global OTT Event Pipeline

Reference architecture for ingesting and processing telemetry events from OTT streaming clients across multiple AWS regions.

The design draws on my time at LG Electronics on the webOS Smart TV platform (100M+ devices during my tenure), where I integrated 20+ OTT partner services and ran the LG Content Store across 53 countries.

## What this repository is

A portfolio project organized around architectural decisions rather than a single polished application. The value is in the judgment: the problem framing, the Architecture Decision Records (ADRs), the rollout plan, and a small working implementation that proves the central decision holds up in code.

## What this repository is not

Not a production system, not a benchmark of enterprise throughput, and not a drop-in template. The code is a development-scale illustration of the ingest pattern, kept small enough to read in one sitting.

## Status

Design package complete; reference implementation of the ingest pattern working and tested in CI. Terraform and end-to-end examples are planned.

Read in this order:

1. [Problem Space](docs/01-problem-space.md): the question the pipeline answers, why a generic event pipeline falls short on a Smart TV platform, and requirements R1 to R8
2. [Architecture Overview](docs/02-architecture-overview.md): C4 context, container, and deployment diagrams, the request path, and requirement coverage
3. Decision records:
   - [ADR-001: Regional Cells with Aggregate-Only Global View](docs/03-decision-records/ADR-001-multi-region-strategy.md)
   - [ADR-002: Consent-Enforcing Regional Ingest](docs/03-decision-records/ADR-002-event-ingest-pattern.md)
   - [ADR-003: Platform-First Partner Integration with Declared Extensions](docs/03-decision-records/ADR-003-partner-integration-pattern.md)
4. [Rollout Plan](docs/04-rollout-plan.md): phases, exit criteria, risks and mitigations, and the success metrics
5. [Lessons from the Field](docs/05-lessons-from-field.md): the operating experience behind the requirements
6. [Trade-offs](docs/06-trade-offs.md): what each decision gave up, in one table
7. [Reference implementation](src/README.md): ADR-002 in plain Python, with tests named after the requirements they cover

## Structure

- `docs/` - problem framing, architecture overview, ADRs, rollout plan, field lessons, trade-offs
- `src/ott_ingest/` - reference implementation of consent-enforcing regional ingest (Python 3.12, standard library only)
- `tests/` - unit tests, one file per requirement (`test_r1_*` to `test_r8_*`) plus ADR-002 and ADR-003 rules
- `.github/workflows/ci.yml` - lint (ruff) and tests (pytest) on every push and pull request
- `diagrams/` - diagrams live inline in the architecture overview as Mermaid
- `infrastructure/terraform/` - AWS infrastructure-as-code modules (planned)
- `examples/` - end-to-end walkthroughs (planned; the requirement-named tests serve for now)

## Run it

```bash
pip install "pytest>=8" "ruff>=0.6"
ruff check . && ruff format --check .
pytest
```

## About

Written by Deokhwa Jeong.

- LG Electronics: Software Engineer, NPI & Mass Production (2011 to 2013), then Senior Technical Program Manager, Platform Integration (2013 to 2021)
- Held go / no-go certification authority for 20+ streaming partners across 100+ TV models; ran the LG Content Store across 53 countries; built the Smart TV privacy compliance program (GDPR, CCPA)
- M.S. Software Management, Carnegie Mellon University (expected December 2027)

## License

MIT. See LICENSE.
