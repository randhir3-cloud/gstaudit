#!/usr/bin/env bash
# Railway Management Helper for GST Audit (Linux/macOS)
#
# Operations:
#   ./scripts/railway.sh link
#   ./scripts/railway.sh status
#   ./scripts/railway.sh logs [frontend|backend]
#   ./scripts/railway.sh redeploy [frontend|backend]
#   ./scripts/railway.sh ssh [backend]
#   ./scripts/railway.sh migrate
#   ./scripts/railway.sh check
#   ./scripts/railway.sh up

set -euo pipefail

COMMAND="${1:-status}"
TARGET="${2:-backend}"

FRONTEND_SERVICE="${RAILWAY_FRONTEND_SERVICE:-gstaudit-frontend}"
BACKEND_SERVICE="${RAILWAY_BACKEND_SERVICE:-gstaudit-backend}"

get_service_name() {
  if [[ "$1" == *"front"* ]]; then
    echo "$FRONTEND_SERVICE"
  else
    echo "$BACKEND_SERVICE"
  fi
}

if ! command -v railway &>/dev/null; then
  echo "Error: Railway CLI is not installed. Run: npm i -g @railway/cli"
  exit 1
fi

case "$COMMAND" in
  link)
    echo "=== Linking Railway Project for GST Audit ==="
    railway link
    ;;
  status)
    echo "=== Railway Project Status ==="
    railway status
    ;;
  logs)
    SVC=$(get_service_name "$TARGET")
    echo "=== Streaming logs for service '$SVC' ==="
    railway logs --service "$SVC"
    ;;
  redeploy)
    SVC=$(get_service_name "$TARGET")
    echo "=== Triggering redeployment for service '$SVC' ==="
    railway redeploy --service "$SVC" --yes
    ;;
  ssh)
    SVC=$(get_service_name "$TARGET")
    echo "=== Connecting SSH shell to service '$SVC' ==="
    railway ssh --service "$SVC"
    ;;
  migrate)
    echo "=== Running Alembic database migrations on '$BACKEND_SERVICE' ==="
    railway run --service "$BACKEND_SERVICE" -- alembic upgrade head
    ;;
  up)
    echo "=== Deploying local repository changes to Railway ==="
    railway up --ci
    ;;
  check)
    echo "=== Running Health Checks for GST Audit ==="
    bash "$(dirname "$0")/check-health.sh"
    ;;
  *)
    echo "Unknown command: $COMMAND"
    echo "Usage: $0 [link|status|logs|redeploy|ssh|migrate|up|check] [frontend|backend]"
    exit 1
    ;;
esac
