# ADR-001: System Architecture

**Status:** Accepted  
**Date:** 2026-07-09  
**Deciders:** GAIS core team

## Context

GAIS must merge multiple GST Excel workbooks, run cross-dataset comparisons, support officer investigation workflows, and generate audit reports. The team needed to choose a stack and structural pattern that supports rapid iteration by a small team while allowing modular extension (new comparison pairs, intelligence rules).

## Decision

Adopt a **React SPA + FastAPI monolith** with **feature-oriented backend packages**:

```
frontend/ (React/Vite)  ←REST→  backend/main.py
                                      ├── services/     (orchestration)
                                      ├── comparison/   (domain)
                                      ├── intelligence/ (domain)
                                      └── models/       (contracts)
```

Key choices:

1. **Single FastAPI app** — one deployable backend unit; no microservices in v0.1
2. **Pluggable comparison registry** — new comparators without engine changes
3. **AuditSession as aggregate root** — central workflow state synced from frontend
4. **In-memory stores** — acceptable for v0.1 prototype; database deferred to v0.2
5. **Client-side session persistence** — localStorage + debounced API sync for offline resilience

## Consequences

### Positive

- Fast local development (uvicorn + vite hot reload)
- Clear separation: HTTP → services → domain packages
- Frontend contexts map cleanly to backend session model
- Docker Compose deploys two containers with Nginx API proxy

### Negative

- In-memory stores prevent horizontal scaling and durability
- Monolith grows with each new domain — may need module boundaries enforced by lint rules
- Base64 workbook transfer adds overhead vs dedicated object storage

## Alternatives Considered

| Alternative | Why rejected (v0.1) |
|-------------|---------------------|
| Next.js full-stack | Team familiarity with Vite; API already Python/pandas-heavy |
| Django | FastAPI + Pydantic better fit for typed API + OpenAPI |
| Microservices (merge vs compare) | Operational overhead unjustified at current scale |
| Electron desktop app | Web deploy preferred for shared audit stations |

## References

- `backend/main.py`
- `docs/ARCHITECTURE.md`
- `docs/BACKEND_ARCHITECTURE.md`
