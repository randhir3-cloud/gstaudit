# Testing

GAIS uses a three-layer testing strategy: backend unit/integration tests (pytest), frontend unit tests (Vitest), and end-to-end tests (Playwright).

## Backend (pytest)

**Location:** `backend/tests/`  
**Config:** `backend/pytest.ini`

```bash
cd backend
pip install -r requirements.txt
pytest                    # full suite
pytest -v --tb=short      # verbose
pytest tests/test_comparison_engine.py -k "gstr1"  # single module
```

### Test modules

| File | Coverage |
|------|----------|
| `test_comparison_engine.py` | Engine run, result shape |
| `test_comparison_matchers.py` | Invoice, GSTIN, value, date matchers |
| `test_comparison_normalizer.py` | Normalization edge cases |
| `test_comparison_risk_observations.py` | Risk scoring, observation text |
| `test_comparison_service.py` | Service orchestration, session apply |
| `test_dashboard_service.py` | Dashboard aggregation, readiness |
| `test_dealer_metadata_service.py` | GSTIN extraction |
| `test_eway_classification_service.py` | EWB direction classification |
| `test_eway_merge_service.py` | EWB merge workflow |
| `test_investigation_service.py` | Case sync, filters, updates |
| `test_intelligence_service.py` | Pattern detection, prioritization |
| `test_audit_report_service.py` | Report preview and generation |
| `test_report_export.py` | Legacy Excel/PDF export |
| `test_integration_samples.py` | Sample workbook integration |

### Fixtures

- `comparison_fixtures.py` — minimal GSTR-1 / EWB workbooks as bytes
- `eway_fixtures.py` — EWB classification samples

## Frontend (Vitest)

**Config:** `frontend/vitest.config.js`  
**Setup:** `frontend/src/test/setup.js`

```bash
cd frontend
npm install
npm run test
```

Current component tests:

- `components/DealerHeader.test.jsx`

Add Vitest tests for pure utilities (`formatNumbers.js`) and complex components when logic exceeds trivial rendering.

## End-to-End (Playwright)

**Location:** `e2e/`  
**Config:** `e2e/playwright.config.js`

```bash
cd e2e
npm install
npx playwright test                    # all specs, chromium
npx playwright test dashboard.spec.js  # single spec
npx playwright test --project=mobile   # viewport tests
npx playwright show-report ../docs/evidence/playwright-report
```

### Web servers (auto-started)

| Server | Command | URL |
|--------|---------|-----|
| Backend | `uvicorn main:app --host 127.0.0.1 --port 8000` | `:8000/docs` |
| Frontend | `npm run dev -- --host 127.0.0.1 --port 5173` | `:5173` |

`reuseExistingServer: true` — uses already-running dev servers when available.

### Spec files

| Spec | Coverage |
|------|----------|
| `dashboard.spec.js` | Header, dataset cards, FY calendar, duplicates, statistics, readiness, upload history |
| `dashboard-viewport.spec.js` | Tablet + mobile responsive layout |
| `comparison.spec.js` | Run comparison, summary, detail tables, discrepancy links |
| `investigation.spec.js` | Workbench, case remark, bulk verify, report export |
| `intelligence.spec.js` | Intelligence cards, patterns, investigation integration |
| `eway-classification.spec.js` | Outward/inward upload, wrong upload dialog, unknown rejection |

### Helpers

- `helpers/dashboardSession.js` — seed session via API for consistent dashboard state
- `helpers/visualStability.js` — wait for animations before screenshots

### Evidence output

- Screenshots: `docs/evidence/playwright-output/`
- HTML report: `docs/evidence/playwright-report/index.html`
- Curated screenshots: `docs/evidence/2026-07-09/*.png`

## Browser Verification (Agents)

Cursor agents use **IronBee DevTools** browser MCP for manual verification flows. Rules: `.cursor/rules/ironbee-devtools-use.mdc`

Flow: navigate → ARIA snapshot → interact → screenshot → check console errors.

## Definition of Done (Testing)

Per [PROJECT_RULES.md](./PROJECT_RULES.md):

1. Backend logic changes → pytest coverage for happy path + one error path
2. User-visible UI changes → Playwright spec update or new test case
3. All tests pass before merge

## CI Recommendations

```yaml
# Example pipeline stages
- cd backend && pytest
- cd frontend && npm run test && npm run lint
- cd e2e && npx playwright test --project=chromium
```

Set `CI=true` for Playwright retries (`retries: 1` in config).

## Related

- [DEPLOYMENT.md](./DEPLOYMENT.md)
- [PROJECT_RULES.md](./PROJECT_RULES.md)
