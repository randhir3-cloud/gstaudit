# Health verification script for GST Audit Production & Local deployments
#
# Usage:
#   .\scripts\check-health.ps1
#   .\scripts\check-health.ps1 -BaseFrontendUrl "http://localhost:8081" -BaseBackendUrl "http://localhost:8001"

param(
    [string]$BaseFrontendUrl = "https://gstaudit.gkcircle.com",
    [string]$BaseBackendUrl = "https://api-gstaudit.gkcircle.com"
)

$ErrorActionPreference = "Continue"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host " GST Audit - Deployment Health Check " -ForegroundColor Cyan
Write-Host " Frontend: $BaseFrontendUrl" -ForegroundColor Gray
Write-Host " Backend:  $BaseBackendUrl" -ForegroundColor Gray
Write-Host "==========================================" -ForegroundColor Cyan

$allPassed = $true

# 1. Backend Core Health
Write-Host "`n[1/3] Checking Backend Health ($BaseBackendUrl/health)..." -NoNewline
try {
    $resp = Invoke-RestMethod -Uri "$BaseBackendUrl/health" -Method Get -TimeoutSec 10
    if ($resp.status -eq "healthy") {
        Write-Host " [PASS] (Service: $($resp.service))" -ForegroundColor Green
    } else {
        Write-Host " [WARN] (Response: $($resp | ConvertTo-Json -Compress))" -ForegroundColor Yellow
    }
} catch {
    Write-Host " [FAIL] ($_)" -ForegroundColor Red
    $allPassed = $false
}

# 2. Backend System Monitor Health
Write-Host "[2/3] Checking Backend System Status ($BaseBackendUrl/api/system/health)..." -NoNewline
try {
    $resp = Invoke-RestMethod -Uri "$BaseBackendUrl/api/system/health" -Method Get -TimeoutSec 10
    if ($resp.application -eq "healthy") {
        Write-Host " [PASS] (App: $($resp.application), DB: $($resp.database), Workers: $($resp.workers))" -ForegroundColor Green
    } else {
        Write-Host " [WARN] (App: $($resp.application), DB: $($resp.database))" -ForegroundColor Yellow
    }
} catch {
    Write-Host " [FAIL] ($_)" -ForegroundColor Red
    $allPassed = $false
}

# 3. Frontend Availability
Write-Host "[3/3] Checking Frontend Availability ($BaseFrontendUrl)..." -NoNewline
try {
    $resp = Invoke-WebRequest -Uri $BaseFrontendUrl -Method Get -TimeoutSec 10 -UseBasicParsing
    if ($resp.StatusCode -eq 200) {
        Write-Host " [PASS] (HTTP 200 OK)" -ForegroundColor Green
    } else {
        Write-Host " [WARN] (HTTP $($resp.StatusCode))" -ForegroundColor Yellow
    }
} catch {
    Write-Host " [FAIL] ($_)" -ForegroundColor Red
    $allPassed = $false
}

Write-Host "`n==========================================" -ForegroundColor Cyan
if ($allPassed) {
    Write-Host " All Health Checks PASSED" -ForegroundColor Green
    exit 0
} else {
    Write-Host " Health Check finished with FAILURES or WARNINGS" -ForegroundColor Yellow
    exit 1
}
