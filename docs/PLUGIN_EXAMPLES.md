# GAIS Plugin Examples

## Example 1 — Reference plugin (GSTR-1)

Location: `plugins/gstr1/`

```
plugins/gstr1/
  manifest.json    # id, datasets, comparisons, routes
  plugin.py        # register comparators + job runner + router
  routes.py        # POST /api/merge/gstr1, POST /api/comparison/gstr1-eway
```

The GSTR-1 plugin registers:

- Comparator `gstr1_ewb_outward` on the platform comparison registry
- Job runner for background comparison jobs
- HTTP routes at unchanged paths

## Example 2 — Minimal stub plugin

`plugins/analytics/manifest.json`:

```json
{
  "id": "analytics",
  "name": "Audit Analytics",
  "version": "0.1.0",
  "description": "Cross-module KPIs",
  "required_permissions": ["view_dashboard"],
  "routes": ["/api/analytics/summary"],
  "datasets": {},
  "comparisons": [],
  "jobs": [],
  "reports": [],
  "navigation": [
    { "label": "Analytics", "path": "/analytics", "permission": "view_dashboard" }
  ]
}
```

`plugins/analytics/plugin.py`:

```python
from fastapi import APIRouter

router = APIRouter()

@router.get("/api/analytics/summary")
async def analytics_summary():
    return {"status": "ok", "modules": 4}

def register(registry, ctx):
    registry.add_router(router)
```

## Example 3 — GSTR-2A plugin (implemented)

Location: `plugins/gstr2a/`

Compares merged GSTR-2A against EWB Inward for purchase verification.

- Comparison ID: `gstr2a_ewb_inward`
- Trigger: `POST /api/comparison/gstr2a-eway`
- Report section: **Purchase Reconciliation**
- Investigation cases created automatically via platform `sync_cases_from_comparison`

## Example 4 — GSTR-2A migration pattern

To migrate GSTR-2A without platform changes:

1. Copy `plugins/gstr1/` → `plugins/gstr2a/`
2. Update manifest datasets and comparison pair to `gstr2a_ewb_inward`
3. Move `POST /api/merge/gstr2a` from `main.py` into `plugins/gstr2a/routes.py`
4. Register comparator from `comparison/comparators/gstr2a_vs_eway_inward.py`
5. Remove the route from `main.py` only — no dashboard or security edits

## Example 4 — Frontend catalog consumption

```javascript
import { loadPluginCatalog } from '../plugins/registry';

const catalog = await loadPluginCatalog();
const pairs = catalog.comparison_pairs;
// [{ comparison_id: 'gstr1_ewb_outward', label: 'GSTR-1 ↔ EWB OUTWARD', ... }]
```

## Example 5 — Job payload with comparison_id

```python
from models.job import JobCreateRequest, JobType
from services.job_service import create_job

create_job(JobCreateRequest(
    session_id=session_id,
    job_type=JobType.COMPARISON,
    title="My comparison",
    payload={
        "comparison_id": "gstr1_ewb_outward",
        "gstr1_workbook_base64": "...",
        "ewb_outward_workbook_base64": "...",
    },
))
```

The job executor resolves the runner from `plugin_registry.get_comparison_runner(comparison_id)`.
