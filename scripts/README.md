# Scripts

Utility and operational scripts for the **GST Audit** project.

- **Frontend**: React 19 + Vite (`/frontend`) → Deployed at `https://gstaudit.gkcircle.com`
- **Backend**: FastAPI + Python 3.11 (`/backend`) → Deployed at `https://api-gstaudit.gkcircle.com`
- **Database**: PostgreSQL (with SQLAlchemy + Alembic) or In-Memory provider
- **Platform**: Railway & Docker

---

## Script Inventory

| Script | Platform | Purpose | Example Usage |
|---|---|---|---|
| `update-project.ps1` | PowerShell | Verifies clean tree, pushes to `main` on GitHub, and optionally triggers Railway deployment | `.\scripts\update-project.ps1` (or `-SkipRailway`) |
| `railway.ps1` / `railway.sh` | Cross-Platform | Railway CLI helper for logs, status, redeploy, SSH, and migrations | `.\scripts\railway.ps1 status` / `./scripts/railway.sh logs backend` |
| `check-health.ps1` / `check-health.sh` | Cross-Platform | Checks health of backend (`/health`, `/api/system/health`) and frontend availability | `.\scripts\check-health.ps1` / `./scripts/check-health.sh` |

---

## Prerequisites

1. **Git**: Configured for `https://github.com/randhir3-cloud/gstaudit.git`
2. **Railway CLI** (Optional for CLI automation):
   ```bash
   npm i -g @railway/cli
   railway login
   railway link
   ```

---

## Railway Operations Quick Reference

### 1. Linking & Status
```powershell
# PowerShell
.\scripts\railway.ps1 link
.\scripts\railway.ps1 status

# Bash
./scripts/railway.sh link
./scripts/railway.sh status
```

### 2. View Real-time Logs
```powershell
# Stream backend logs
.\scripts\railway.ps1 logs backend

# Stream frontend logs
.\scripts\railway.ps1 logs frontend
```

### 3. SSH into Backend Container
```powershell
.\scripts\railway.ps1 ssh backend
```

### 4. Trigger Redeployments
```powershell
.\scripts\railway.ps1 redeploy backend
.\scripts\railway.ps1 redeploy frontend
```

### 5. Run Database Migrations (Alembic)
```powershell
.\scripts\railway.ps1 migrate
```

### 6. Verify Health
```powershell
.\scripts\railway.ps1 check
```

---

## Standard Git Deployment Workflow

1. Commit changes:
   ```bash
   git add .
   git commit -m "Your descriptive commit message"
   ```
2. Push & auto-deploy:
   ```powershell
   .\scripts\update-project.ps1
   ```
3. Monitor deployment status and logs:
   ```powershell
   .\scripts\railway.ps1 status
   .\scripts\railway.ps1 logs backend
   ```
4. Verify production health:
   ```powershell
   .\scripts\check-health.ps1
   ```

---

## Expected Production Environment Variables

### Backend (`gstaudit-backend`)
- `DATABASE_PROVIDER`: `postgres` (or `memory`)
- `DATABASE_URL`: `postgresql+psycopg://user:password@host:port/dbname`
- `CORS_ORIGINS`: `https://gstaudit.gkcircle.com,http://localhost:8081,http://localhost:5173`
- `JWT_SECRET`: Random 32+ character string
- `GAIS_ADMIN_USERNAME`: Default admin username (e.g. `admin`)
- `GAIS_ADMIN_PASSWORD`: Default admin initial password
- `PORT`: (Injected automatically by Railway, defaults to `8000`)

### Frontend (`gstaudit-frontend`)
- `VITE_API_BASE`: `https://api-gstaudit.gkcircle.com` (or proxied `/api` in local Docker/Vite)

---

## Security Guidelines

- **No hardcoded secrets**: All scripts read configuration from environment variables or Railway context.
- **Fail-safe**: Destructive scripts check for current git origin and linked project before running.
