# verify-nuc-deployment.ps1
# GST Audit (gstaudit) - NUC Runtime Verification Script
#
# Verification Gates:
#   V1  Container recreation (StartedAt recency)
#   V2  Image ID match (running = freshly built)
#   V3  Health endpoint: GET /health
#   V4  Docker logs clean (no ERROR/FATAL in last 50 lines)
#   V5  Backend API reachable: GET /api/ (via nginx proxy)
#   V6  Frontend availability: GET / -> HTTP 200
#
# Usage:
#   .\scripts\verify-nuc-deployment.ps1
#   .\scripts\verify-nuc-deployment.ps1 -MaxStartedAgeSecs 600

param(
    [int]$MaxStartedAgeSecs = 600
)

$ErrorActionPreference = "Stop"
$NucProject = "/home/randhir/apps/gstaudit"
$ComposeFile = "docker-compose.nuc.yml"
$FrontendPort = "8081"

function Invoke-NucBash([string]$Script) {
    $lf = $Script.Replace("`r", "")
    $tmpLocal = [System.IO.Path]::GetTempFileName()
    $tmpRemote = "/tmp/nuc-verify-$(Get-Random).sh"
    try {
        [System.IO.File]::WriteAllText($tmpLocal, $lf, (New-Object System.Text.UTF8Encoding $false))
        scp $tmpLocal "nuc:$tmpRemote" 2>$null

        $prevEap = $ErrorActionPreference
        $ErrorActionPreference = "Continue"
        $out = ssh nuc ('bash ' + $tmpRemote + '; exitCode=$?; rm -f ' + $tmpRemote + '; exit $exitCode') 2>&1
        $exit = $LASTEXITCODE
        $ErrorActionPreference = $prevEap
    } finally {
        Remove-Item $tmpLocal -ErrorAction SilentlyContinue
    }
    return [PSCustomObject]@{ Output = ($out | Out-String).Trim(); ExitCode = $exit }
}

$gateResults = @()
$allPass = $true

function Write-Gate([string]$Id, [string]$Label, [bool]$Pass, [string]$Detail = "") {
    $icon = if ($Pass) { "OK" } else { "FAIL" }
    Write-Host "  $Id  $icon  ${Label}: $Detail"
    $script:gateResults += [PSCustomObject]@{ Id = $Id; Pass = $Pass; Label = $Label; Detail = $Detail }
    if (-not $Pass) { $script:allPass = $false }
}

Write-Host ""
Write-Host "==========================================================="
Write-Host " GST Audit NUC - Runtime Verification (V1-V6)"
Write-Host "==========================================================="
Write-Host "  Target: ssh nuc:$NucProject"
Write-Host ""

$remoteScriptTemplate = @'
set -e
cd __NUC_PROJECT__

if docker compose version >/dev/null 2>&1; then DC="docker compose"; else DC="docker-compose"; fi

NOW_EPOCH=$(date +%s)
MAX_AGE=__MAX_AGE__
FRONTEND_PORT=__FRONTEND_PORT__

echo "--- V1: Container StartedAt ---"
for CONTAINER in gstaudit-backend gstaudit-frontend; do
  STARTED_AT=$(docker inspect --format '{{.State.StartedAt}}' "$CONTAINER" 2>/dev/null || echo 'NOT_FOUND')
  if [ "$STARTED_AT" = 'NOT_FOUND' ]; then
    echo "V1_FAIL:$CONTAINER:not found"
    continue
  fi
  START_EPOCH=$(date -d "$STARTED_AT" +%s 2>/dev/null || python3 -c "from datetime import datetime; import sys; ts = sys.argv[1].replace('Z','+00:00'); print(int(datetime.fromisoformat(ts).timestamp()))" "$STARTED_AT")
  AGE=$(( NOW_EPOCH - START_EPOCH ))
  if [ "$AGE" -gt "$MAX_AGE" ]; then
    echo "V1_FAIL:$CONTAINER:started ${AGE}s ago (max __MAX_AGE__s)"
  else
    echo "V1_OK:$CONTAINER:${AGE}s ago"
  fi
done

echo "--- V2: Image ID match ---"
BUILT_BACKEND=$(docker images --format '{{json .}}' | python3 -c "import sys, json; data = [json.loads(line) for line in sys.stdin]; img = next((i for i in data if i.get('Repository','') == 'gstaudit-backend' and i.get('Tag','') == 'latest'), None); print(img['ID'][:12] if img else 'unknown')" 2>/dev/null || echo 'unknown')
BUILT_FRONTEND=$(docker images --format '{{json .}}' | python3 -c "import sys, json; data = [json.loads(line) for line in sys.stdin]; img = next((i for i in data if i.get('Repository','') == 'gstaudit-frontend' and i.get('Tag','') == 'latest'), None); print(img['ID'][:12] if img else 'unknown')" 2>/dev/null || echo 'unknown')

