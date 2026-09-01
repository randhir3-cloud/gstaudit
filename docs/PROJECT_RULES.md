# GAIS Project Rules

Engineering standards for the GST Audit Intelligence System (GAIS). These rules reflect how the codebase is actually structured today and how we extend it going forward.

## Architectural Principles

### Clean Architecture (Pragmatic)

We apply a **layered, dependency-inward** model without over-abstracting:

| Layer | Location | Responsibility |
|-------|----------|----------------|
| **Delivery** | `backend/main.py`, `frontend/src/pages/` | HTTP routes, routing, user interaction |
| **Application** | `backend/services/`, `frontend/src/context/` | Orchestration, session sync, use cases |
| **Domain** | `backend/comparison/`, `backend/intelligence/`, `backend/models/` | Business rules, matchers, scoring |
| **Infrastructure** | `*_store.py`, `merger.py`, `data_loader.py` | Persistence, file I/O, Excel parsing |

**Rules:**

1. `main.py` delegates to services — no business logic in route handlers beyond validation and HTTP mapping.
2. Comparison matchers (`comparison/comparators/`) must not import from `main.py` or FastAPI.
3. Frontend pages compose components and call `api/` modules — no raw `fetch` scattered in JSX.
4. Pydantic models in `backend/models/` are the contract between layers.

### SOLID

| Principle | GAIS Application |
|-----------|------------------|
| **S** — Single Responsibility | Each comparator file handles one concern (e.g. `value_matcher.py`). Each service file owns one domain (e.g. `investigation_service.py`). |
| **O** — Open/Closed | New comparisons register via `comparison_registry.register()` without editing `ComparisonEngine`. |
| **L** — Liskov Substitution | All comparators implement `(config, left_bytes, right_bytes, session_id) → ComparisonResult`. |
| **I** — Interface Segregation | API modules split by domain (`api/dashboard.js`, `api/comparison.js`, …). |
| **D** — Dependency Inversion | `ComparisonEngine` depends on registry abstraction, not concrete comparators. |

### DRY

- Normalization logic lives once in `comparison/normalizer.py`.
- Dashboard aggregation is centralized in `dashboard_service.build_dashboard()` — individual `/api/dashboard/*` endpoints reuse it.
- Session ID generation: backend accepts frontend-computed `session_id`; algorithm documented in `auditSession.js`.
- Risk scoring weights defined once in `comparison/comparators/risk_engine.py`.

**When duplication is acceptable:** Tailwind class strings in components (extract only when a third identical pattern appears).

## Definition of Done

A feature or fix is **done** when all of the following are true:

1. **Functional** — Implements the stated requirement with correct behavior on happy path and documented error paths.
2. **Typed / validated** — Backend uses Pydantic models; frontend validates API responses where shapes are critical.
3. **Tested** — Backend: pytest in `backend/tests/` for service/domain logic. E2E: Playwright spec when the change is user-visible (`e2e/*.spec.js`).
4. **Integrated** — Session state, dashboard, and downstream modules (comparison → investigation → intelligence) stay consistent.
5. **Verified** — Manually or via IronBee DevTools / Playwright against running frontend + backend (see `.cursor/rules/ironbee-devtools-use.mdc`).
6. **Documented** — API changes update `docs/API_REFERENCE.md`; architectural shifts add an ADR under `docs/DECISIONS/`.

## Coding Standards

### Python (Backend)

- Python 3.11+, type hints on public functions.
- Pydantic v2 models with `model_dump()` for JSON responses.
- Module docstrings on packages and non-obvious modules.
- Exceptions: domain errors (`DealerValidationError`, `EwayValidationError`) return structured JSON; unexpected errors become HTTP 500.
- Tests: `pytest`, fixtures in `backend/tests/*_fixtures.py`.
- Import comparators through `comparison/bootstrap.py` side-effect registration.

```python
# Preferred service pattern
def run_gstr1_eway_comparison(session_id: str, ...) -> ComparisonResult:
    session = get_session(session_id)
    if not session:
        raise ValueError("Session not found")
    ...
```

### JavaScript (Frontend)

- React 19 functional components with hooks.
- Context providers for cross-cutting state (`AuditSessionContext`, `DealerContext`, `EwayContext`).
- API base URL from `import.meta.env.VITE_API_BASE` with fallback to `http://127.0.0.1:8000`.
- `data-testid` attributes on elements covered by Playwright specs.
- Lint with `npm run lint` (oxlint).
- Unit tests with Vitest for isolated components (e.g. `DealerHeader.test.jsx`).

### Git & Reviews

- Focused commits; do not commit secrets, sample taxpayer PDFs with PII, or `.env` virtualenvs.
- PRs describe user-visible impact and list test commands run.

## Naming Conventions

| Artifact | Convention | Example |
|----------|------------|---------|
| API routes | kebab-case, `/api/` prefix | `/api/comparison/gstr1-eway` |
| Python modules | snake_case | `investigation_service.py` |
| React components | PascalCase | `ComparisonStatusCards.jsx` |
| Context hooks | `use` prefix | `useAuditSession()` |
| Session / case IDs | prefixed hashes | `session_abc123`, `CASE-A1B2C3D4` |
| Comparison result types | SCREAMING_SNAKE | `MISSING_IN_GSTR1` |

## Security Baseline

- No authentication in v0.1 — deploy only on trusted networks or behind auth gateway (see [SECURITY.md](./SECURITY.md)).
- Validate file uploads server-side; never trust client classification alone for EWB direction.
- CORS is `*` in dev — tighten for production.

## Related Documents

- [UI_STANDARDS.md](./UI_STANDARDS.md)
- [TESTING.md](./TESTING.md)
- [DECISIONS/](./DECISIONS/)
