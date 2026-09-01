# Changelog

All notable changes to GAIS (GST Audit Intelligence System) are documented here.

Format based on [Keep a Changelog](https://keepachangelog.com/). Versioning follows [Semantic Versioning](https://semver.org/).

---

## [0.1.0] — 2026-07-09 — Foundation Release

First integrated release of the GST Audit Intelligence System, combining Excel merge tooling with comparison, investigation, intelligence, and audit reporting.

### Added

#### Platform
- React 19 + Vite 8 frontend with dark/light theme toggle
- FastAPI backend with 37 HTTP endpoints (`backend/main.py`)
- Docker Compose deployment (frontend `:8081`, backend `:8001`)
- Nginx reverse proxy for `/api/` in production container

#### Data Ingestion
- GSTR-1 and GSTR-2A multi-file merge with missing-month detection (`merger.py`)
- E-Way Bill outward/inward merge with direction classification (`eway_merge_service.py`, `eway_classification_service.py`)
- Dealer metadata extraction and GSTIN consistency validation
- Wrong-upload detection with cross-direction file move UI

#### Audit Dashboard
- Financial year month coverage calendar
- Dataset status cards (GSTR-1, GSTR-2A, EWB outward/inward)
- Upload health checks and duplicate month resolution
- Audit readiness bar and comparison status cards
- Upload history table and summary statistics
- Case tracking panel for investigation workflow

#### Comparison Engine
- Pluggable comparator registry (`comparison/registry.py`)
- GSTR-1 vs EWB Outward reference comparator
- Invoice, GSTIN, date, value, and duplicate matchers
- Risk scoring engine with CRITICAL/HIGH/MEDIUM/LOW levels
- Audit observation generator for officer guidance
- Paginated discrepancy detail API

#### Investigation Workbench
- Auto-generated cases from comparison discrepancies
- Category filters, search, risk filters, pagination
- Case detail with officer remarks and status workflow
- Bulk case verification
- Intelligence enrichment on cases

#### Audit Intelligence
- Pattern detection (repeated missing invoices, GSTIN mismatches, clusters)
- Month-level timeline analysis
- Supplier and customer risk rankings
- Executive summary with heatmaps and insight cards
- Document recommendation catalog
- Case prioritization with GST provision hints

#### Audit Reporting
- Report preview API with executive summary and intelligence
- Full report export: Excel, PDF, DOCX (`audit_report_service.py`)
- Legacy dealer-only Excel/PDF export

#### State Management
- `AuditSessionContext` with localStorage persistence and debounced backend sync
- `DealerContext` for workbook metadata
- `EwayContext` for dual-direction EWB workflows

#### Testing
- 15+ pytest modules covering services, comparison, intelligence, investigation
- Playwright E2E: dashboard, comparison, investigation, intelligence, eway-classification
- Responsive viewport tests (tablet, mobile)
- Visual evidence captured in `docs/evidence/2026-07-09/`

#### Documentation
- Architecture, API reference, comparison/investigation/intelligence guides
- ADRs for key design decisions
- This changelog

### Technical Notes

- Storage: in-memory Python dicts (non-durable across restarts)
- Authentication: none (internal/trusted network assumed)
- CORS: permissive for development
- Session ID: deterministic hash from GSTIN + financial year

### Known Limitations

- GSTR-2A vs EWB Inward comparator implemented but not registered
- shadcn/ui dependencies installed; component library not fully vendored
- No persistent database or file storage on server

---

## [0.5.0] — 2026-07-09 — Repository Persistence Layer

### Added

- **Repository pattern:** interfaces + memory + PostgreSQL implementations
- **SQLAlchemy 2.x ORM** models in `backend/db/orm/models.py`
- **Alembic** initial migration (`001_initial_schema`) with indexes and foreign keys
- **Configuration:** `DATABASE_PROVIDER=memory|postgres`, `DATABASE_URL`
- **Docker Compose:** PostgreSQL 16 service
- Docs: [DATABASE.md](./DATABASE.md), [REPOSITORY_PATTERN.md](./REPOSITORY_PATTERN.md), [ENTITY_RELATIONSHIP.md](./ENTITY_RELATIONSHIP.md)
- Tests: memory repository suite (76 tests), postgres suite (marker), migration tests

### Changed

- Store modules (`audit_session_store`, `comparison_store`, `investigation_store`, `intelligence_store`) delegate to repositories — **zero service changes**
- Default provider remains `memory` for backward compatibility

### Verification

- 76 backend pytest tests passing (memory provider)
- 32 Playwright E2E tests passing (unchanged API)

---

## [0.4.0] — 2026-07-09 — Comparison + Investigation Migration

### Added

- **Feature modules:** `features/comparison/`, `features/investigation/`
- Comparison components: `ComparisonToolbar`, `ComparisonSummary`, `ComparisonDetail`, `ComparisonObservations`, `ComparisonActions`
- Investigation components: `CaseSidebar`, `CaseFilters`, `CaseActions`, `CaseTable`, `CaseDetails`, `InvestigationToolbar`
- Page hooks: `useComparisonPage`, `useInvestigationPage` (services layer only)
- Docs: [FEATURE_MODULES.md](./FEATURE_MODULES.md)

### Changed

- **Comparison** — migrated to Dashboard architecture; `ComparisonScreen.jsx` is a thin re-export
- **Investigation** — three-panel layout via `InvestigationLayout`; zero inline badges; `PriorityBadge` with score display
- Legacy `components/investigation/*` re-export feature components for `WorkbookViewer` compatibility
- [COMPONENT_LIBRARY.md](./COMPONENT_LIBRARY.md), [MIGRATION_REPORT.md](./MIGRATION_REPORT.md) updated with v0.4 metrics

### Verification

- 32/32 Playwright E2E passing (desktop + tablet + mobile viewport)
- Production build success
- Zero `bg-zinc` / `lucide-react` in Comparison and Investigation feature code

---

## [0.3.1] — 2026-07-09 — Dashboard + Layout Complete

### Completed

- **All** `components/dashboard/*` migrated to theme tokens (zero zinc, zero lucide)
- **Layout.jsx** migrated: `SidebarSection`, `AppBrand`, `ThemeToggleButton`, `Icons.*`
- Workbook Summary → `DataTable` + `workbookColumns.js`
- `RiskCard`, `theme/calendar.js`, Radix Tooltip for `StatusTooltip`
- Accessibility: ARIA on calendar grid, modal focus, nav labels

### Reference architecture

Dashboard is the canonical pattern for future pages (Comparison, Investigation, Report).

### Verification

- 22/22 Playwright E2E passing
- Production build success

---

## [0.3.0] — 2026-07-09 — Design System Migration (Dashboard partial)

### Added

- Layout: `PageLayout`, `DashboardLayout`, `SectionContainer`, `ResponsiveGrid`, `Toolbar`
- Cards: `ContentCard`, `MetricCard`, `SummaryCard`, `ProgressCard`, `DatasetCard`
- Badges: `AuditBadge`, `DatasetBadge`, `ComparisonBadge`, `PriorityBadge`
- shadcn: `Input`, `Textarea`, `Label`, `Tooltip`, `Separator`
- Theme: `forms`, `charts`, `sidebar`, `layout`, `animations`, semantic `theme.text` / `theme.alert`
- Docs: `REFACTOR_AUDIT.md`, `MIGRATION_REPORT.md`

### Changed

- **Dashboard** — reference implementation using theme tokens, shared layout/cards/badges
- `UploadHistoryTable` → `DataTable` + `columns/uploadColumns.js`
- `useDashboard` hook exports `resolveDuplicate`, `hasSession`
- 22 Playwright E2E tests passing

### Verification

- Build succeeds; bundle +4.3% gzip (shared layer + Radix Tooltip)

---

## [0.2.0] — 2026-07-09 — Architecture Foundation

Standardization pass with no new product features.

### Added

- Full documentation suite under `docs/` (architecture, API reference, testing, performance, security, roadmap)
- ADRs `DECISIONS/ADR-001` through `ADR-006`
- Theme tokens in `frontend/src/theme/`
- shadcn-style UI primitives in `frontend/src/components/ui/`
- Shared component library in `frontend/src/components/common/` including unified `DataTable`
- Custom hooks in `frontend/src/hooks/`
- Consolidated utilities (`formatCurrency`, `formatGSTIN`, `riskUtils`, etc.)
- Unified API client (`frontend/src/api/client.js`)

### Changed

- Tailwind + CSS variables for semantic design tokens
- `ComparisonRecordsTable` refactored to wrap `DataTable`
- Dashboard, comparison, investigation, intelligence APIs use `apiFetch`
- `MergePage` deduplicated file helper imports

### Verification

- 67 backend tests, 22 Playwright E2E tests, production build — all passing

---

## [0.7.0] — 2026-07-09 — Enterprise Security

Government-ready authentication, authorization, audit logging, and administration.

### Added

- JWT authentication with refresh tokens and secure httpOnly cookies
- RBAC: 6 roles, 17 fine-grained permissions
- Security middleware protecting all `/api/*` endpoints
- User management API and admin panel (`/admin`)
- Audit logging (`audit_logs` table + mutation middleware)
- Session management: concurrent limits, logout-all, open sessions
- Password policy: length, complexity, history, expiry support
- Rate limiting (in-memory, configurable)
- Dashboard **Officer Session** panel: current user, last login, activity, sessions
- Alembic migration `003_security_schema.py`
- Docs: `AUTHENTICATION.md`, `RBAC.md`, `AUDIT_LOGGING.md`, `ADMIN_GUIDE.md`
- Playwright `auth.spec.js` — login, permission denied, audit logs

### Changed

- All API routes require authentication (`AUTH_DISABLED=true` for dev/tests only)
- Frontend login page, protected routes, auth headers on all API calls
- Default bootstrap admin: `admin` / `Admin@123456!`

### Verification

- Backend pytest: 90+ passing
- Playwright E2E: 42 tests including security suite

---

## [0.6.0] — 2026-07-09 — Background Job Processing

All long-running operations execute through a background job queue instead of blocking HTTP handlers.

### Added

- Job queue with states: queued, running, completed, failed, cancelled, retrying
- Job types: `comparison`, `intelligence`, `report`, `merge`, `import` (+ reserved `ai`)
- PostgreSQL tables: `jobs`, `job_logs`, `job_progress` (migration `002_jobs_schema.py`)
- Embedded + standalone worker (`backend/worker.py`) with configurable concurrency
- Job API: create, list, get, cancel, retry, download
- WebSocket `/ws/jobs/{session_id}` for live dashboard progress
- Comparison checkpoint/resume on retry
- Dashboard **Job Queue** panel with cancel, retry, and open result
- `docs/BACKGROUND_JOBS.md`

### Changed

- `POST /api/comparison/gstr1-eway` returns **202** with `job_id` (no synchronous comparison)
- `POST /api/report/generate` returns **202** with `job_id`
- Intelligence analysis runs as separate background job after comparison
- `GET /api/intelligence/*` reads cached results only (no inline analysis)
- Frontend comparison and report flows poll job status

### Verification

- Backend pytest (80+), frontend production build, Playwright E2E including `jobs.spec.js`

---

## [0.8.0] — 2026-07-09 — Platform Operations

Production operations dashboard for government deployment monitoring.

### Added

- **System Monitor** navigation (`/system-monitor`) with health, metrics, jobs, sessions, users, performance, storage, backup, configuration, and logs panels
- System API: `GET /api/system/health`, `/metrics`, `/jobs`, `/users`, `/storage`, `/version`, `/config`, `/sessions`, `/logs`, `/logs/export`
- RBAC permission `view_system_monitor` (administrator only)
- Host metrics via `psutil` (CPU, memory, disk) with graceful fallback
- Global job listing (`list_all`) for cross-session operations view
- Playwright E2E: `e2e/system-monitor.spec.js` (health cards, logs, responsive, dark mode)
- Backend tests: `backend/tests/test_system_monitor.py`

### Verification

- Backend pytest **96 passed**, Playwright E2E **46 passed**, frontend build green

---

## [0.9.0] — 2026-07-09 — Plugin SDK

Platform extension layer for installable GST modules without core changes.

### Added

- **Plugin SDK** — `backend/plugins/sdk/` (manifest, registry, loader, context)
- **Plugin catalog API** — `GET /api/plugins`
- **Reference plugin** — `plugins/gstr1/` (GSTR-1 merge + comparison; identical behavior)
- **Stub plugin directories** — gstr2a, eway, purchase, sales, gstr3b, analytics, future
- **Frontend registry** — `frontend/src/plugins/registry.js`
- **Documentation** — PLUGIN_SDK.md, PLUGIN_GUIDE.md, PLUGIN_API.md, PLUGIN_EXAMPLES.md
- **Tests** — `backend/tests/test_plugin_loader.py`

### Changed

- GSTR-1 routes moved from `main.py` to `plugins/gstr1/routes.py`
- Comparison bootstrap delegates to plugin loader
- Job executor dispatches comparison jobs via plugin registry

### Plugin modules

- `plugins/gstr2a/` — GSTR-2A ↔ EWB Inward purchase verification (v1.0.0)

---

## [1.0.0] — plugins/gstr2a — GSTR-2A Purchase Verification

Installable plugin — zero platform core changes.

### Added

- GSTR-2A ↔ EWB Inward comparator (`gstr2a_ewb_inward`)
- `POST /api/comparison/gstr2a-eway` background job enqueue
- Purchase intelligence observations and **Purchase Reconciliation** report section
- Automatic investigation case creation via platform engine
- Tests: `backend/tests/test_gstr2a_plugin.py`, `e2e/gstr2a-plugin.spec.js`

---

## [Unreleased]

### Added — Multi-Source Audit Engine (MSAE) v1.0

Platform-level audit orchestration module — consumes comparison plugin outputs without modifying plugins.

- **Backend:** `backend/services/msae_service.py`, pattern engine, models, routes (`/api/msae/*`)
- **Multi-source ingestion:** `list_results(session_id)` reads all comparison runs (GSTR-1 ↔ EWB Outward, GSTR-2A ↔ EWB Inward)
- **Case consolidation:** Master investigation cases with child plugin findings correlated by invoice
- **Audit scores:** Dealer, month, supplier, customer risk; officer priority; audit confidence
- **Cross-source patterns:** Repeated supplier mismatch, month spikes, round values, duplicates, split invoices, GSTIN errors, tax variance
- **Audit timeline:** Upload → merge → comparison → MSAE orchestration → investigation
- **Frontend:** Audit Intelligence Center (`/audit-intelligence`) — top risks, master cases, heatmaps, trends
- **Consolidated report:** `consolidated_audit` section in audit report preview
- **Tests:** `backend/tests/test_msae_service.py` (113 total pytest), `e2e/msae.spec.js`

### Added — Audit Case Management Workflow v1.0

Platform workflow layer on MSAE master cases — full government GST audit lifecycle.

- **Workflow:** Draft → Assigned → Under Investigation → Notice Issued → Dealer Response → Verification → Supervisor Review → Approved → Closed → Archived
- **Backend:** `case_management_service.py`, `workflow_engine.py`, routes `/api/audit-cases/*`
- **Features:** Assignment, notices, documents, dealer responses, timeline, officer tasks, supervisor dashboard
- **Database:** Migration `004_case_management_schema.py` (8 tables)
- **Frontend:** `/audit-cases`, `/officer-tasks`, `/supervisor-dashboard`
- **Permissions:** `manage_audit_cases`, `supervise_audit_cases`
- **Docs:** `CASE_MANAGEMENT.md`, `WORKFLOW_ENGINE.md`, `NOTICE_SYSTEM.md`, `TIMELINE.md`
- **Tests:** `test_case_management.py`, `e2e/case-management.spec.js`

### Added — Purchase Register Plugin v1.0

Plugin-only module at `plugins/purchase/` — reconciles Purchase Register against GSTR-2A and EWB Inward.

- **Import:** Smart column detection (Tally/Busy/Marg/generic), mapping profiles, HTML workbench at `/api/purchase/ui`
- **Comparisons:** `purchase_register_vs_gstr2a`, `purchase_register_vs_ewb_inward`
- **Intelligence:** Risk, priority, suggested documents, officer observations via canonical comparison results (MSAE-ready)
- **Report:** `purchase_register_reconciliation` section
- **Tests:** `backend/tests/test_purchase_plugin.py`, `e2e/purchase-plugin.spec.js`

Report page migration and Merge/E-way design system adoption — see [ROADMAP.md](./ROADMAP.md).

---

[0.1.0]: https://github.com/your-org/gstaudit/releases/tag/v0.1.0
