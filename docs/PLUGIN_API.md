# GAIS Plugin API Reference

## PluginContext (`ctx`)

Available in `register(registry, ctx)`:

| Member | Description |
|--------|-------------|
| `ctx.settings` | Application settings (`config.settings`) |
| `ctx.repositories` | Repository bundle (sessions, dealers, comparisons, …) |
| `ctx.comparisons` | `ComparisonRegistry` — register comparators |
| `ctx.get_session(session_id)` | Load audit session |
| `ctx.upsert_session(session)` | Persist audit session |
| `ctx.create_job(request)` | Enqueue background job |
| `ctx.cache_workbook(session_id, key, bytes)` | Cache merged workbook |
| `ctx.get_workbook(session_id, key)` | Read cached workbook |
| `ctx.build_dashboard(session)` | Build dashboard response |
| `ctx.log_audit(user, action, **kwargs)` | Security audit log entry |

## PluginRegistry (`registry`)

| Method | Description |
|--------|-------------|
| `register_manifest(manifest)` | Called by loader from `manifest.json` |
| `add_router(router)` | Mount FastAPI routes on the app |
| `register_comparison_runner(id, fn)` | Background job comparison executor |
| `register_merge_handler(dataset_key, fn)` | Optional merge dispatch |
| `register_validator(name, fn)` | Optional validation hook |
| `register_upload_handler(key, fn)` | Optional upload hook |
| `get_comparison_runner(id)` | Resolve runner for job executor |
| `public_catalog()` | JSON catalog for `GET /api/plugins` |

## Comparison runner signature

```python
def run_comparison_with_progress(
    session_id: str,
    *,
    gstr1_workbook_base64: str = "",
    ewb_outward_workbook_base64: str = "",
    progress_callback=None,
    checkpoint=None,
    job_id=None,
) -> ComparisonResult:
    ...
```

Plugins may define additional payload keys; job executor passes the full payload as kwargs where compatible.

## HTTP catalog

### `GET /api/plugins`

Returns:

```json
{
  "plugins": [ { "id": "gstr1", "name": "GSTR-1", ... } ],
  "datasets": { "gstr1": "GSTR-1" },
  "comparison_pairs": [ { "comparison_id": "gstr1_ewb_outward", ... } ],
  "navigation": [],
  "dashboard_cards": [ { "dataset_key": "gstr1", ... } ]
}
```

Requires authentication (`view_dashboard` permission).

## Platform services plugins must not modify

- `backend/main.py` (except existing plugin hooks)
- Dashboard, Jobs, Security, Database layers
- Authentication middleware

All GST-specific logic belongs in `plugins/<module>/`.
