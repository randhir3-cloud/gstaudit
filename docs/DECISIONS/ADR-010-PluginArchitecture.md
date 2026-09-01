# ADR-010: Plugin Architecture

## Status

Proposed

## Context

GAIS comparison engine already uses a **registry** (`backend/comparison/registry.py`). Adding GSTR-3B, purchase register, or TDS modules today requires editing `main.py`, routes, dashboard cards, and sidebar manually.

## Decision

Extend registry pattern to a **platform plugin system**:

```
plugins/
  {module_id}/
    manifest.json      # id, name, routes, comparators, cards
    routes.py          # FastAPI router
    comparator.py      # optional
    frontend/          # pages, columns, cards (or JS manifest)
```

Frontend plugin manifest registers:

- Route paths
- Sidebar items
- Dashboard card components
- Column definition modules
- Report sections

Backend plugin manifest registers:

- Comparator classes
- Validators
- Report data providers

## Consequences

**Positive:** New GST module = new plugin folder + manifest, not app rewrite.

**Negative:** Plugin API versioning and sandboxing needed before third-party plugins.

## References

- [COMPARISON_ENGINE.md](../COMPARISON_ENGINE.md)
- [PRE_V1_ROADMAP.md](../PRE_V1_ROADMAP.md) §13
