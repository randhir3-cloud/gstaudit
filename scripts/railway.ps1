# Railway Management Helper for GST Audit
#
# Operations:
#   .\scripts\railway.ps1 link               # Link Railway project/environment
#   .\scripts\railway.ps1 status             # Show deployment status and variables
#   .\scripts\railway.ps1 logs [frontend|backend] # Stream service logs
#   .\scripts\railway.ps1 redeploy [frontend|backend] # Trigger service redeployment
#   .\scripts\railway.ps1 ssh [backend]      # Open Railway SSH shell into backend
#   .\scripts\railway.ps1 migrate            # Run Alembic migrations on backend
#   .\scripts\railway.ps1 check              # Check health endpoints

param(
    [Parameter(Position=0, Mandatory=$true)]
    [ValidateSet("link", "status", "logs", "redeploy", "ssh", "migrate", "check", "up")]
    [string]$Command,

    [Parameter(Position=1)]
    [string]$Target = "backend",

    [Parameter(Position=2)]
    [string]$ExtraArg
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

# Check Railway CLI
$railway = Get-Command railway -ErrorAction SilentlyContinue
if (-not $railway) {
    Write-Error "Railway CLI is not installed. Install via: npm i -g @railway/cli"
    exit 1
}

# Resolve Service Name
function Get-ServiceName([string]$svc) {
    if ($svc -like "*front*") {
        return if ($env:RAILWAY_FRONTEND_SERVICE) { $env:RAILWAY_FRONTEND_SERVICE } else { "gstaudit-frontend" }
    } else {
        return if ($env:RAILWAY_BACKEND_SERVICE) { $env:RAILWAY_BACKEND_SERVICE } else { "gstaudit-backend" }
    }
}

switch ($Command) {
    "link" {
        Write-Host "=== Linking Railway Project for GST Audit ===" -ForegroundColor Cyan
        railway link
    }

    "status" {
        Write-Host "=== Railway Project Status ===" -ForegroundColor Cyan
        railway status
    }

    "logs" {
        $svcName = Get-ServiceName $Target
        Write-Host "=== Streaming logs for service '$svcName' ===" -ForegroundColor Cyan
        railway logs --service $svcName
    }

    "redeploy" {
        $svcName = Get-ServiceName $Target
        Write-Host "=== Triggering redeployment for service '$svcName' ===" -ForegroundColor Cyan
        railway redeploy --service $svcName --yes
    }

    "ssh" {
        $svcName = Get-ServiceName $Target
        Write-Host "=== Connecting SSH shell to service '$svcName' ===" -ForegroundColor Cyan
        railway ssh --service $svcName
    }

    "migrate" {
        $svcName = Get-ServiceName "backend"
        Write-Host "=== Running Alembic database migrations on '$svcName' ===" -ForegroundColor Cyan
        railway run --service $svcName -- alembic upgrade head
    }

    "up" {
        Write-Host "=== Deploying local repository changes to Railway ===" -ForegroundColor Cyan
        railway up --ci
    }

    "check" {
        Write-Host "=== Running Health Checks for GST Audit ===" -ForegroundColor Cyan
        & "$PSScriptRoot\check-health.ps1"
    }
}
