#!/usr/bin/env bash
# Collect Cloudflare Error 1033 diagnostics — run ON the NUC
# Usage: bash scripts/diagnose-cloudflare-tunnel.sh | tee /tmp/tunnel-diag.txt

set -u

section() { echo ""; echo "========== $1 =========="; }

section "1. systemd cloudflared (if installed)"
sudo systemctl status cloudflared --no-pager 2>&1 || echo "(no systemd service)"

section "2. cloudflared journal (last 50)"
sudo journalctl -u cloudflared -n 50 --no-pager 2>&1 || echo "(no journal)"

section "3. cloudflared config files"
for f in /etc/cloudflared/config.yml ~/.cloudflared/config.yml; do
  if [ -f "$f" ]; then
    echo "--- $f ---"
    sudo cat "$f" 2>/dev/null || cat "$f"
  else
    echo "--- $f (not found) ---"
  fi
done

section "4. cloudflared tunnel list"
cloudflared tunnel list 2>&1 || echo "(cloudflared CLI not in PATH)"

section "5. Docker: cloudflared + gstaudit + gkcircle"
docker ps -a --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}' 2>&1 | grep -E 'NAMES|cloud|gstaudit|gk-circle' || docker ps -a

section "6. cloudflared-tunnel container logs (last 40)"
docker logs cloudflared-tunnel --tail 40 2>&1 || echo "(container not found)"

section "7. Local origin health"
echo -n "gstaudit :8081/health -> "; curl -sf -o /dev/null -w "%{http_code}" http://127.0.0.1:8081/health 2>/dev/null || echo "FAIL"
echo -n "gkcircle :3100/health -> "; curl -sf -o /dev/null -w "%{http_code}" http://127.0.0.1:3100/health 2>/dev/null || echo "FAIL"
echo ""

section "8. Internet connectivity"
ping -c 2 1.1.1.1 2>&1 || true
ping -c 2 google.com 2>&1 || true

section "9. Expected ingress for gstaudit"
echo "gstaudit.gkcircle.com should map to: http://localhost:8081"
echo "(NOT port 3000 — gstaudit frontend runs on 8081)"

echo ""
echo "=== Done. Paste /tmp/tunnel-diag.txt or this output for analysis ==="
