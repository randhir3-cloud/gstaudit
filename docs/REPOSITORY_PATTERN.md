# Repository Pattern

GAIS uses a repository layer to decouple services from persistence. Services call store modules; stores delegate to repositories selected by configuration.

---

## Architecture

```
Controller (main.py)
       ↓
   Service (*_service.py)
       ↓
   Store (*_store.py)          ← unchanged public API
       ↓
   Repository Interface       ← ABC in repositories/interfaces.py
       ↓
   Implementation
   ├── MemoryRepository       ← default (DATABASE_PROVIDER=memory)
   └── PostgresRepository     ← DATABASE_PROVIDER=postgres
       ↓
   Database (PostgreSQL)
```

**Rule:** Services never import SQLAlchemy or execute SQL. Only repository implementations touch the database.

---

## Repository Interfaces

| Interface | Store adapter | Key methods |
|-----------|---------------|-------------|
| `DealerRepository` | (via session) | `create`, `get_by_gstin_fy` |
| `AuditSessionRepository` | `audit_session_store` | `create`, `update`, `get_by_id`, `search` |
| `WorkbookRepository` | `comparison_store` | `cache_workbook`, `get_workbook` |
| `ComparisonRepository` | `comparison_store` | `save_result`, `get_result`, `search_records` |
| `InvestigationCaseRepository` | `investigation_store` | `create`, `bulk_update`, `search` |
| `AuditIntelligenceRepository` | `intelligence_store` | `save`, `get` |
| `AuditReportRepository` | (future report cache) | `create`, `get_by_session` |

Standard method families:

- **Create / Update / Delete**
- **Get By ID / Get By Session**
- **Search / Pagination** (`PageResult[T]`)
- **Bulk Update**
- **Transactions** (PostgreSQL via `session_scope()`)

---

## Factory

```python
from repositories.factory import get_repositories

repos = get_repositories()
session = repos.audit_session.get_by_id("session_abc")
```

`get_repositories()` is cached per process. Use `reset_repositories()` in tests.

---

## Implementations

| Module | Provider |
|--------|----------|
| `repositories/memory.py` | In-process dicts (production default for single-node dev) |
| `repositories/postgres.py` | SQLAlchemy 2.x + PostgreSQL |

Switching providers requires **zero service changes**:

```bash
DATABASE_PROVIDER=postgres
DATABASE_URL=postgresql+psycopg://gais:gais@127.0.0.1:5432/gais
```

---

## Store Adapters (unchanged API)

Existing services import stores directly:

```python
from services.audit_session_store import get_session, upsert_session
from services.comparison_store import save_result, get_result
from services.investigation_store import save_case, list_cases
from intelligence.intelligence_store import save_intelligence, get_intelligence
```

Stores delegate internally:

```python
def upsert_session(session: AuditSession) -> AuditSession:
    repos = get_repositories()
    ...
```

---

## Adding a New Repository

1. Define ABC in `repositories/interfaces.py`
2. Implement in `memory.py` and `postgres.py`
3. Register in `RepositoryBundle` + `factory.py`
4. Create store adapter or extend existing store
5. Add Alembic migration for new tables
6. Add tests in `tests/test_repository_memory.py` and `tests/test_repository_postgres.py`

---

## Related

- [DATABASE.md](./DATABASE.md)
- [ENTITY_RELATIONSHIP.md](./ENTITY_RELATIONSHIP.md)
- [BACKEND_ARCHITECTURE.md](./BACKEND_ARCHITECTURE.md)
