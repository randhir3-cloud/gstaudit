# Purchase Register Plugin

Reconciles dealer **Purchase Register** against **GSTR-2A** and **EWB Inward**, publishing findings into MSAE via the standard comparison result store.

## Features

- Smart import with template detection (Tally, Busy, Marg, generic GST)
- Column mapping UI at `GET /api/purchase/ui`
- Saved mapping profiles (`GET/POST /api/purchase/mapping-profiles`)
- Comparisons:
  - `purchase_register_vs_gstr2a`
  - `purchase_register_vs_ewb_inward`
- Report section: **Purchase Register Reconciliation**

## API Routes

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/purchase/ui` | Import workbench (HTML) |
| POST | `/api/purchase/import/preview` | Auto-detect columns |
| POST | `/api/purchase/import` | Import normalized workbook into session |
| GET/POST | `/api/purchase/mapping-profiles` | List/save mapping profiles |
| POST | `/api/comparison/purchase-gstr2a` | Enqueue PR ↔ GSTR-2A job |
| POST | `/api/comparison/purchase-ewb` | Enqueue PR ↔ EWB Inward job |
| GET | `/api/plugins/purchase/report-section` | Report section metadata |

## Registration

Auto-discovered from `manifest.json` + `plugin.py` — no platform changes required.

## Tests

```bash
cd backend && pytest tests/test_purchase_plugin.py -v
cd e2e && npx playwright test purchase-plugin.spec.js
```
