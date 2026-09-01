# ADR-012: Feature Module Structure

## Status

Proposed

## Context

Frontend is organized by file type (`pages/`, `components/`, `api/`). As modules grow, cross-cutting changes touch many unrelated folders.

## Decision

Migrate to **feature-first** layout:

```
features/
  dashboard/
    pages/
    components/
    hooks/
    columns/
  comparison/
  investigation/
  ...
  shared/
    components/
    hooks/
    theme/
```

`src/pages/` becomes route re-exports only during transition.

## Migration strategy

1. New code goes in `features/`
2. Move one module per release (dashboard first)
3. Update imports incrementally; no big-bang rename

## Consequences

- Clearer ownership boundaries
- Easier plugin alignment (ADR-010)
- Temporary duplicate paths during migration

## References

- [FRONTEND_ARCHITECTURE.md](../FRONTEND_ARCHITECTURE.md)
- [PRE_V1_ROADMAP.md](../PRE_V1_ROADMAP.md) §12
