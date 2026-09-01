# ADR-005: Unified DataTable Component

## Status

Accepted (2026-07-09)

## Context

GAIS had multiple inline table implementations (`ComparisonRecordsTable`, dashboard upload history, e-way validation tables) with duplicated sorting, pagination, and search logic.

## Decision

Introduce a single reusable `DataTable` at `frontend/src/components/common/DataTable.jsx` with:

- Column configuration via props
- Built-in search, sort, pagination
- Sticky header
- Row selection and click handlers
- Shared hooks: `useSearch`, `useSorting`, `usePagination`

Domain-specific tables (e.g. `ComparisonRecordsTable`) become thin wrappers that define columns only.

## Consequences

**Positive**

- One place to add virtual scroll, export, column visibility later
- E2E test IDs preserved via `testIdPrefix`
- Consistent table styling via `theme/tables.js`

**Negative**

- Highly custom tables may still need bespoke markup
- Virtual scroll not yet implemented (see PERFORMANCE.md)

## References

- `frontend/src/components/common/DataTable.jsx`
- `frontend/src/components/investigation/ComparisonRecordsTable.jsx`
- `docs/COMPONENT_LIBRARY.md`
