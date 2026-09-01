# Frontend Refactor Audit

**Date:** 2026-07-09  
**Version:** v0.3.1 — Dashboard + Layout migration **complete**  
**Scope:** `frontend/src/components/dashboard/`, `Layout.jsx`, `pages/Dashboard.jsx`

---

## Executive Summary

The **Dashboard and app Layout are now the canonical reference implementation** for GAIS. All 22 dashboard components use theme tokens, shared layout/cards/badges, `Icons.*`, and `DataTable` for tabular data (except the FY calendar matrix grid — see below).

**Comparison, Investigation, Merge, E-way, and Report pages are intentionally not migrated** — they copy Dashboard patterns in the next phase.

---

## Dashboard Migration Status: ✅ COMPLETE

| Criterion | Status |
|-----------|--------|
| Zero `bg-zinc-*` / hardcoded palette in `components/dashboard/` | ✅ |
| Zero direct `lucide-react` in dashboard | ✅ |
| All cards use `ContentCard` / `MetricCard` / `SummaryCard` / `ProgressCard` / `DatasetCard` / `RiskCard` | ✅ |
| All badges use shared badge components | ✅ |
| Upload History + Workbook Summary use `DataTable` | ✅ |
| FY Calendar uses `theme.calendar.*` tokens | ✅ |
| `Layout.jsx` uses `SidebarSection`, `theme.*`, `Icons.*` | ✅ |
| Playwright dashboard tests | ✅ 8/8 |

### FY Calendar table exception

`FinancialYearCalendar.jsx` retains a **matrix `<table>`** (months × datasets) because `DataTable` is row-oriented, not a pivot grid. Styling is fully tokenized via `theme.calendar.*` and `theme.table.*`.

---

## Component Inventory (`components/dashboard/`)

| Component | Cards | Badges | Theme | Icons | Table |
|-----------|-------|--------|-------|-------|-------|
| AuditHeader | ContentCard | AuditBadge | ✅ | ✅ | — |
| TopSummaryPanel | SummaryCard | — | ✅ | — | — |
| DatasetCard (was DatasetStatusCard) | DatasetCard | DatasetBadge | ✅ | ✅ | — |
| FinancialYearCalendar | — | — | ✅ | — | matrix* |
| MonthCellModal | theme.card | — | ✅ | ✅ | — |
| DuplicateMonthPanel | ContentCard | — | ✅ | — | — |
| ReadinessBar | ContentCard | — | ✅ | ✅ | — |
| ComparisonStatusCards | ContentCard | ComparisonBadge | ✅ | — | — |
| DuplicateDetectionPanel | ContentCard | — | ✅ | — | — |
| DiscrepancySummary | ContentCard | — | ✅ | — | — |
| SummaryStatistics | ContentCard | — | ✅ | — | — |
| UploadHealthCard | theme.card | — | ✅ | ✅ | — |
| UploadHistoryTable | ContentCard | — | ✅ | — | DataTable |
| WorkbookSummarySection | ContentCard | — | ✅ | — | DataTable |
| MergeSummarySection | ContentCard | — | ✅ | — | — |
| CaseTrackingPanel | ContentCard | — | ✅ | — | — |
| AuditIntelligencePanel | ContentCard | PriorityBadge | ✅ | ✅ | — |
| StatusTooltip | Radix Tooltip | — | ✅ | — | — |
| MonthCoverageGrid | ContentCard | StatusBadge | ✅ | — | — |

---

## Layout Migration Status: ✅ COMPLETE

| Before | After |
|--------|-------|
| Inline zinc header/footer/nav | `theme.layout.pageShell`, `theme.sidebar.*` |
| Direct lucide imports | `Icons.Dashboard`, `Icons.Compare`, etc. |
| Inline nav styling | `SidebarSection` + `AppBrand` + `ThemeToggleButton` |

---

## Remaining Work (post v0.3.1)

| Area | Files | Priority |
|------|-------|----------|
| Comparison page | `ComparisonScreen.jsx` | P1 |
| Investigation page | `InvestigationPage.jsx`, `InvestigationDetailsPanel.jsx` | P1 |
| Report page | `AuditReportPreview.jsx` | P2 |
| Merge module | `MergePage.jsx`, `merge/*`, `eway/*` | P2 |
| Workbook viewer | `WorkbookViewer.jsx` | P2 |
| Dealer header | `DealerHeader.jsx` | P2 |
| shadcn wrappers (Tabs, Toast, Form, …) | `components/ui/` | P3 |
| Virtual DataTable | ADR-013 | P3 |

---

## Metrics (v0.3 → v0.3.1)

| Metric | v0.3 | v0.3.1 |
|--------|------|--------|
| Dashboard zinc usages | ~155 | **0** |
| Layout zinc usages | 27 | **0** |
| Dashboard lucide imports | 2 | **0** |
| Layout lucide imports | 1 | **0** |
| Dashboard inline tables | 2 | **0** (+ calendar matrix) |
| Playwright E2E | 22/22 | **22/22** |

---

## Related

- [MIGRATION_REPORT.md](./MIGRATION_REPORT.md)
- [COMPONENT_LIBRARY.md](./COMPONENT_LIBRARY.md)
- [DESIGN_SYSTEM.md](./DESIGN_SYSTEM.md)
