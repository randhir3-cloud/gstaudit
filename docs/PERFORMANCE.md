# Performance

Performance characteristics and optimization guidance for GAIS v0.1.

## Workload Profile

| Operation | Dominant cost | Typical input size |
|-----------|---------------|-------------------|
| GSTR merge | pandas + openpyxl I/O | 12 monthly files, ~5–50k rows |
| EWB merge | pandas + sheet parsing | Multi-sheet outward/inward |
| Comparison | In-memory record matching | 1k–100k invoice records |
| Intelligence | Python loops over records | Same as comparison output |
| Report generation | reportlab / python-docx / openpyxl | Hundreds of cases |

## Backend

### Excel processing

- **pandas** reads workbooks into DataFrames — memory scales with row × column count
- Merge operations concatenate monthly files — peak memory ≈ 2× final workbook size during processing
- Recommendation: 512 MB–1 GB RAM minimum per backend instance for typical FY audits

### Comparison engine

- Invoice index: `O(n)` build + `O(n)` scan — linear in record count
- Duplicate detection: hash set on normalized keys
- Pagination on details endpoint: `offset/limit` prevents loading all records in one HTTP response (default limit 100, max 1000)

### In-memory stores

Session, comparison, investigation, and intelligence stores are Python dicts — fast reads, no serialization overhead, but **not durable** and **not shared across workers**.

### Caching

- `comparison_store` caches uploaded workbook bytes per session/dataset
- `intelligence_store` caches analysis — recomputation skipped on subsequent `/api/intelligence` calls
- Frontend debounces session sync (400 ms) to reduce write churn

## Frontend

### Bundle

- Vite production build with tree-shaking
- Dependencies: React 19, lucide-react (icon subset imported per file), Tailwind (purged unused classes)
- No heavy charting library in v0.1

### Runtime

- Dashboard renders ~20 child components — avoid unnecessary `refreshDashboard()` calls
- Workbook blobs held in EwayContext memory — release on workflow reset
- localStorage session JSON typically < 100 KB

### Network

- Merged workbooks transferred as base64 in JSON for EWB merge responses — ~33% overhead vs binary; acceptable for v0.1
- Comparison can use cached workbooks server-side to avoid re-upload
- Report downloads are streaming responses

## Playwright / E2E

- `workers: 1` — sequential tests avoid session store races
- `timeout: 60_000` — allows merge + comparison flows
- `fullyParallel: false` — shared backend state

## Known Bottlenecks

1. **Large Excel files (>20 MB)** — upload and parse time dominates; no chunked upload
2. **First intelligence run** — full pattern scan on all discrepancy records
3. **Investigation list sync** — re-syncs cases from comparison on every list request
4. **No database index** — linear scan for case filters (acceptable at hundreds of cases)

## Optimization Roadmap

| Priority | Improvement |
|----------|-------------|
| High | Persist comparison results in SQLite/Postgres with indexed filters |
| High | Incremental intelligence — recompute only changed records |
| Medium | Binary workbook transfer (multipart) instead of base64 JSON |
| Medium | Background job queue for comparison on large datasets |
| Low | Virtualized tables in investigation workbench for 10k+ rows |
| Low | Web Worker for client-side workbook preview parsing |

## Monitoring Recommendations

For production deployments, track:

- P95 latency: `/api/merge/*`, `/api/comparison/gstr1-eway`, `/api/report/generate`
- Memory usage of uvicorn workers during merge
- Upload size distribution (413 errors)
- Comparison record counts per session

## Related

- [ARCHITECTURE.md](./ARCHITECTURE.md)
- [ROADMAP.md](./ROADMAP.md)
- [DEPLOYMENT.md](./DEPLOYMENT.md)
