# ADR-011: Background Job Processing

## Status

Accepted (implemented v0.6.0)

## Context

Large comparisons and report generation block HTTP requests. Officers may upload 500k-row workbooks.

## Options

| Option | Fit |
|--------|-----|
| FastAPI BackgroundTasks | Simple, single-instance |
| Celery + Redis | Multi-worker, retries, scheduling |
| ARQ (async Redis queue) | Lighter than Celery, async-native |
| In-process thread-pool worker + DB queue | No extra infra; works with memory or PostgreSQL |

## Decision

**In-process job queue** backed by `jobs` / `job_logs` / `job_progress` tables (see [BACKGROUND_JOBS.md](../BACKGROUND_JOBS.md)).

- HTTP handlers enqueue work and return **202 Accepted** with `job_id`
- Embedded worker (default) or standalone `python worker.py` processes jobs with configurable concurrency
- WebSocket `/ws/jobs/{session_id}` pushes live progress to the dashboard
- Comparison jobs support checkpoint resume on retry

Long-running paths (comparison, intelligence, report) never execute synchronously on HTTP threads. Merge/import can also be submitted via `POST /api/jobs`.

## Consequences

- Job API: create, list, get, cancel, retry, download
- Dashboard Job Queue panel with cancel, retry, open result
- Intelligence analysis is a separate job spawned after comparison completes
- Read endpoints use cached intelligence only

## References

- [BACKGROUND_JOBS.md](../BACKGROUND_JOBS.md)
- [PERFORMANCE.md](../PERFORMANCE.md)
