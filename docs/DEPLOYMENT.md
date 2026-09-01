# Deployment

Guide for running GAIS in development and production environments.

## Prerequisites

| Requirement | Version |
|-------------|---------|
| Node.js | 22+ (frontend build) |
| Python | 3.11+ |
| Docker & Docker Compose | Optional, recommended for production |
| npm | For frontend and e2e packages |

## Local Development

### Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

Verify: `curl http://127.0.0.1:8000/health`

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Opens at `http://127.0.0.1:5173`. API calls default to `http://127.0.0.1:8000` unless `VITE_API_BASE` is set.

### Environment Variables

| Variable | Location | Purpose |
|----------|----------|---------|
| `VITE_API_BASE` | frontend `.env` | Override API URL for Vite dev |

Create `frontend/.env.local`:

```
VITE_API_BASE=http://127.0.0.1:8000
```

## Docker Compose (Production-style)

**File:** `docker-compose.yml`

```bash
docker compose up --build
```

| Service | Container | Host port | Internal |
|---------|-----------|-----------|----------|
| backend | gstaudit-backend | 8001 | 8000 |
| frontend | gstaudit-frontend | 8081 | 80 |

Access UI: `http://localhost:8081`

### Nginx API Proxy

`frontend/nginx.conf` proxies:

- `/api/*` → `http://backend:8000/api/`
- `/health` → backend health check

`client_max_body_size 50m` supports large Excel uploads.

### Alternate Compose

`docker-compose.nuc.yml` — variant for low-resource deployments (Intel NUC). Adjust resource limits as needed for your hardware.

## Build Artifacts

### Frontend production build

```bash
cd frontend
npm run build
# Output: frontend/dist/
npm run preview  # local preview of dist
```

Multi-stage `frontend/Dockerfile`:

1. Node 22 Alpine — `npm install && npm run build`
2. Nginx Alpine — serves `dist/`

### Backend image

`backend/Dockerfile` — Python 3.11-slim, installs requirements, runs uvicorn on `0.0.0.0:8000`.

## Deployment Checklist

- [ ] Set restrictive CORS origins in `main.py` (not `*`)
- [ ] Place authentication gateway in front of UI/API
- [ ] Configure HTTPS termination (reverse proxy / load balancer)
- [ ] Set `client_max_body_size` appropriately for max upload size
- [ ] Plan persistent storage for sessions (v0.1 is in-memory — see ROADMAP)
- [ ] Run health check: `GET /health` via frontend port
- [ ] Run smoke E2E or manual dashboard load test

## CI / Verification

E2E suite auto-starts both servers (`e2e/playwright.config.js`):

```bash
cd e2e
npm install
npx playwright test
```

Reports: `docs/evidence/playwright-report/index.html`

## Updating Production

```powershell
# scripts/update-project.ps1 — project-specific update script
docker compose down
git pull
docker compose up --build -d
```

Verify backend: `curl http://localhost:8081/health`

## Scaling Notes (v0.1)

- **Single instance only** — in-memory stores do not share state across replicas
- For horizontal scaling, implement shared database-backed stores first (see [ROADMAP.md](./ROADMAP.md))
- Comparison and merge are CPU/IO bound — allocate adequate memory for pandas operations

## Troubleshooting

| Issue | Check |
|-------|-------|
| CORS errors in dev | Backend running on 8000; `VITE_API_BASE` correct |
| 413 upload failed | Nginx `client_max_body_size` |
| Empty dashboard | Session not synced — upload + merge on Merge page |
| API 404 behind Docker | Frontend nginx proxy config; backend container name `backend` |
| Comparison fails | Both GSTR-1 and EWB outward merged for session |

## Related

- [SECURITY.md](./SECURITY.md)
- [TESTING.md](./TESTING.md)
- [ARCHITECTURE.md](./ARCHITECTURE.md)
