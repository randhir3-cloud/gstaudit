# State Management

GAIS uses **React Context** for global state. No Redux, Zustand, or React Query in v0.1.

## Overview

```
┌─────────────────────────────────────────────────────────────┐
│ DealerContext          — workbook-level dealer metadata      │
│ AuditSessionContext    — full audit workflow + dashboard     │
│ EwayContext            — EWB upload/merge workflow state   │
└─────────────────────────────────────────────────────────────┘
         │ localStorage              │ component-local useState
         ▼                           ▼
   gst_audit_session            page fetch state
```

## AuditSessionContext

**File:** `frontend/src/context/AuditSessionContext.jsx`  
**Hook:** `useAuditSession()`

### State shape

Mirrors backend `AuditSession` with client-side additions:

| Field | Source |
|-------|--------|
| `session` | localStorage + user actions |
| `dashboard` | `GET /api/dashboard` response |
| `loading` | Dashboard refresh in flight |

Session object includes: `session_id`, `dealer`, `financial_year`, `datasets`, `upload_history`, `comparison_status`, `discrepancies`, timestamps.

### Persistence

- **Key:** `gst_audit_session` (`STORAGE_KEY` in `types/auditSession.js`)
- **Write:** every `recordUpload`, `recordMerge`, `resolveDuplicate`
- **Sync:** debounced 400 ms → `POST /api/session/sync`
- **Offline:** sync failures are silently ignored; local state remains valid

### Session ID generation

```javascript
// types/auditSession.js
buildSessionId(gstin, financialYear) → `session_${hash}`
```

Hash is deterministic from `{GSTIN}:{FY}` so frontend and backend agree on identity.

### Actions

| Method | Trigger |
|--------|---------|
| `recordUpload(datasetKey, filenames, dealer, rows)` | File selected on merge page |
| `recordMerge(datasetKey, payload)` | Successful merge API response |
| `resolveDuplicate(datasetKey, month, action, keepFilename)` | Duplicate month resolution |
| `refreshDashboard()` | Manual refresh; called on session_id change |
| `clearSession()` | Reset workflow |

### Derived values

- `hasSession` — `Boolean(session.dealer?.gstin)`

### Consumers

- `Dashboard.jsx` — primary dashboard data
- `ComparisonScreen.jsx` — session_id for comparison API
- `InvestigationPage.jsx` — session_id for cases
- `MergePage.jsx` — record upload/merge events

## DealerContext

**File:** `frontend/src/context/DealerContext.jsx`  
**Hook:** `useDealer()`

### Purpose

Holds **current workbook metadata** extracted from merge response headers (`X-Workbook-Metadata` JSON). Separate from audit session because a user may inspect workbook metadata before a full session exists.

### State

| Field | Description |
|-------|-------------|
| `workbookId` | Stable workbook identifier |
| `dealer` | `{ gstin, legal_name, financial_year, tax_period, ... }` |
| `returnType` | `gstr1` \| `gstr2a` |
| `sourceFiles` | Original upload filenames |
| `currentDataset` | Display label for active workbook |

### Actions

- `setWorkbookMetadata(metadata)` — parse API response header
- `clearDealer()` — reset all fields
- `setCurrentDataset(label)` — update display name

### Derived

- `hasDealer` — `Boolean(dealer?.gstin)`

### Consumers

- `DealerHeader.jsx` — shows GSTIN, name, FY across pages
- `MergePage.jsx` — sets metadata after GSTR merge
- `ComparisonScreen.jsx` — gates UI when no dealer

**Note:** `AuditSessionContext` also stores `dealer` on the session. DealerContext is the **active workbook** view; AuditSession is the **audit-wide** view. They converge after merge via `recordMerge`.

## EwayContext

**File:** `frontend/src/context/EwayContext.jsx`  
**Hooks:** `useEway()`, `useEwayWorkflow(direction)`

### Purpose

Manages **dual EWB workflows** (outward and inward) with classification modals, merge state, and cross-direction file moves.

### State per direction (`outward` | `inward`)

```javascript
{
  direction,
  files: [],              // classified file entries with ids
  mergeStatus: 'idle' | 'merging' | 'merged' | 'error',
  error, successMessage,
  warningModal,            // missing months
  wrongUploadModal,        // direction mismatch
  unknownModal,            // unclassifiable file
  mergedWorkbook: { blob, filename },
  summary,                 // row counts, sheets, dealer
  dealerMetadata,
  previewOpen,
  outputName,
  isClassifying,
}
```

### Global EWB state

| Field | Purpose |
|-------|---------|
| `activeSubTab` | `'outward'` \| `'inward'` |
| `dealerGstin` | User-resolved GSTIN for classification |
| `dealerGstinSource` | `'user'` \| `'gstr1'` \| `'none'` |
| `dealerGstinModalOpen` | Prompt when GSTIN unknown |
| `pendingUploadQueue` | Files waiting for GSTIN resolution |

### Actions

| Method | Purpose |
|--------|---------|
| `getWorkflow(direction)` | Read outward/inward state |
| `updateWorkflow(direction, updater)` | Patch workflow |
| `applyMergeResult(direction, result)` | Decode base64 workbook to Blob |
| `moveFileToDirection(file, target, source)` | Wrong-upload auto-move |
| `setResolvedDealerGstin(gstin, source)` | Close GSTIN modal |

### Helper hook

```javascript
useEwayWorkflow('outward') → { workflow, updateWorkflow, applyMergeResult, direction, ...ctx }
```

Used by `EwayWorkflowPanel.jsx` and `EwayBillSection.jsx`.

## Data Flow Diagram

```
Merge GSTR-1
  → setWorkbookMetadata (DealerContext)
  → recordMerge (AuditSessionContext)
  → debounced syncSession → backend

Merge EWB Outward
  → applyMergeResult (EwayContext)
  → recordMerge ewb_outward (AuditSessionContext)

Run Comparison
  → reads session.session_id (AuditSessionContext)
  → backend updates discrepancies
  → refreshDashboard()

Open Investigation
  → session_id → GET /api/investigation
  → cases include intelligence enrichment from backend
```

## Local vs Server State

| Data | Authority | Notes |
|------|-----------|-------|
| Session metadata | Client + server | Client writes first; server rebuilds dashboard |
| Merged workbook bytes | Client (Blob) | Not stored on server in v0.1 except comparison cache |
| Comparison results | Server | `comparison_store` |
| Investigation cases | Server | Synced from comparison; officer updates via PATCH |
| Intelligence | Server | Cached analysis per session |

## Anti-patterns

- Do not duplicate session state in page-level state — use `useAuditSession()`.
- Do not call `syncSession` directly from pages — use context actions.
- Do not store workbook Blobs in AuditSessionContext (too large for localStorage).

## Related

- [FRONTEND_ARCHITECTURE.md](./FRONTEND_ARCHITECTURE.md)
- [ARCHITECTURE.md](./ARCHITECTURE.md)
