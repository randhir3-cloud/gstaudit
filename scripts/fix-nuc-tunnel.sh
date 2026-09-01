#!/usr/bin/env bash
# Run ON the NUC when gstaudit.gkcircle.com shows Cloudflare Error 1033
# Usage: bash ~/apps/gstaudit/scripts/fix-nuc-tunnel.sh

set -euo pipefail

echo "=== GST Audit NUC — tunnel & app health check ==="
echo ""

echo "--- Docker containers (gstaudit + cloudflared) ---"
docker ps -a --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}' | grep -E 'NAMES|gstaudit|cloudflared' || true
echo ""

echo "--- Start gstaudit app ---"
if [ -d "$HOME/apps/gstaudit" ]; then
  cd "$HOME/apps/gstaudit"
  docker compose -f docker-compose.nuc.yml up -d --build
else
  echo "WARN: ~/apps/gstaudit not found"
fi
echo ""

echo "--- Start cloudflared tunnel ---"
if docker ps -a --format '{{.Names}}' | grep -q '^cloudflared-tunnel$'; then
  docker start cloudflared-tunnel || docker restart cloudflared-tunnel
else
  echo "WARN: cloudflared-tunnel container not found."
  echo "      Check: docker ps -a | grep cloud"
fi
echo ""

echo "--- Local health checks ---"
sleep 3
curl -sf http://127.0.0.1:8081/health && echo "  gstaudit frontend:8081 OK" || echo "  gstaudit frontend:8081 FAIL"
curl -sf http://127.0.0.1:8001/health && echo "  gstaudit backend:8001 OK"  || echo "  gstaudit backend:8001 FAIL"
echo ""

echo "--- cloudflared logs (last 20 lines) ---"
docker logs cloudflared-tunnel --tail 20 2>&1 || true
echo ""

echo "=== Cloudflare ingress reminder ==="
echo "In Cloudflare Zero Trust → Tunnels → your tunnel → Public Hostname:"
echo "  gstaudit.gkcircle.com  ->  http://localhost:8081"
echo ""
echo "After cloudflared is running, test: https://gstaudit.gkcircle.com"
