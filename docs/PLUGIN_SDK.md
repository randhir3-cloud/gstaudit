# GAIS Plugin SDK

The GAIS platform is **frozen**. New GST modules ship as plugins under `plugins/` at the repository root.

## Architecture

```
plugins/                    ← install modules here (no core edits)
  gstr1/                    ← reference plugin (manifest + plugin.py + routes)
  gstr2a/                   ← stub
  eway/
  ...

backend/plugins/sdk/        ← platform extension layer (do not modify for GST features)
  manifest.py               ← PluginManifest schema
  registry.py               ← PluginRegistry
  loader.py                 ← auto-discovery at startup
  context.py                ← PluginContext API
```

## Plugin contract

Every plugin provides:

| Export | Required | Description |
|--------|----------|-------------|
| `manifest.json` | Yes | Declarative metadata |
| `plugin.py` → `register(registry, ctx)` | Yes | Runtime registration |
| `routes.py` | Optional | FastAPI router |
| Comparators | Optional | Via `ctx.comparisons.register()` |
| Job runners | Optional | Via `registry.register_comparison_runner()` |

## Startup flow

1. `main.py` calls `ensure_plugins_loaded()` in lifespan
2. `load_plugins(app)` mounts plugin routers
3. Each plugin's `register()` adds comparators, routes, and job handlers

## Reference plugin

See `plugins/gstr1/` — GSTR-1 merge and GSTR-1 ↔ EWB comparison. Platform behavior is identical to pre-plugin wiring; routes remain at the same URLs.

## Documentation

- [PLUGIN_GUIDE.md](./PLUGIN_GUIDE.md) — authoring walkthrough
- [PLUGIN_API.md](./PLUGIN_API.md) — `PluginContext` and registry API
- [PLUGIN_EXAMPLES.md](./PLUGIN_EXAMPLES.md) — copy-paste templates

## Frontend

`GET /api/plugins` returns the public catalog. Use `frontend/src/plugins/registry.js` to load manifests in the UI.