RUNNING_BACKEND_SHORT=$(docker inspect gstaudit-backend --format '{{.Image}}' 2>/dev/null | xargs docker inspect --format '{{slice .Id 7 19}}' 2>/dev/null || echo 'unknown')
RUNNING_FRONTEND_SHORT=$(docker inspect gstaudit-frontend --format '{{.Image}}' 2>/dev/null | xargs docker inspect --format '{{slice .Id 7 19}}' 2>/dev/null || echo 'unknown')

echo "V2_BACKEND:built=$BUILT_BACKEND running=$RUNNING_BACKEND_SHORT match=$([ "$BUILT_BACKEND" = "$RUNNING_BACKEND_SHORT" ] && echo 'YES' || echo 'NO')"
echo "V2_FRONTEND:built=$BUILT_FRONTEND running=$RUNNING_FRONTEND_SHORT match=$([ "$BUILT_FRONTEND" = "$RUNNING_FRONTEND_SHORT" ] && echo 'YES' || echo 'NO')"

HEALTH_URL="http://127.0.0.1:${FRONTEND_PORT}/health"
FRONTEND_URL="http://127.0.0.1:${FRONTEND_PORT}/"
BACKEND_DIRECT="http://127.0.0.1:8001/health"

echo "--- V3: Health endpoint ---"
HEALTH_BODY=$(curl -sf "$HEALTH_URL" 2>/dev/null || echo 'CURL_FAIL')
if echo "$HEALTH_BODY" | grep -q '"status":"healthy"'; then
  echo "V3_OK:$HEALTH_BODY"
else
  echo "V3_FAIL:response=$HEALTH_BODY"
fi

echo "--- V4: Docker logs ---"
BACKEND_ERRORS=$($DC -f __COMPOSE_FILE__ logs backend --tail 50 2>/dev/null | grep -iE '(ERROR|FATAL|Traceback)' | wc -l)
if [ "$BACKEND_ERRORS" -eq 0 ]; then
  echo "V4_OK:0 ERROR/FATAL lines in last 50 backend log lines"
else
  echo "V4_WARN:$BACKEND_ERRORS ERROR/FATAL lines found"
fi

echo "--- V5: Backend direct ---"
DIRECT_BODY=$(curl -sf "$BACKEND_DIRECT" 2>/dev/null || echo 'CURL_FAIL')
if echo "$DIRECT_BODY" | grep -q '"status":"healthy"'; then
  echo "V5_OK:backend direct health OK"
else
  echo "V5_FAIL:direct=$DIRECT_BODY"
fi

echo "--- V6: Frontend ---"
FRONTEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$FRONTEND_URL" 2>/dev/null || echo '000')
if [ "$FRONTEND_STATUS" = '200' ]; then
  echo "V6_OK:GET / -> HTTP 200"
else
  echo "V6_FAIL:GET / -> HTTP $FRONTEND_STATUS"
fi

echo "VERIFY_COMPLETE"
'@

$remoteScript = $remoteScriptTemplate `
    -replace '__NUC_PROJECT__', $NucProject `
    -replace '__COMPOSE_FILE__', $ComposeFile `
    -replace '__MAX_AGE__', $MaxStartedAgeSecs `
    -replace '__FRONTEND_PORT__', $FrontendPort

$result = Invoke-NucBash $remoteScript
$output = $result.Output
Write-Host $output
Write-Host ""

$v1Pass = ($output -notmatch "V1_FAIL:")
$v1Detail = ($output | Select-String -Pattern "V1_(OK|FAIL):\S+:.+" -AllMatches).Matches.Value -join " | "
Write-Gate "V1" "Container times" $v1Pass $v1Detail

$v2Pass = ($output -match "V2_BACKEND:.*match=YES") -and ($output -match "V2_FRONTEND:.*match=YES")
Write-Gate "V2" "Image IDs" $v2Pass "backend+frontend"

$v3Pass = $output -match "V3_OK:"
Write-Gate "V3" "Health (via nginx)" $v3Pass ($(if ($v3Pass) { "healthy" } else { "FAIL" }))

$v4Pass = $output -match "V4_OK:"
Write-Gate "V4" "Docker logs" $v4Pass ($(if ($v4Pass) { "clean" } else { "warnings" }))

$v5Pass = $output -match "V5_OK:"
Write-Gate "V5" "Backend direct" $v5Pass ($(if ($v5Pass) { "healthy" } else { "FAIL" }))

$v6Pass = $output -match "V6_OK:"
Write-Gate "V6" "Frontend" $v6Pass ($(if ($v6Pass) { "HTTP 200" } else { "FAIL" }))

Write-Host ""
Write-Host "==========================================================="
Write-Host " GST Audit NUC - VERIFICATION SUMMARY"
Write-Host "==========================================================="
foreach ($g in $gateResults) {
    $icon = if ($g.Pass) { "OK" } else { "FAIL" }
    Write-Host "  $($g.Id)  $icon  $($g.Label): $($g.Detail)"
}
$overallStatus = if ($allPass) { "PASS" } else { "FAIL" }
Write-Host "  Overall: $overallStatus"
Write-Host "==========================================================="
Write-Host ""

if (-not $allPass) { exit 1 }
Write-Host "[verify] All verification gates passed."
