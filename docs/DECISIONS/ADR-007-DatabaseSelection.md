# ADR-007: Database Selection

## Status

Accepted (implemented v0.5.0)

## Context

GAIS v0.1–v0.2 uses in-memory Python dicts for sessions, comparisons, investigations, and intelligence. This is acceptable for single-instance dev but blocks durability, horizontal scaling, and audit trails required for v1.0.

## Options

| Option | Pros | Cons |
|--------|------|------|
| **SQLite** | Zero-config, file-based, Alembic-friendly | Single-writer, weak multi-instance |
| **PostgreSQL** | ACID, JSONB, full-text, replication | Ops overhead, requires connection pool |
| **Hybrid SQLite → PG** | Fast local dev | Two code paths if not careful |

## Decision (recommended)

**PostgreSQL** for production; **SQLite** optional for offline/single-officer installs via env flag.

## Consequences

- Introduce SQLAlchemy 2.0 + Alembic migrations
- Repository layer abstracts store implementation
- Session/comparison/case tables with GSTIN + FY indexes

## References

- [BACKEND_ARCHITECTURE.md](../BACKEND_ARCHITECTURE.md)
- [PRE_V1_ROADMAP.md](../PRE_V1_ROADMAP.md) Phase G
