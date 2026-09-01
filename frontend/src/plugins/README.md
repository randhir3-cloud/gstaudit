# GAIS Plugin System

Platform-wide plugin architecture for GST modules. **Platform core is frozen** — new modules install under `plugins/`.

## Status

**Active** — see [PLUGIN_SDK.md](../docs/PLUGIN_SDK.md).

## Directory layout

```
plugins/
  gstr1/           # Reference plugin (GSTR-1 merge + comparison)
  gstr2a/          # Stub — copy gstr1 pattern
  gstr3b/          # Stub
  eway/            # Stub
  purchase/        # Stub
  sales/           # Stub
  analytics/       # Stub
  future/          # Experimental namespace
```

## Plugin manifest

Each plugin ships `manifest.json` + `plugin.py`:

```json
{
  "id": "gstr1",
  "name": "GSTR-1",
  "routes": ["/api/merge/gstr1", "/api/comparison/gstr1-eway"],
  "comparisons": [{ "comparison_id": "gstr1_ewb_outward", ... }],
  "datasets": { "gstr1": "GSTR-1" }
}
```

## Registration

- **Backend:** auto-discovered at startup via `backend/plugins/sdk/loader.py`
- **Frontend:** `GET /api/plugins` + `frontend/src/plugins/registry.js`

## Reference

- [ADR-010-PluginArchitecture.md](../docs/DECISIONS/ADR-010-PluginArchitecture.md)
- [PLUGIN_GUIDE.md](../docs/PLUGIN_GUIDE.md)
