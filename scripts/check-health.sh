#!/usr/bin/env bash
# Health verification script for GST Audit Production & Local deployments (Linux/macOS)
#
# Usage:
#   ./scripts/check-health.sh
#   FRONTEND_URL="http://localhost:8081" BACKEND_URL="http://localhost:8001" ./scripts/check-health.sh

FRONTEND_URL="${FRONTEND_URL:-https://gstaudit.gkcircle.com}"
BACKEND_URL="${BACKEND_URL:-https://api-gstaudit.gkcircle.com}"

echo "=========================================="
echo " GST Audit - Deployment Health Check "
echo " Frontend: $FRONTEND_URL"
echo " Backend:  $BACKEND_URL"
echo "=========================================="

FAILED=0

# 1. Backend Core Health
echo -n "[1/3] Checking Backend Health ($BACKEND_URL/health)... "
HEALTH_RESP=$(curl -s -m 10 "$BACKEND_URL/health" || true)
if echo "$HEALTH_RESP" | grep -q '"status":\s*"healthy"'; then
  echo "[PASS]"
else
  echo "[FAIL] - Response: $HEALTH_RESP"
  FAILED=1
fi

# 2. Backend System Monitor Health
echo -n "[2/3] Checking Backend System Status ($BACKEND_URL/api/system/health)... "
SYS_RESP=$(curl -s -m 10 "$BACKEND_URL/api/system/health" || true)
if echo "$SYS_RESP" | grep -q '"application":\s*"healthy"'; then
  echo "[PASS]"
else
  echo "[WARN/FAIL] - Response: $SYS_RESP"
  FAILED=1
fi

# 3. Frontend Availability
echo -n "[3/3] Checking Frontend Availability ($FRONTEND_URL)... "
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -m 10 "$FRONTEND_URL" || true)
if [ "$HTTP_CODE" = "200" ]; then
  echo "[PASS] (HTTP 200)"
else
  echo "[FAIL] (HTTP $HTTP_CODE)"
  FAILED=1
fi

echo "=========================================="
if [ $FAILED -eq 0 ]; then
  echo " All Health Checks PASSED"
  exit 0
else
  echo " Health Check finished with FAILURES"
  exit 1
fi
