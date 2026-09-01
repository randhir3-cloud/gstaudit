# Component Library

Catalog of reusable GAIS frontend components. **v0.4:** Comparison and Investigation migrated to feature modules — see [FEATURE_MODULES.md](./FEATURE_MODULES.md) and [MIGRATION_REPORT.md](./MIGRATION_REPORT.md).

---

## Shared Primitives (`components/common/`)

| Component | Purpose |
|-----------|---------|
| `PageContainer` | Max-width page wrapper |
| `PageHeader` | Title, description, actions |
| `SectionHeader` | Subsection title |
| `LoadingState` | Spinner + message |
| `ErrorState` | Alert panel |
| `EmptyState` | No-data placeholder |
| `SearchBar` | Filter input + record count |
| `DataTable` | Sort, search, pagination, selection |
| `StatusBadge` | Workflow status pill |
| `RiskBadge` | LOW/MEDIUM/HIGH/CRITICAL |

## Layout (`components/layout/`)

| Component | Purpose |
|-----------|---------|
| `PageLayout` | Standard page shell |
| `DashboardLayout` | Dashboard spacing |
| `ComparisonLayout` | Comparison page shell |
| `InvestigationLayout` | Three-panel grid |
| `ReportLayout` | Report preview shell |
| `SectionContainer` | Section with optional title |
| `ResponsiveGrid` | `dashboard` / `stats` / `two` column presets |
| `Toolbar` | Action bar |

## Cards (`components/cards/`)

| Component | Purpose |
|-----------|---------|
| `ContentCard` | Themed card with optional header |
| `SummaryCard` | KPI row (used by TopSummaryPanel) |
| `MetricCard` | Label + value stat |
| `KpiCard` | Large metric variant |
| `StatsCard` | Metric with icon |
| `ProgressCard` | Progress bar |
| `HealthCard` | Score + checklist |
| `DatasetCard` | Dataset status (replaces DatasetStatusCard) |

## Badges (`components/badges/`)

| Component | Purpose |
|-----------|---------|
| `AuditBadge` | Audit workflow status |
| `DatasetBadge` | Dataset upload status |
| `ComparisonBadge` | Comparison pair status |
| `PriorityBadge` | Investigation priority / risk |

## shadcn Wrappers (`components/ui/`)

| Component | Status |
|-----------|--------|
| `Button`, `Card`, `Badge`, `Dialog` | ✅ |
| `Input`, `Textarea`, `Label` | ✅ |
| `Tooltip`, `Separator` | ✅ |
| Tabs, Select, Toast, Form, … | Planned |

## Icons (`src/icons/index.js`)

Use `Icons.Calendar`, `Icons.Upload`, etc. — never import `lucide-react` in feature code.

---

## Layout & Shared (legacy)

### Layout

**File:** `Layout.jsx`

App shell with header, navigation, theme toggle, footer, and `<Outlet />` for pages.

| Prop | Type | Description |
|------|------|-------------|
| `theme` | `'dark'` \| `'light'` | Current theme |
| `onToggleTheme` | `() => void` | Toggle handler |

Nav items: Dashboard, Merge, Workbook Viewer, Comparison, Investigation, Audit Report.

### DealerHeader

**File:** `DealerHeader.jsx`

Displays dealer GSTIN, legal name, financial year, and current dataset. Reads from `useDealer()` and/or `useAuditSession()`.

**Test:** `DealerHeader.test.jsx` (Vitest)

### StatusTooltip

**File:** `dashboard/StatusTooltip.jsx`

CSS hover tooltip (no Radix). Wraps children with optional title + detail lines.

| Prop | Type |
|------|------|
| `children` | ReactNode |
| `title` | string |
| `details` | string[] |

---

## Dashboard Components

Located in `components/dashboard/`. Composed by `pages/Dashboard.jsx`.

| Component | Purpose | Key testids |
|-----------|---------|-------------|
| `AuditHeader.jsx` | Dealer + audit status banner | — |
| `TopSummaryPanel.jsx` | Files/rows/duplicate summary | — |
| `DatasetStatusCard.jsx` | Per-dataset upload stats | `dataset-card-{key}` — **use `DatasetCard`** |
| `FinancialYearCalendar.jsx` | 12-month coverage grid | month cells |
| `MonthCellModal.jsx` | Month detail popup | — |
| `MonthCoverageGrid.jsx` | Alternate month grid layout | — |
| `DuplicateDetectionPanel.jsx` | Duplicate statistics | — |
| `DuplicateMonthPanel.jsx` | Duplicate month resolution UI | `duplicate-panel` |
| `UploadHistoryTable.jsx` | Chronological upload log | — |
| `UploadHealthCard.jsx` | Upload quality checks | — |
| `SummaryStatistics.jsx` | Aggregate numeric stats | — |
| `WorkbookSummarySection.jsx` | Merged workbook metadata | — |
| `MergeSummarySection.jsx` | Post-merge row/sheet counts | — |
| `DiscrepancySummary.jsx` | Discrepancy count chips | — |
| `ComparisonStatusCards.jsx` | Comparison pair status | `comparison-status`, `comparison-{id}` |
| `ReadinessBar.jsx` | Audit readiness progress | `audit-not-ready` |
| `AuditIntelligencePanel.jsx` | Intelligence cards + patterns | intelligence testids |
| `CaseTrackingPanel.jsx` | Investigation case counts | case tracking testids |

