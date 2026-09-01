# GSTR-2A ↔ EWB Inward Plugin

Purchase verification plugin comparing merged **GSTR-2A** workbooks against merged **EWB Inward** workbooks.

## Routes

- `POST /api/comparison/gstr2a-eway` — enqueue comparison job
- `GET /api/plugins/gstr2a/report-section` — report section metadata

Merge for GSTR-2A remains at platform route `POST /api/merge/gstr2a`.

## Comparison ID

`gstr2a_ewb_inward`

## Files

| File | Role |
|------|------|
| `manifest.json` | Plugin contract |
| `plugin.py` | Registration |
| `routes.py` | HTTP endpoints |
| `comparison.py` | Comparator + job runner |
| `validators.py` | Workbook loaders |
| `intelligence.py` | Purchase observations |
| `report.py` | Purchase Reconciliation section |

Auto-discovered at startup — no platform changes required.
