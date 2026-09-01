# GAIS Database Guide

PostgreSQL persistence for GAIS v0.5+. Services remain database-independent via the repository layer.

---

## Provider Selection

| Variable | Values | Default |
|----------|--------|---------|
| `DATABASE_PROVIDER` | `memory`, `postgres` | `memory` |
| `DATABASE_URL` | SQLAlchemy URL | `postgresql+psycopg://gais:gais@127.0.0.1:5432/gais` |
| `DATABASE_ECHO` | `true` / `false` | `false` |

```bash
# Development (in-memory — no setup)
DATABASE_PROVIDER=memory uvicorn main:app --reload

# Production (PostgreSQL)
DATABASE_PROVIDER=postgres
DATABASE_URL=postgresql+psycopg://gais:gais@postgres:5432/gais
```

---

## Stack

| Component | Version | Purpose |
|-----------|---------|---------|
| PostgreSQL | 16+ | Primary datastore |
| SQLAlchemy | 2.x | ORM |
| Alembic | 1.13+ | Schema migrations |
| psycopg | 3.x | PostgreSQL driver |

ORM models: `backend/db/orm/models.py`  
Mappers (Pydantic ↔ ORM): `backend/db/mappers.py`

---

## Schema Overview

| Table | Purpose |
|-------|---------|
| `dealers` | Dealer identity (GSTIN + FY unique) |
| `audit_sessions` | Session aggregate + JSONB payload |
| `uploaded_files` | Upload history rows |
| `merged_datasets` | Cached workbook bytes per dataset |
| `comparison_runs` | Comparison execution metadata |
| `comparison_results` | Individual discrepancy records (indexed) |
| `audit_observations` | Officer guidance observations |
| `investigation_cases` | Investigation workbench cases |
| `audit_reports` | Generated report cache (optional) |
| `intelligence_results` | Intelligence analysis cache |
| `system_settings` | Key-value configuration |

See [ENTITY_RELATIONSHIP.md](./ENTITY_RELATIONSHIP.md) for relationships and indexes.

---

## Migrations

```bash
cd backend

# Start PostgreSQL (Docker)
docker compose up -d postgres

# Apply migrations
DATABASE_URL=postgresql+psycopg://gais:gais@127.0.0.1:5432/gais alembic upgrade head

# Rollback one revision
alembic downgrade -1

# Generate new migration (after ORM changes)
alembic revision --autogenerate -m "description"
```

Initial migration: `alembic/versions/001_initial_schema.py`

---

## Performance Indexes

Indexes are defined on:

- **Session:** `audit_sessions.session_id`, `financial_year`, `audit_status`
- **GSTIN:** `dealers.gstin`, `investigation_cases.supplier_gstin`
- **Invoice:** `comparison_results.normalized_invoice`, `investigation_cases.invoice_number`
- **Month:** `uploaded_files.month`, `comparison_results.source_period`
- **Financial year:** `dealers.financial_year`, `audit_sessions.financial_year`
- **Risk:** `comparison_results.risk_score`, `investigation_cases.priority`
- **Case status:** `investigation_cases.status`

---

## Docker Compose

```bash
# PostgreSQL only
docker compose up -d postgres

# Full stack with postgres backend
DATABASE_PROVIDER=postgres docker compose up -d
```

---

## Testing

```bash
# Memory repositories (default, no DB)
pytest tests/test_repository_memory.py

# PostgreSQL repositories (requires running Postgres)
TEST_DATABASE_URL=postgresql+psycopg://gais:gais@127.0.0.1:5432/gais_test pytest -m postgres
```

---

## Related

- [REPOSITORY_PATTERN.md](./REPOSITORY_PATTERN.md)
- [ENTITY_RELATIONSHIP.md](./ENTITY_RELATIONSHIP.md)
- [DECISIONS/ADR-007-DatabaseSelection.md](./DECISIONS/ADR-007-DatabaseSelection.md)
