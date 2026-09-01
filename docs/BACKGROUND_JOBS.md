# Background Jobs Architecture

GAIS v0.6 moves all long-running work off the HTTP request thread into a durable job queue with live progress and WebSocket updates.

## Flow

```
Client → API (202 Accepted + job_id)
           ↓
       jobs table (PostgreSQL or memory)
           ↓
       Worker (embedded or standalone)
           ↓
       Executors → Services → Repositories
           ↓
       WebSocket /ws/jobs/{session_id} → Dashboard Job Queue panel
```

## Job Types

| Type | Trigger | Executor |
|------|---------|----------|
| `comparison` | `POST /api/comparison/gstr1-eway` | GSTR-1 ↔ EWB comparison with checkpoint resume |
| `intelligence` | Auto after comparison; `POST /api/intelligence/analyze` | Pattern analysis + case enrichment |
| `report` | `POST /api/report/generate` | Excel / PDF / DOCX audit report |
| `merge` | `POST /api/jobs` with `job_type: merge` | GSTR-1 / GSTR-2A workbook merge |
| `import` | `POST /api/jobs` with `job_type: import` | Large workbook cache import |
| `ai` | Reserved | Future AI analysis |

## Job States

`queued` → `running` → `completed` | `failed` | `cancelled`

Failed or cancelled jobs can be moved to `retrying` via `POST /api/jobs/{id}/retry`.

## Progress Model

Every running job reports:

- **percent** — 0–100
- **stage** — human-readable step (e.g. "Invoice Matching")
- **rows_processed** / **rows_total**
- **eta_seconds** — estimated remaining time
- **started_at** / **updated_at**

Progress is persisted in `job_progress` and broadcast over WebSocket.

## Database Tables

| Table | Purpose |
|-------|---------|
| `jobs` | Job metadata, status, payload, result_ref, checkpoint |
| `job_logs` | Structured log lines per job |
| `job_progress` | Historical progress snapshots |

Migration: `backend/alembic/versions/002_jobs_schema.py`

## API

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/jobs` | Create arbitrary job (merge, import, etc.) |
| GET | `/api/jobs?session_id=` | List jobs for session |
| GET | `/api/jobs/{id}` | Job detail + progress |
| POST | `/api/jobs/{id}/cancel` | Cancel queued or running job |
| POST | `/api/jobs/{id}/retry` | Retry failed/cancelled job (uses checkpoint) |
| GET | `/api/jobs/{id}/download` | Download completed report result |
| WS | `/ws/jobs/{session_id}` | Live job progress events |

Long-running endpoints return **202 Accepted** with `{ job_id, status, session_id }`:

- `POST /api/comparison/gstr1-eway`
- `POST /api/report/generate`
- `POST /api/intelligence/analyze`

Read endpoints (`GET /api/intelligence/*`, dashboard) use **cached** intelligence only — they never run analysis inline.

## Workers

### Embedded (default)

```bash
JOB_WORKER_EMBEDDED=true   # default
JOB_WORKER_COUNT=2
JOB_POLL_INTERVAL_MS=500
```

The FastAPI lifespan starts an embedded thread-pool worker when the API boots.

### Standalone

```bash
cd backend
python worker.py
```

Set `JOB_WORKER_EMBEDDED=false` on the API process when using a dedicated worker.

## Checkpoint Resume

Comparison jobs save checkpoints during invoice matching (`eway_index`, `classified` records). On retry after failure, the worker resumes from the last checkpoint instead of restarting from zero.

## Frontend

- `frontend/src/api/jobs.js` — REST + WebSocket helpers
- `frontend/src/hooks/useJobs.js` — live job state for dashboard
- `frontend/src/components/dashboard/JobQueuePanel.jsx` — cancel, retry, open result

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_PROVIDER` | `memory` | `memory` or `postgres` |
| `JOB_WORKER_EMBEDDED` | `true` | Run worker inside API process |
| `JOB_WORKER_COUNT` | `2` | Concurrent job threads |
| `JOB_POLL_INTERVAL_MS` | `500` | Queue poll interval |

See also [DATABASE.md](./DATABASE.md) and [ARCHITECTURE.md](./ARCHITECTURE.md).
