# Roadmap

Planned evolution of GAIS toward **v1.0 production release**.

> **Canonical pre-v1.0 plan:** [PRE_V1_ROADMAP.md](./PRE_V1_ROADMAP.md) — design system, plugins, service layer, persistence.

## v0.1 — Foundation Release

**Status:** ✅ Released (2026-07-09)

- GSTR merge, EWB classification, dashboard, comparison, investigation, intelligence, reports
- Playwright E2E + Docker Compose

## v0.2 — Architecture Foundation

**Status:** ✅ Released (2026-07-09)

- Documentation suite + ADRs 001–006
- Theme tokens, shadcn foundation, shared DataTable
- Hooks, utils, API client, column/service scaffolding

## v0.3 — Complete Design System

**Target:** Next sprint

- [ ] Finish theme modules (`forms`, `charts`, `sidebar`, `layout`, `animations`)
- [ ] Migrate all pages off hardcoded Tailwind (see [DESIGN_SYSTEM.md](./DESIGN_SYSTEM.md))
- [ ] Central icon registry (`src/icons/`)
- [ ] Semantic `theme.card.background` usage everywhere

## v0.4 — UI Shell & shadcn Wrappers

- [ ] Full `components/ui/` wrapper set (Input, Tabs, Toast, Form, …)
- [ ] Layout components (`PageLayout`, `Toolbar`, `FilterToolbar`, grids)
- [ ] Vite `@/` path aliases

## v0.5 — Cards, Badges & Tables

- [ ] Common cards (KpiCard, DatasetCard, RiskCard, …)
- [ ] Unified badges (GSTBadge, ComparisonBadge, …)
- [ ] Migrate all tables to DataTable + `columns/`
- [ ] Export + column resize on DataTable

## v0.6 — Forms & Motion

- [ ] Form system (GSTINInput, MonthPicker, …)
- [ ] Animation tokens applied consistently

## v0.7 — Service Layer & Features

- [ ] Pages → hooks → services → api (no direct API in pages)
- [ ] Feature module migration (`features/dashboard/` first)

## v0.8 — Plugin Architecture

- [ ] Plugin manifest + registry (backend + frontend)
- [ ] GSTR-1 and EWB as first-class plugins
- [ ] Register GSTR-2A vs EWB Inward comparator

## v0.9 — Persistence & Backend Layering

**Status:** 🔄 In progress (v0.5 repository layer complete)

- [x] Repository interfaces + memory/postgres implementations (ADR-007)
- [x] Alembic initial migration + indexes
- [x] `DATABASE_PROVIDER` configuration switch
- [ ] Authentication (ADR-008)
- [ ] Controllers layer; background jobs (ADR-011)
- [ ] Virtual DataTable for 500k rows (ADR-013)

## v1.0 — Production Release

- [ ] All PRE_V1_ROADMAP definition-of-done items
- [ ] Security hardening, audit logs, multi-instance
- [ ] Full ADR set 001–015 accepted
- [ ] Performance benchmarks in CI

## Future (post-v1.0)

- GSTR-3B reconciliation, purchase register, TDS
- Optional AI narrative (ADR-014)
- Multi-dealer portfolio, role-based access
- Analytics / ML risk baselines

## Technical Debt

| Item | Priority | Phase |
|------|----------|-------|
| Inline Tailwind in dashboard components | High | v0.3 |
| Pages calling API directly | Medium | v0.7 |
| In-memory backend stores | High | v0.9 |
| Duplicate badge styling | Medium | v0.5 |
| No virtual scroll | High | v0.9 |

## Related

- [PRE_V1_ROADMAP.md](./PRE_V1_ROADMAP.md)
- [DESIGN_SYSTEM.md](./DESIGN_SYSTEM.md)
- [CHANGELOG.md](./CHANGELOG.md)
- [DECISIONS/](./DECISIONS/)
