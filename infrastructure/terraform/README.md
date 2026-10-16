# Terraform Infrastructure

Planned, not built.

The reference implementation in `src/` runs in memory and needs no cloud resources. When modules are added here, they will follow [ADR-001](../../docs/03-decision-records/ADR-001-multi-region-strategy.md): one set of modules instantiated once per regional cell (EU, US, APAC), plus a small global control plane, with development-scale defaults. They will illustrate the layout, not serve as a production deployment.
