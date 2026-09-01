# Pre-v1.0 Roadmap

This document defines what GAIS must build **after v0.2 foundation** and **before v1.0 production release**. It supersedes scattered UI notes and aligns engineering priorities with long-term maintainability.

**Principle:** No new GST product features until each phase's infrastructure is complete and migrated.

---

## Phase Overview

| Phase | Focus | Target |
|-------|-------|--------|
| **A** | Complete design system | v0.3 |
| **B** | shadcn wrappers + layout | v0.4 |
| **C** | Cards, badges, tables, columns | v0.5 |
| **D** | Forms, icons, animations | v0.6 |
| **E** | Service layer + feature modules | v0.7 |
| **F** | Plugin architecture | v0.8 |
| **G** | Backend layering + persistence | v0.9 |
| **H** | Hardening → v1.0 | v1.0 |

See [ROADMAP.md](./ROADMAP.md) for release versioning and [DECISIONS/](./DECISIONS/) for ADRs.

---

## 1. Design System (Highest Priority)

**Current:** `frontend/src/theme/` has partial tokens (colors, spacing, typography, risk, status, tables, cards).

**Target:** Every visual decision flows from one module. **No component may hardcode** `bg-zinc-900`, `text-red-500`, `rounded-xl`, or `p-4`.

### Token modules (`src/theme/`)

| File | Purpose |
|------|---------|
| `colors.js` | Semantic palette (primary, danger, muted, border, …) |
| `typography.js` | Font families, sizes, weights |
| `spacing.js` | Scale + page/section presets |
| `radius.js` | Radius scale + component presets |
| `shadows.js` | Elevation tokens |
| `animations.js` | fade, slide, modal, drawer, toast, spinner |
| `breakpoints.js` | Responsive breakpoints |
| `zindex.js` | Layer stack |
| `icons.js` | Icon size tokens (not icon imports) |
| `tables.js` | Table shell, header, row, cell |
| `forms.js` | Input, label, error, field spacing |
| `charts.js` | Chart colors, grid, axis (future dashboards) |
| `cards.js` | Card backgrounds, padding, borders |
| `sidebar.js` | Nav width, item states |
| `layout.js` | Page max-width, grid gaps, toolbar height |
| `risk.js` | LOW / MEDIUM / HIGH / CRITICAL |
| `status.js` | Workflow states (draft, running, failed, …) |
| `theme.js` | **Single export** — `theme.card.background`, `theme.spacing.md`, `theme.status.error` |

### Usage pattern

```jsx
import theme from '@/theme/theme';
import { cn } from '@/lib/utils';

<div className={cn(theme.card.shell, theme.spacing.md)} />
<span className={theme.status.error}>Failed</span>
```

### Migration rule

When touching any component, replace inline Tailwind with theme tokens. Track progress in [DESIGN_SYSTEM.md](./DESIGN_SYSTEM.md).

**ADR:** [ADR-002-Theme.md](./DECISIONS/ADR-002-Theme.md)

---

## 2. shadcn Wrappers

**Rule:** Pages and features **never** import `@radix-ui/*` or raw shadcn paths. Only `components/ui/*` wrappers.

### Required wrappers (`components/ui/`)

| Component | Status (v0.2) |
|-----------|---------------|
| Button, Card, Badge, Dialog | Done |
| Input, Table, Tabs, Accordion | Planned |
| Dropdown, Tooltip, Popover | Planned |
| Calendar, Toast, Alert | Planned |
| Checkbox, Switch, Form | Planned |
| ScrollArea, Separator | Planned |
| DataTable (ui layer over common) | Planned |

If shadcn changes upstream, **only wrappers change**.

**ADR:** [ADR-006-ShadcnAdoption.md](./DECISIONS/ADR-006-ShadcnAdoption.md)

---

## 3. Common Layout Components

Every page today builds its own shell. Standardize on:

| Component | Purpose |
|-----------|---------|
| `PageLayout` | App shell wrapper (nav + content area) |
| `PageHeader` | Title, description, primary actions |
| `SectionHeader` | Subsection title + optional actions |
| `Toolbar` | Action bar (export, run, refresh) |
| `FilterToolbar` | Search + filters row |
| `PageFooter` | Secondary actions / metadata |
| `DashboardGrid` | Dashboard-specific grid |
| `ResponsiveGrid` | Generic responsive columns |
| `StatsGrid` | KPI row layout |
| `ContentCard` | Bordered content panel |
| `Panel` | Side / detail panel |
| `SidebarSection` | Grouped nav items |

**Location:** `frontend/src/components/layout/`

After migration, Dashboard, Comparison, Investigation, and Reports share identical page rhythm.

---

## 4. Common Cards

GST Audit repeats the same card patterns. Build once in `components/cards/`:

- `KpiCard`, `StatisticCard`, `MetricCard`
- `AuditCard`, `WorkbookCard`, `DatasetCard`
- `ProgressCard`, `HealthCard`, `SummaryCard`
- `RiskCard`, `AlertCard`, `TimelineCard`

Each card composes `theme.card.*` + optional `components/ui/Card`.

---

## 5. Common Badges

**Remove** all inline badge styling. Single source in `components/badges/`:

- `RiskBadge`, `StatusBadge` (partially done in `common/`)
- `AuditBadge`, `DatasetBadge`, `ComparisonBadge`
- `PriorityBadge`, `GSTBadge`

No page styles badges independently.

---

## 6. Unified DataTable

