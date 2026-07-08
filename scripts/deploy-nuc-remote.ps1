# deploy-nuc-remote.ps1
# GST Audit (gstexcel) - NUC Production Deployment Script
#
# Responsibility: DEPLOY ONLY (G1-G5)
#   G1  Git pull / SHA verification
#   G2  Clean working tree
#   G3  Docker image build
#   G4  docker compose up -d
#   G5  Health check via frontend port
#
# Usage:
#   .\scripts\deploy-nuc-remote.ps1
#
# Requirements:
#   - Passwordless SSH: 'ssh nuc' must work
#   - NUC project: ~/apps/gstaudit

$ErrorActionPreference = "Stop"
$NucProject = "/home/randhir/apps/gstaudit"
$ComposeFile = "docker-compose.nuc.yml"
$FrontendPort = "8081"

function Invoke-NucBash([string]$Script, [switch]$AllowNonZero) {
    $lf = $Script.Replace("`r", "")
    $tmpLocal = [System.IO.Path]::GetTempFileName()
    $tmpRemote = "/tmp/nuc-deploy-$(Get-Random).sh"
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
    if (-not $AllowNonZero -and $exit -ne 0) {
        throw "Remote bash failed (exit $exit):`n$out"
    }
    return [PSCustomObject]@{ Output = ($out | Out-String).Trim(); ExitCode = $exit }
}

$gateResults = @()

function Write-Gate([string]$Id, [string]$Label, [bool]$Pass, [string]$Detail = "") {
    $icon = if ($Pass) { "OK" } else { "FAIL" }
    Write-Host "  $Id  $icon  ${Label}: $Detail"
    $script:gateResults += [PSCustomObject]@{ Id = $Id; Pass = $Pass; Label = $Label; Detail = $Detail }
}

Write-Host ""
Write-Host "==========================================================="
Write-Host " GST Audit NUC - Deployment (G1-G5)"
Write-Host "==========================================================="
Write-Host ""

$preflightResult = Invoke-NucBash "test -d $NucProject && test -f $NucProject/$ComposeFile && echo PREFLIGHT_OK"
if ($preflightResult.Output -notmatch "PREFLIGHT_OK") {
    Write-Error "Preflight failed: project or compose file missing at $NucProject"
    exit 1
}
Write-Host "[deploy] Preflight OK."
Write-Host ""

$remoteScriptTemplate = @'
set -e
cd __NUC_PROJECT__

if docker compose version >/dev/null 2>&1; then
  DC="docker compose"
elif command -v docker-compose >/dev/null 2>&1; then
  DC="docker-compose"
else
  echo "GATE_FAIL:G0:Docker compose not found"; exit 1
fi

if git pull --ff-only 2>/dev/null; then
  echo "[nuc] git pull OK"
else
  echo "[nuc] WARN: git pull skipped. Deploying current HEAD."
fi
GIT_SHA=$(git rev-parse --short HEAD 2>/dev/null || echo 'no-git')
echo "GATE_G1_SHA:$GIT_SHA"

DIRTY=$(git status --short 2>/dev/null || true)
if [ -n "$DIRTY" ]; then
  echo "GATE_FAIL:G2:Dirty tree: $DIRTY"; exit 1
fi
echo "GATE_G2_OK"

if ! $DC -f __COMPOSE_FILE__ build 2>&1; then
  echo "GATE_FAIL:G3:docker compose build failed"; exit 1
fi

BACKEND_IMAGE_ID=$(docker images --format '{{json .}}' | python3 -c "import sys, json; data = [json.loads(line) for line in sys.stdin]; img = next((i for i in data if i.get('Repository','') == 'gstaudit-backend' and i.get('Tag','') == 'latest'), None); print(img['ID'][:12] if img else 'unknown')" 2>/dev/null || echo 'unknown')
FRONTEND_IMAGE_ID=$(docker images --format '{{json .}}' | python3 -c "import sys, json; data = [json.loads(line) for line in sys.stdin]; img = next((i for i in data if i.get('Repository','') == 'gstaudit-frontend' and i.get('Tag','') == 'latest'), None); print(img['ID'][:12] if img else 'unknown')" 2>/dev/null || echo 'unknown')
echo "GATE_G3_OK:backend=$BACKEND_IMAGE_ID frontend=$FRONTEND_IMAGE_ID"

if ! $DC -f __COMPOSE_FILE__ up -d; then
  echo "GATE_FAIL:G4:docker compose up -d failed"; exit 1
fi
echo "GATE_G4_OK"

sleep 8
HEALTH_BODY=$(curl -sf "http://127.0.0.1:__FRONTEND_PORT__/health" 2>/dev/null || echo 'CURL_FAIL')
if echo "$HEALTH_BODY" | grep -q '"status":"healthy"'; then
  echo "GATE_G5_OK:$HEALTH_BODY"
else
  echo "GATE_FAIL:G5:health check failed: $HEALTH_BODY"
  $DC -f __COMPOSE_FILE__ logs backend --tail 30
  exit 1
fi

echo "DEPLOY_COMPLETE"
'@

$remoteScript = $remoteScriptTemplate `
    -replace '__NUC_PROJECT__', $NucProject `
    -replace '__COMPOSE_FILE__', $ComposeFile `
    -replace '__FRONTEND_PORT__', $FrontendPort

$result = Invoke-NucBash $remoteScript -AllowNonZero
$output = $result.Output
Write-Host $output
Write-Host ""

if ($output -match "GATE_FAIL:(\w+):(.+)") {
    Write-Gate $Matches[1] "FAILED" $false $Matches[2]
    exit 1
}

if ($result.ExitCode -ne 0 -or $output -notmatch "DEPLOY_COMPLETE") {
    Write-Host "[deploy] Deployment failed."
    exit 1
}

$sha = if ($output -match "GATE_G1_SHA:(\S+)") { $Matches[1] } else { "unknown" }
$images = if ($output -match "GATE_G3_OK:(.+)") { $Matches[1] } else { "unknown" }
$health = if ($output -match "GATE_G5_OK:(.+)") { $Matches[1] } else { "ok" }

Write-Gate "G1" "Git SHA" $true $sha
Write-Gate "G2" "Clean tree" $true "clean"
Write-Gate "G3" "Docker build" $true $images
Write-Gate "G4" "Compose up" $true "containers running"
Write-Gate "G5" "Health check" $true $health

Write-Host ""
Write-Host "[deploy] Deployment complete."
Write-Host "  Frontend: http://192.168.1.2:8081"
Write-Host "  Backend:  http://192.168.1.2:8001/health"
Write-Host "[deploy] Run: .\scripts\verify-nuc-deployment.ps1"
Write-Host ""
