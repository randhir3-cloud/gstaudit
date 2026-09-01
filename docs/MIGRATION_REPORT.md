# Migration Report — Design System (v0.4.0)

**Date:** 2026-07-09  
**Milestone:** Comparison + Investigation feature migration **complete**

---

## Summary

GAIS v0.4.0 migrates Comparison and Investigation to the Dashboard v0.3.1 architecture. Both pages now use feature modules, shared layout/cards/badges/tables, `Icons.*`, `theme.*`, and the services layer. **Report migration is deferred** until this phase is verified.

---

## Before / After Metrics

| Metric | v0.3.1 (before) | v0.4.0 (now) |
|--------|-----------------|--------------|
| Comparison page hardcoded zinc | 18 | **0** |
| Investigation page hardcoded zinc | 27 | **0** |
| Comparison `lucide-react` imports | 3 | **0** |
| Investigation `lucide-react` imports | 1 | **0** |
| Pages calling API directly | 2 | **0** |
| Feature modules (Comparison, Investigation) | 0 | **2** |
| Shared DataTable on Investigation | ✅ (wrapper) | ✅ (`CaseTable`) |
| Playwright E2E | 22/22 | **32/32** |

### Cumulative (Dashboard + Layout + Comparison + Investigation)

| Metric | v0.2 baseline | v0.4.0 |
|--------|---------------|--------|
| Dashboard + Layout zinc | ~182 | **0** |
| Comparison + Investigation zinc | ~45 | **0** |
| Direct lucide in migrated pages | 6+ | **0** |
| Inline investigation badges | 1 (`PRIORITY_COLORS`) | **0** |

---

## Bundle Size

| Build | JS (gzip) | CSS (gzip) |
|-------|-----------|------------|
| v0.3.1 | 136.55 kB | 7.53 kB |
| v0.4.0 | 137.90 kB | 7.50 kB |

Minimal JS increase (+1.35 kB gzip) from feature module composition; no new dependencies.

---

## New in v0.4.0

### Feature modules

```
features/comparison/
  pages/ComparisonPage.jsx
  hooks/useComparisonPage.js → comparisonService
  components/ComparisonToolbar, ComparisonSummary, ComparisonDetail, …

features/investigation/
  pages/InvestigationPage.jsx
  hooks/useInvestigationPage.js → investigationService
  components/CaseSidebar, CaseFilters, CaseActions, CaseTable, CaseDetails, …
```

### Service layer

- `useComparisonPage` → `comparisonService` (no direct `api/comparison`)
- `useInvestigationPage` → `investigationService` (no direct `api/investigation`)

### Shared primitives reused

- `ComparisonLayout`, `InvestigationLayout`, `PageHeader`, `Toolbar`
- `ContentCard`, `MetricCard`, `ComparisonBadge`, `PriorityBadge`, `RiskBadge`
- `DataTable` + `columns/investigationColumns.js`
- `Icons.Loading` (replaces lucide in filters)
- `theme.forms.input`, `theme.sidebar.itemActive`, `theme.card.dashed`

### Legacy compatibility

- `pages/ComparisonScreen.jsx` → re-exports `ComparisonPage`
- `pages/InvestigationPage.jsx` → re-exports feature page
- `components/investigation/*` → thin re-exports for `WorkbookViewer` and external imports

---

## Component Usage (Comparison + Investigation)

```
ComparisonLayout / InvestigationLayout
  → PageHeader / Toolbar
  → ContentCard | MetricCard
  → ComparisonBadge | PriorityBadge | RiskBadge | StatusBadge
  → DataTable (CaseTable / workbook detail)
  → Icons.* (zero lucide)
  → theme.* (zero zinc)
```

---

## Technical Debt (remaining)

| Item | Severity |
|------|----------|
| Audit Report page unmigrated | Expected (next phase) |
| MergePage (~90 zinc usages) | High |
| E-way module | Medium |
| Full shadcn catalog (Tabs, Select, Toast) | Medium |
| Virtual DataTable | High (ADR-013) |
| `@/` Vite aliases | Low |

---

## Test Results

| Suite | Result |
|-------|--------|
| Backend pytest | 67 passed |
| Frontend Vitest | 2 passed |
| Playwright E2E (desktop) | **28 passed** |
| Playwright viewport (tablet + mobile) | **4 passed** |
| **Total Playwright** | **32/32** |
| Production build | Success |

Evidence screenshots regenerated via `saveEvidence()` in comparison, investigation, and intelligence specs.

---

## Next Phase (v0.5)

1. Migrate `AuditReportPreview.jsx` using Dashboard template
2. Migrate `MergePage` and E-way module
3. Add shadcn Tabs, Select, Toast
4. Dark-mode viewport tests for Comparison + Investigation

---

## Related

- [FEATURE_MODULES.md](./FEATURE_MODULES.md)
- [REFACTOR_AUDIT.md](./REFACTOR_AUDIT.md)
- [COMPONENT_LIBRARY.md](./COMPONENT_LIBRARY.md)
- [PRE_V1_ROADMAP.md](./PRE_V1_ROADMAP.md)
