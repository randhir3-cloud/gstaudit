# ADR-013: Virtual DataTable Implementation

## Status

Proposed

## Context

v0.2 `DataTable` paginates in memory — fine for investigation cases (<10k) but insufficient for workbook views at 500k+ rows.

## Options

| Library | Pros | Cons |
|---------|------|------|
| **TanStack Virtual** | Headless, works with existing table | Manual column sync |
| **TanStack Table + Virtual** | Full table features | Heavier bundle |
| **AG Grid** | Enterprise features | License, weight |

## Decision (recommended)

**TanStack Table v8 + TanStack Virtual** inside `components/ui/DataTable.jsx` wrapper. Keep column definition pattern from `columns/`.

## Requirements

- Sticky header + optional sticky first column
- Server-side sort/filter/pagination for workbook mode
- Client-side mode for investigation mode
- Export streams CSV without loading all rows into DOM

## Consequences

- Two DataTable modes: `client` | `server`
- Performance benchmarks in CI (see TESTING.md)

## References

- [ADR-005-DataTable.md](./ADR-005-DataTable.md)
- [PERFORMANCE.md](../PERFORMANCE.md)
