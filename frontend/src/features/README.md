# Feature Modules

Target structure for frontend organization before v1.0.

**Status:** Comparison and Investigation migrated (v0.4.0). New code should prefer `features/` over flat `pages/` + `components/`.

```
features/
  dashboard/       # FY calendar, readiness, dataset cards
  comparison/      # GSTR-1 vs EWB and future pairs
  investigation/   # Case workbench
  audit/           # Intelligence panel
  reports/         # Preview + export
  dealer/          # GSTIN header, validation
  merge/           # GSTR merge workflows
  eway/            # EWB classification + merge
  shared/          # theme, layout, DataTable, badges
```

Each feature owns:

- `pages/` — route entry components
- `components/` — feature-specific UI
- `hooks/` — feature hooks (may re-export from `src/hooks/`)
- `columns/` — DataTable column defs (may re-export from `src/columns/`)

Migration tracked in [PRE_V1_ROADMAP.md](../docs/PRE_V1_ROADMAP.md) Phase E.

See [ADR-012-FeatureModules.md](../docs/DECISIONS/ADR-012-FeatureModules.md).