**Biggest UX/consistency win.** One implementation in `components/common/DataTable.jsx`:

| Feature | v0.2 | v1.0 target |
|---------|------|-------------|
| Sorting | ✓ | ✓ |
| Search / filter | ✓ | ✓ |
| Pagination | ✓ | ✓ |
| Sticky header | ✓ | ✓ |
| Selection | ✓ | ✓ |
| Custom renderers | ✓ | ✓ |
| Export | — | ✓ |
| Column resize | — | ✓ |
| Sticky columns | — | ✓ |
| Virtual scroll (500k+ rows) | — | ✓ |
| Row actions | — | ✓ |

### Consumers (migrate all)

- Upload history
- Comparison details
- Investigation workbench
- Workbook viewer
- Report preview tables

**ADR:** [ADR-005-DataTable.md](./DECISIONS/ADR-005-DataTable.md), [ADR-013-VirtualDataTable.md](./DECISIONS/ADR-013-VirtualDataTable.md)

---

## 7. Column Definitions

**Never** define table columns inside pages.

```
frontend/src/columns/
  comparisonColumns.js
  investigationColumns.js
  reportColumns.js
  uploadColumns.js
  dealerColumns.js
```

Pages import column configs; `DataTable` renders them.

---

## 8. Form System

Replace ad-hoc form markup with `components/forms/`:

| Component | Purpose |
|-----------|---------|
| `FormField` | Label + control + error |
| `GSTINInput` | Validated GSTIN |
| `InvoiceInput` | Normalized invoice number |
| `CurrencyInput` | INR formatting |
| `DateInput` | Audit date fields |
| `MonthPicker` | FY month selection |
| `DealerSelector` | Dealer / GSTIN picker |

Built on `theme/forms.js` + shadcn `Form`, `Input`, `Label`.

---

## 9. Central Icons

**Don't** scatter `lucide-react` imports.

```
frontend/src/icons/index.js
```

```js
import Icons from '@/icons';
<Icons.Calendar className={Icons.size.sm} />
```

Map semantic names (`Icons.Report`, `Icons.Warning`) to lucide components. Theme provides sizes only.

---

## 10. Animation System

Consolidate in `theme/animations.js`:

- `fade`, `slide`, `modal`, `tooltip`, `drawer`, `toast`, `loading`, `spinner`

Replace scattered `animate-*` and inline keyframes. Pair with CSS variables for duration/easing.

---

## 11. Service Layer

Frontend call stack:

```
pages → hooks → services → api → backend
```

**Not:** pages → api directly.

```
frontend/src/services/
  dashboardService.js
  comparisonService.js
  investigationService.js
  intelligenceService.js
  reportService.js
  mergeService.js
  ewayService.js
```

Hooks orchestrate UI state; services encapsulate business logic and API composition.

---

## 12. Feature Modules

Organize by domain, not file type:

```
frontend/src/features/
  dashboard/
  comparison/
  investigation/
  audit/
  reports/
  dealer/
  merge/
  eway/
  shared/
```

Each feature owns its pages, hooks, components, and column defs. `src/pages/` becomes thin route re-exports.

---

## 13. Plugin Architecture

Extend the comparison **registry pattern** platform-wide:

```
plugins/
  gstr1/
  gstr2a/
  gstr3b/
  eway/
  purchase/
  sales/
  tds/
  refund/
  analytics/
```

Each plugin registers:

- Routes and pages
- Comparators and validators
- Report sections
- Dashboard cards
- Sidebar items

Adding GSTR-3B reconciliation becomes **configuration**, not a rewrite.

**ADR:** [ADR-010-PluginArchitecture.md](./DECISIONS/ADR-010-PluginArchitecture.md)

---

## 14. Backend Layering

Evolve from:

```
routes → services → models (in-memory)
```

To:

```
routes → controllers → services → repositories → database
```

Prepares PostgreSQL migration documented in [BACKEND_ARCHITECTURE.md](./BACKEND_ARCHITECTURE.md).

**ADR:** [ADR-007-DatabaseSelection.md](./DECISIONS/ADR-007-DatabaseSelection.md)

---

## 15. Architecture Decision Records

Existing ADRs (001–006). Add before v1.0:

| ADR | Topic |
|-----|-------|
| ADR-007 | Database selection |
| ADR-008 | Authentication strategy |
| ADR-009 | Caching strategy |
| ADR-010 | Plugin architecture |
| ADR-011 | Background job processing |
| ADR-012 | Feature module structure |
| ADR-013 | Virtual DataTable |
| ADR-014 | AI integration |
| ADR-015 | Report generation pipeline |

---

## Definition of Done (v1.0)

- [ ] Zero hardcoded colors/spacing/radius in feature components
- [ ] All pages use layout + card + badge primitives
- [ ] All tables use `DataTable` + column defs
- [ ] All API access via services
- [ ] Feature module structure in place
- [ ] At least 2 GST plugins registered (GSTR-1, EWB)
- [ ] PostgreSQL persistence + auth
- [ ] Virtual scroll validated at 500k rows
- [ ] Full Playwright suite + evidence
- [ ] All ADRs 001–015 accepted or superseded

---

## Related

- [DESIGN_SYSTEM.md](./DESIGN_SYSTEM.md) — token catalog and migration checklist
- [PROJECT_RULES.md](./PROJECT_RULES.md) — coding standards
- [COMPONENT_LIBRARY.md](./COMPONENT_LIBRARY.md) — component inventory
- [ROADMAP.md](./ROADMAP.md) — version timeline
