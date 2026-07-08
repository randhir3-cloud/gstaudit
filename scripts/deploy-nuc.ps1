# Deploy GST Audit locally with Docker (mirrors NUC stack ports)
# Usage: .\scripts\deploy-nuc.ps1

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

Write-Host "[deploy-nuc] Building and starting docker-compose.nuc.yml..."
docker compose -f docker-compose.nuc.yml up -d --build
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "[deploy-nuc] Waiting for services..."
Start-Sleep -Seconds 10

Write-Host "[deploy-nuc] Health check:"
try {
    $health = Invoke-RestMethod -Uri "http://127.0.0.1:8081/health" -TimeoutSec 10 -ErrorAction Stop
    Write-Host "  Health: $($health | ConvertTo-Json -Compress)"
} catch {
    Write-Host "  Health check failed - see container logs:"
    docker compose -f docker-compose.nuc.yml ps
    docker compose -f docker-compose.nuc.yml logs backend --tail 30
    exit 1
}

Write-Host "[deploy-nuc] Done."
Write-Host "  Frontend: http://127.0.0.1:8081"
Write-Host "  Backend:  http://127.0.0.1:8001/health"
