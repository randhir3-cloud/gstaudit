# Frontend Architecture

The GAIS frontend is a React 19 single-page application built with Vite 8 and Tailwind CSS 3. It communicates with the FastAPI backend over REST.

## Entry Points

| File | Role |
|------|------|
| `frontend/index.html` | HTML shell |
| `frontend/src/main.jsx` | ReactDOM root, imports `index.css` |
| `frontend/src/App.jsx` | Providers, router, theme toggle |
| `frontend/vite.config.js` | Vite + React plugin configuration |

## Provider Hierarchy

```jsx
<DealerProvider>
  <AuditSessionProvider>
    <EwayProvider>
      <BrowserRouter>
        <Layout />  {/* Outlet for pages */}
      </BrowserRouter>
    </EwayProvider>
  </AuditSessionProvider>
</DealerProvider>
```

Defined in `frontend/src/App.jsx`. Nesting order matters: audit session wraps EWB workflows because merge events update session datasets.

## Pages

| Route | Component | Description |
|-------|-----------|-------------|
| `/` | `pages/Dashboard.jsx` | FY calendar, dataset cards, readiness, intelligence panel, case tracking |
| `/merge` | `pages/MergePage.jsx` | GSTR-1, GSTR-2A, EWB outward/inward upload and merge |
| `/workbook` | `pages/WorkbookViewer.jsx` | Preview merged workbook blobs |
| `/comparison` | `pages/ComparisonScreen.jsx` | Run GSTR-1 vs EWB comparison, view summary/risk/observations |
| `/investigation` | `pages/InvestigationPage.jsx` | Case workbench with filters, detail panel, bulk actions |
| `/audit-report` | `pages/AuditReportPreview.jsx` | Report preview and export (Excel/PDF/DOCX) |

All pages render inside `components/Layout.jsx` which provides header navigation, theme toggle, and footer.

## Component Organization

```
frontend/src/components/
├── Layout.jsx                 # App shell + nav
├── DealerHeader.jsx           # Shared dealer identity banner
├── dashboard/                 # Dashboard-specific widgets
│   ├── AuditHeader.jsx
│   ├── FinancialYearCalendar.jsx
│   ├── DatasetStatusCard.jsx
│   ├── ComparisonStatusCards.jsx
│   ├── AuditIntelligencePanel.jsx
│   ├── CaseTrackingPanel.jsx
│   └── ...
├── merge/                     # File upload UI
│   ├── FileUploadZone.jsx
│   └── FileList.jsx
├── eway/                      # E-Way Bill workflow
│   ├── EwayWorkflowPanel.jsx
│   ├── WrongUploadDialog.jsx
│   └── DealerGstinModal.jsx
└── investigation/             # Investigation workbench
    ├── InvestigationCategoryPanel.jsx
    ├── InvestigationDetailsPanel.jsx
    └── ComparisonRecordsTable.jsx
```

Components are **feature-colocated** by screen domain, not by atomic design tier. Shared primitives are inlined with Tailwind rather than a large `ui/` library (see [DECISIONS/ADR-006-ShadcnAdoption.md](./DECISIONS/ADR-006-ShadcnAdoption.md)).

## Contexts

See [STATE_MANAGEMENT.md](./STATE_MANAGEMENT.md) for full detail.

| Context | Hook | Scope |
|---------|------|-------|
| `DealerContext` | `useDealer()` | Current workbook metadata from merge response headers |
| `AuditSessionContext` | `useAuditSession()` | Full audit session + dashboard, localStorage persistence |
| `EwayContext` | `useEway()`, `useEwayWorkflow(dir)` | Outward/inward EWB file queues, modals, merge results |

## API Layer

Thin fetch wrappers in `frontend/src/api/`:

| Module | Backend prefix |
|--------|----------------|
| `dashboard.js` | `/api/dashboard`, `/api/session/sync` |
| `dealer.js` | `/api/dealer/extract` |
| `eway.js` | `/api/eway/*`, `/api/merge/eway/*` |
| `comparison.js` | `/api/comparison/*` |
| `investigation.js` | `/api/investigation/*` |
| `intelligence.js` | `/api/intelligence/*` |

Pattern:

```javascript
const API_BASE = import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8000';

export async function fetchDashboard(sessionId) {
  const res = await fetch(`${API_BASE}/api/dashboard?session_id=${encodeURIComponent(sessionId)}`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}
```

## Types

JSDoc-style constants in `frontend/src/types/`:

- `dealer.js` — `EMPTY_DEALER`, dealer field shapes
- `auditSession.js` — `DATASET_KEYS`, `buildSessionId()`, `STORAGE_KEY`

No TypeScript in v0.1; types are documentation for developers.

## Utilities

| File | Purpose |
|------|---------|
| `utils/fileHelpers.js` | Base64 ↔ Blob conversion for merged workbooks |
| `utils/formatNumbers.js` | Indian locale number/percent formatting |

## Theme

Dark mode uses Tailwind `darkMode: 'class'` with toggle stored in `localStorage` key `theme`. Default: **dark**. See [THEME_GUIDE.md](./THEME_GUIDE.md).

## Hooks Pattern

GAIS does not use a global hooks library. Patterns in use:

1. **Context hooks** — `useAuditSession()`, `useDealer()`, `useEway()`.
2. **Derived workflow hook** — `useEwayWorkflow('outward' | 'inward')` binds direction to workflow state.
3. **Page-local state** — `useState` + `useCallback` + `useEffect` for screen-specific fetching (e.g. `ComparisonScreen` loads comparison on mount).
4. **Debounced sync** — `AuditSessionContext` uses `setTimeout(400ms)` before `POST /api/session/sync`.

Avoid extracting hooks unless the same effect runs in 3+ components.

## Build & Dev

```bash
cd frontend
npm install
npm run dev          # http://127.0.0.1:5173
npm run build        # output to dist/
npm run test         # Vitest
npm run lint         # oxlint
```

Production build served by Nginx (`frontend/Dockerfile`, `frontend/nginx.conf`) with `/api/` proxied to backend.

## Testing Hooks

- `data-testid` on interactive and assertion targets (e.g. `run-comparison-btn`, `comparison-status`).
- Vitest setup: `frontend/src/test/setup.js`, config in `vitest.config.js`.

## Related

- [COMPONENT_LIBRARY.md](./COMPONENT_LIBRARY.md)
- [UI_STANDARDS.md](./UI_STANDARDS.md)
- [STATE_MANAGEMENT.md](./STATE_MANAGEMENT.md)
