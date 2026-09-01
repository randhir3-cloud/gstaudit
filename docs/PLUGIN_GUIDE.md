# GAIS Plugin Authoring Guide

## Quick start

1. Create `plugins/my_module/manifest.json`
2. Create `plugins/my_module/plugin.py` with a `register(registry, ctx)` function
3. Optionally add `routes.py` with a FastAPI `APIRouter`
4. Restart the backend — the loader discovers the plugin automatically

No changes to Dashboard, Jobs, Security, Database, or platform routes are required.

## manifest.json

```json
{
  "id": "gstr2a",
  "name": "GSTR-2A",
  "version": "1.0.0",
  "author": "Your Department",
  "description": "GSTR-2A merge and inward comparison",
  "required_permissions": ["merge_files", "run_comparison"],
  "routes": ["/api/merge/gstr2a"],
  "datasets": { "gstr2a": "GSTR-2A" },
  "comparisons": [],
  "jobs": [],
  "reports": [],
  "navigation": [],
  "settings": {}
}
```

## plugin.py

```python
from routes import router

def register(registry, ctx):
    registry.add_router(router)
    registry.register_merge_handler("gstr2a", my_merge_fn)
```

## Routes

Use the same URL paths the frontend already expects, or add new paths and register navigation in the manifest.

Import shared helpers from `gais_platform.http_helpers` when running inside the backend process.

## Comparisons

```python
from comparison.models import ComparisonConfig

config = ComparisonConfig(
    comparison_id="gstr2a_ewb_inward",
    left_dataset="gstr2a",
    right_dataset="ewb_inward",
    left_label="GSTR-2A",
    right_label="EWB INWARD",
)
ctx.comparisons.register("gstr2a_ewb_inward", config, my_comparator_fn)
registry.register_comparison_runner("gstr2a_ewb_inward", my_runner_with_progress)
```

Job payloads must include `"comparison_id": "gstr2a_ewb_inward"`.

## Permissions

List required permissions in `manifest.json`. Map routes in `settings.audit_actions` for audit logging.

## Testing

Add tests under `backend/tests/` that call `ensure_plugins_loaded()` and assert registry state. Keep E2E paths unchanged for migrated modules.

## Checklist before shipping

- [ ] `manifest.json` validates against `PluginManifest`
- [ ] `register()` is idempotent-safe (loader calls once per process)
- [ ] Routes match existing frontend API clients or manifest documents new ones
- [ ] Comparison IDs and dataset keys are stable across releases
- [ ] Pytest and Playwright pass with no core platform edits
