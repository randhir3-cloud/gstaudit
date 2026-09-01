# Feature Modules

GAIS frontend organization for v0.4+. **Dashboard v0.3.1** is the UI reference; Comparison and Investigation follow the same patterns.

---

## Architecture

```
Page (route re-export)
  └── features/{name}/pages/*Page.jsx
        ├── hooks/use*Page.js     → services/*Service.js → api/*
        └── components/*          → components/common|layout|cards|badges
```

**Rules**

- No page calls `api/*` directly — use `services/` via feature hooks.
- No inline column definitions — use `columns/*.js` with `DataTable`.
- No direct `lucide-react` — use `Icons.*`.
- No hardcoded zinc/spacing — use `theme.*`.
- Badges: `AuditBadge`, `StatusBadge`, `ComparisonBadge`, `PriorityBadge`, `DatasetBadge`, `RiskBadge` only.
- Cards: `ContentCard`, `MetricCard`, `SummaryCard`, `ProgressCard`, `RiskCard`, `DatasetCard` only.

---

## Module Status

| Module | Path | Status | Reference |
|--------|------|--------|-----------|
| Dashboard | `pages/Dashboard.jsx` + `components/dashboard/` | ✅ v0.3.1 complete | Canonical UI |
| Comparison | `features/comparison/` | ✅ v0.4.0 migrated | Dashboard patterns |
| Investigation | `features/investigation/` | ✅ v0.4.0 migrated | Dashboard patterns |
| Reports | `pages/AuditReportPreview.jsx` | ⏳ Not migrated | Blocked until Comparison + Investigation done |
| Merge | `pages/MergePage.jsx` | ⏳ Legacy | High debt |
| E-way | `components/eway/` | ⏳ Legacy | Medium debt |

---

## Comparison (`features/comparison/`)

```
comparison/
  pages/ComparisonPage.jsx
  hooks/useComparisonPage.js
  components/
    ComparisonToolbar.jsx    PageHeader + Toolbar
    ComparisonActions.jsx    Run comparison button
    ComparisonSummary.jsx    MetricCard grid + status + detail links
    ComparisonDetail.jsx     Workbook filter links
    ComparisonObservations.jsx
  constants.js
  index.js
```

**Route:** `pages/ComparisonScreen.jsx` → re-exports `ComparisonPage`.

**Service chain:** `useComparisonPage` → `comparisonService` → `api/comparison`.

**Shared primitives:** `ComparisonLayout`, `ContentCard`, `MetricCard`, `ComparisonBadge`, `RiskBadge`, `ResponsiveGrid`, `Icons.*`, `theme.*`.

---

## Investigation (`features/investigation/`)

```
investigation/
  pages/InvestigationPage.jsx
  hooks/useInvestigationPage.js
  components/
    InvestigationToolbar.jsx
    CaseSidebar.jsx          Category filter sidebar
    CaseFilters.jsx          Status / GSTIN / month filters
    CaseActions.jsx          Bulk verify / pending
    CaseTable.jsx            DataTable + investigationColumns
    CaseDetails.jsx          CaseSummary + detail panel + save form
  constants.js
  index.js
```

**Route:** `pages/InvestigationPage.jsx` → re-exports feature page.

**Legacy re-exports:** `components/investigation/ComparisonRecordsTable.jsx` → `CaseTable`.

**Service chain:** `useInvestigationPage` → `investigationService` → `api/investigation`.

**Layout:** `InvestigationLayout` (three-panel grid: sidebar | table | details).

**E2E test IDs preserved:** `investigation-categories`, `investigation-grid`, `investigation-row-0`, `investigation-details`, `case-priority-badge`, `bulk-verify`, etc.

---

## Shared Layers (not feature-owned)

| Layer | Location |
|-------|----------|
| Layout | `components/layout/` |
| Cards | `components/cards/` |
| Badges | `components/badges/` + `common/StatusBadge`, `common/RiskBadge` |
| DataTable | `components/common/DataTable.jsx` |
| Columns | `columns/` |
| Theme | `theme/` |
| Icons | `icons/index.js` |
| Services | `services/` |

---

## Adding a Feature Module

1. Create `features/{name}/pages`, `components`, `hooks`.
2. Add `{name}Service.js` wrapping API calls.
3. Re-export from `pages/{Name}.jsx` for routes.
4. Match Dashboard layout: `PageHeader`, `SectionContainer`, shared cards/badges.
5. Add Playwright coverage + `saveEvidence` screenshots.
6. Document in [COMPONENT_LIBRARY.md](./COMPONENT_LIBRARY.md) and this file.

---

## Related

- [COMPONENT_LIBRARY.md](./COMPONENT_LIBRARY.md)
- [MIGRATION_REPORT.md](./MIGRATION_REPORT.md)
- [FRONTEND_ARCHITECTURE.md](./FRONTEND_ARCHITECTURE.md)
- [DECISIONS/ADR-012-FeatureModules.md](./DECISIONS/ADR-012-FeatureModules.md)