### ComparisonStatusCards

Exports `FILTER_MAP` — maps dashboard discrepancy keys to comparison result types for deep links.

---

## Merge Components

| Component | File | Purpose |
|-----------|------|---------|
| `FileUploadZone.jsx` | `merge/FileUploadZone.jsx` | Drag-and-drop + file picker |
| `FileList.jsx` | `merge/FileList.jsx` | Staged files with remove action |

---

## E-Way Bill Components

| Component | Purpose |
|-----------|---------|
| `EwayBillSection.jsx` | Tab container for outward/inward |
| `EwayWorkflowPanel.jsx` | Full upload → classify → merge flow |
| `EwaySummaryCard.jsx` | Post-merge summary card |
| `EwayValidationTable.jsx` | Per-file classification results |
| `WrongUploadDialog.jsx` | Direction mismatch dialog + move action |
| `DealerGstinModal.jsx` | Manual GSTIN entry when unknown |
| `WorkbookPreviewModal.jsx` | Preview merged EWB blob |

State: `EwayContext` / `useEwayWorkflow(direction)`.

---

## Investigation (`features/investigation/`)

| Component | Purpose | Key testids |
|-----------|---------|-------------|
| `InvestigationToolbar.jsx` | Page header | `investigation-page-header` |
| `CaseSidebar.jsx` | Category sidebar | `investigation-categories`, `category-{KEY}` |
| `CaseFilters.jsx` | Status/GSTIN/month filters | `filter-status`, `filter-gstin`, `filter-month` |
| `CaseActions.jsx` | Bulk actions | `bulk-verify`, `bulk-pending` |
| `CaseTable.jsx` | DataTable wrapper | `investigation-row-{n}` |
| `CaseDetails.jsx` | Case detail + save | `investigation-details`, `case-priority-badge`, `save-case-btn` |

Legacy paths under `components/investigation/` re-export feature components for backward compatibility.

---

## Comparison (`features/comparison/`)

| Component | Purpose | Key testids |
|-----------|---------|-------------|
| `ComparisonToolbar.jsx` | Header + run action row | `comparison-toolbar`, `run-comparison-btn` |
| `ComparisonSummary.jsx` | Pair status + metrics | `comparison-summary-panel`, `cmp-*` |
| `ComparisonDetail.jsx` | Workbook filter links | `cmp-detail-link-{TYPE}` |
| `ComparisonObservations.jsx` | Audit observations | `comparison-observations` |
| `ComparisonActions.jsx` | Run comparison button | `run-comparison-btn` |

Route entry: `pages/ComparisonScreen.jsx` → `features/comparison/pages/ComparisonPage.jsx`.

---

## Investigation Components (legacy re-exports)

| Component | Re-exports |
|-----------|------------|
| `InvestigationCategoryPanel.jsx` | `CaseSidebar` |
| `InvestigationDetailsPanel.jsx` | `CaseDetailsContent` |
| `ComparisonRecordsTable.jsx` | `CaseTable` |

Priority badges use `PriorityBadge` + `theme.risk.*` — see [THEME_GUIDE.md](./THEME_GUIDE.md).

---

## Utility Functions

Not components but used across UI:

| Module | Functions |
|--------|-----------|
| `utils/formatNumbers.js` | `formatCount`, `formatCurrency`, `formatPercent` |
| `utils/fileHelpers.js` | `base64ToBlob`, `downloadBlob` |

---

## Component Patterns

### Card container

```jsx
<ContentCard testId="my-panel">{children}</ContentCard>
```

### Loading state

```jsx
<Icons.Loading className={cn(Icons.size.sm, 'animate-spin')} aria-label="Loading" />
```

### Empty state

Use `EmptyState` with `theme.card.dashed`.

### Error banner

Use `ErrorState` or `theme.alert.error`.

---

## Planned / Not Yet Present

| Planned | Status |
|---------|--------|
| `components/ui/button.jsx` | shadcn-style — deps installed, not vendored |
| `components/ui/dialog.jsx` | Use Radix directly when needed |
| Shared `DataTable` | ✅ Used by Dashboard, Comparison detail, Investigation |

---

## Adding a New Component

1. Place in appropriate feature folder under `components/`.
2. Follow [UI_STANDARDS.md](./UI_STANDARDS.md) color and spacing rules.
3. Add `data-testid` if user-visible behavior is E2E tested.
4. Document here in the same PR.

## Related

- [FRONTEND_ARCHITECTURE.md](./FRONTEND_ARCHITECTURE.md)
- [UI_STANDARDS.md](./UI_STANDARDS.md)
- [DECISIONS/ADR-005-DataTable.md](./DECISIONS/ADR-005-DataTable.md)
- [DECISIONS/ADR-006-ShadcnAdoption.md](./DECISIONS/ADR-006-ShadcnAdoption.md)
