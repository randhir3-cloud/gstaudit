# Folder Structure

Complete project tree for GAIS at `E:/gstaudit`. Generated from repository layout; excludes `node_modules`, `.git`, virtualenvs, binary artifacts, and Playwright trace caches.

```
gstaudit/
├── .cursor/
│   └── rules/
│       └── ironbee-devtools-use.mdc    # Browser verification rules for agents
├── backend/
│   ├── main.py                         # FastAPI entry — all HTTP routes
│   ├── merger.py                       # GSTR-1 / GSTR-2A Excel merge
│   ├── requirements.txt
│   ├── pytest.ini
│   ├── Dockerfile
│   ├── .dockerignore
│   ├── comparison/
│   │   ├── __init__.py
│   │   ├── bootstrap.py                # Comparator registration
│   │   ├── engine.py
│   │   ├── registry.py
│   │   ├── normalizer.py
│   │   ├── data_loader.py
│   │   ├── models.py
│   │   ├── result_models.py
│   │   ├── comparison_types.py
│   │   └── comparators/
│   │       ├── gstr1_vs_eway_outward.py
│   │       ├── gstr2a_vs_eway_inward.py
│   │       ├── invoice_matcher.py
│   │       ├── gstin_matcher.py
│   │       ├── value_matcher.py
│   │       ├── date_matcher.py
│   │       ├── duplicate_matcher.py
│   │       ├── summary_builder.py
│   │       ├── risk_engine.py
│   │       └── observation_generator.py
│   ├── intelligence/
│   │   ├── __init__.py
│   │   ├── intelligence_service.py
│   │   ├── intelligence_store.py
│   │   ├── pattern_detector.py
│   │   ├── case_prioritizer.py
│   │   ├── anomaly_detector.py
│   │   ├── timeline_builder.py
│   │   ├── executive_summary_generator.py
│   │   ├── recommendation_engine.py
│   │   ├── document_recommender.py
│   │   ├── risk_classifier.py
│   │   └── models.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── audit_session.py
│   │   ├── dealer_metadata.py
│   │   ├── investigation.py
│   │   ├── eway_classification.py
│   │   └── eway_merge.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── audit_session_store.py
│   │   ├── audit_report_service.py
│   │   ├── dashboard_service.py
│   │   ├── comparison_service.py
│   │   ├── comparison_store.py
│   │   ├── investigation_service.py
│   │   ├── investigation_store.py
│   │   ├── report_export.py
│   │   ├── dealer_metadata_service.py
│   │   ├── dealer_validation.py
│   │   ├── dealer_gstin_resolver.py
│   │   ├── eway_merge_service.py
│   │   ├── eway_classification_service.py
│   │   ├── eway_file_loader.py
│   │   ├── eway_errors.py
│   │   └── fy_months.py
│   └── tests/
│       ├── __init__.py
│       ├── comparison_fixtures.py
│       ├── eway_fixtures.py
│       ├── test_audit_report_service.py
│       ├── test_comparison_engine.py
│       ├── test_comparison_matchers.py
│       ├── test_comparison_normalizer.py
│       ├── test_comparison_risk_observations.py
│       ├── test_comparison_service.py
│       ├── test_dashboard_service.py
│       ├── test_dealer_metadata_service.py
│       ├── test_eway_classification_service.py
│       ├── test_eway_merge_service.py
│       ├── test_integration_samples.py
│       ├── test_intelligence_service.py
│       ├── test_investigation_service.py
│       └── test_report_export.py
├── frontend/
│   ├── index.html
│   ├── package.json
│   ├── package-lock.json
│   ├── vite.config.js
│   ├── vitest.config.js
│   ├── tailwind.config.js
│   ├── postcss.config.js
│   ├── .oxlintrc.json
│   ├── Dockerfile
│   ├── nginx.conf
│   ├── README.md
│   ├── public/
│   │   └── icons.svg
│   └── src/
│       ├── main.jsx
│       ├── App.jsx
│       ├── App.css
│       ├── index.css
│       ├── api/
│       │   ├── dashboard.js
│       │   ├── dealer.js
│       │   ├── eway.js
│       │   ├── comparison.js
│       │   ├── investigation.js
│       │   └── intelligence.js
│       ├── context/
│       │   ├── AuditSessionContext.jsx
│       │   ├── DealerContext.jsx
│       │   └── EwayContext.jsx
│       ├── types/
│       │   ├── auditSession.js
│       │   └── dealer.js
│       ├── utils/
│       │   ├── fileHelpers.js
│       │   └── formatNumbers.js
│       ├── pages/
│       │   ├── Dashboard.jsx
│       │   ├── MergePage.jsx
│       │   ├── WorkbookViewer.jsx
│       │   ├── ComparisonScreen.jsx
│       │   ├── InvestigationPage.jsx
│       │   └── AuditReportPreview.jsx
│       ├── components/
│       │   ├── Layout.jsx
│       │   ├── DealerHeader.jsx
│       │   ├── DealerHeader.test.jsx
│       │   ├── dashboard/          # 18 dashboard widgets
│       │   ├── merge/              # FileUploadZone, FileList
│       │   ├── eway/               # 7 EWB workflow components
│       │   └── investigation/      # 3 workbench components
│       └── test/
│           └── setup.js
├── e2e/
│   ├── package.json
│   ├── playwright.config.js
│   ├── dashboard.spec.js
│   ├── dashboard-viewport.spec.js
│   ├── comparison.spec.js
│   ├── investigation.spec.js
│   ├── intelligence.spec.js
│   ├── eway-classification.spec.js
│   ├── fixtures/
│   │   └── dealer_gstin.txt
│   ├── helpers/
│   │   ├── dashboardSession.js
│   │   └── visualStability.js
│   └── scripts/
│       └── diagnose-overlay.mjs
├── docs/
│   ├── ARCHITECTURE.md
│   ├── PROJECT_RULES.md
│   ├── FRONTEND_ARCHITECTURE.md
│   ├── BACKEND_ARCHITECTURE.md
│   ├── FOLDER_STRUCTURE.md         # this file
│   ├── UI_STANDARDS.md
│   ├── THEME_GUIDE.md
│   ├── STATE_MANAGEMENT.md
│   ├── COMPARISON_ENGINE.md
│   ├── INVESTIGATION_ENGINE.md
│   ├── AUDIT_INTELLIGENCE.md
│   ├── COMPONENT_LIBRARY.md
│   ├── API_REFERENCE.md
│   ├── DEPLOYMENT.md
│   ├── TESTING.md
│   ├── PERFORMANCE.md
│   ├── SECURITY.md
│   ├── ROADMAP.md
│   ├── CHANGELOG.md
│   ├── comparison-api.md           # legacy short API note
│   ├── evidence/                   # Playwright screenshots & reports
│   └── DECISIONS/
│       ├── ADR-001-Architecture.md
│       ├── ADR-002-Theme.md
│       ├── ADR-003-ComparisonEngine.md
│       ├── ADR-004-Investigation.md
│       ├── ADR-005-DataTable.md
│       └── ADR-006-ShadcnAdoption.md
├── scripts/
│   └── update-project.ps1
├── docker-compose.yml
├── docker-compose.nuc.yml
├── GSTR 1/                         # Sample GSTR-1 test workbooks
└── Ujjwal SMall bank/              # Sample taxpayer data (local only)
```

## Key Conventions

| Path pattern | Meaning |
|--------------|---------|
| `backend/services/*_store.py` | In-memory persistence (v0.1) |
| `backend/tests/test_*.py` | pytest unit/integration tests |
| `frontend/src/api/*.js` | One module per backend domain |
| `frontend/src/components/{feature}/` | Feature-scoped UI components |
| `e2e/*.spec.js` | Playwright end-to-end tests |
| `docs/evidence/` | Visual regression and manual test artifacts |

## Not in Repository

- `node_modules/` — install via `npm install` in `frontend/` and `e2e/`
- Python virtual environment — create locally; `backend/requirements.txt` lists deps
- Production secrets — never committed
