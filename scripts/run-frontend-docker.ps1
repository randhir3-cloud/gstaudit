# Runs the GST Audit Frontend inside local Docker
#
# Usage:
#   .\scripts\run-frontend-docker.ps1

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

$ContainerName = "gstaudit-frontend-local"
$ImageName = "gstaudit-frontend:local"
$HostPort = "8080"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host " GST Audit - Local Frontend Docker Runner " -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

# 1. Stop / Remove old container if present
Write-Host "`n[1/3] Removing existing '$ContainerName' container (if any)..." -ForegroundColor Gray
docker rm -f $ContainerName 2>$null | Out-Null

# 2. Build Docker Image
Write-Host "[2/3] Building Docker image '$ImageName'..." -ForegroundColor Cyan
docker build -t $ImageName ./frontend
if ($LASTEXITCODE -ne 0) {
    Write-Error "Docker build failed."
    exit 1
}

# 3. Run Container
Write-Host "[3/3] Starting container '$ContainerName' on port $HostPort:80..." -ForegroundColor Cyan
docker run -d --name $ContainerName -p "${HostPort}:80" $ImageName | Out-Null

if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to start Docker container."
    exit 1
}

# 4. Verify status
Start-Sleep -Seconds 2
$status = (docker inspect -f '{{.State.Status}}' $ContainerName).Trim()
if ($status -eq "running") {
    Write-Host "`n==========================================" -ForegroundColor Green
    Write-Host " GST Audit frontend is running!" -ForegroundColor Green
    Write-Host " URL:        http://localhost:$HostPort" -ForegroundColor White
    Write-Host " Merge Page: http://localhost:$HostPort/merge" -ForegroundColor White
    Write-Host " Backend:    NOT RUNNING (Not required for merge)" -ForegroundColor Gray
    Write-Host "==========================================" -ForegroundColor Green
} else {
    Write-Error "Container exited unexpectedly with status '$status'. Check logs using: docker logs $ContainerName"
    exit 1
}
