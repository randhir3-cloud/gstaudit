# Publish the current committed branch to GitHub and optionally deploy via Railway.
#
# GST Audit deploys via Railway (GitHub integration). This script:
#   1. verifies the working tree is clean and origin is the canonical repo
#   2. pushes the current branch to GitHub
#   3. if Railway CLI is installed and linked, optionally triggers Railway deployment
#
# Usage:
#   powershell -File scripts/update-project.ps1              # push + Railway deploy
#   powershell -File scripts/update-project.ps1 -SkipRailway # push only

param(
    [switch]$SkipRailway
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

$allowedOrigins = @(
    "https://github.com/randhir3-cloud/gstaudit.git",
    "git@github.com:randhir3-cloud/gstaudit.git"
)
$origin = (git remote get-url origin).Trim()
if ($origin -notin $allowedOrigins) {
    throw "Unexpected origin '$origin'. Expected canonical repository: https://github.com/randhir3-cloud/gstaudit.git"
}

if (git status --porcelain -uno) {
    throw "Working tree has unstaged modifications. Review and commit changes before publishing."
}

$branch = (git branch --show-current).Trim()
if (-not $branch) { throw "Detached HEAD is not deployable." }

git push -u origin $branch
if ($LASTEXITCODE -ne 0) { throw "Git push failed." }
Write-Host "Successfully pushed origin/$branch." -ForegroundColor Green

if ($SkipRailway) {
    Write-Host "Skipped Railway deploy (-SkipRailway)." -ForegroundColor Cyan
    exit 0
}

$railway = Get-Command railway -ErrorAction SilentlyContinue
if (-not $railway) {
    Write-Host "Railway CLI not found. If GitHub auto-deploy is configured on Railway, the push above triggered a deploy." -ForegroundColor Yellow
    Write-Host "To link Railway CLI: npm i -g @railway/cli; railway login; railway link" -ForegroundColor Gray
    exit 0
}

# Check if directory is linked to Railway
railway status *> $null
if ($LASTEXITCODE -ne 0) {
    Write-Host "This repository is not yet linked to a Railway project. Run 'railway link' to connect." -ForegroundColor Yellow
    exit 0
}

Write-Host "Triggering Railway deployment via Railway CLI..." -ForegroundColor Cyan
railway up --ci
if ($LASTEXITCODE -ne 0) { throw "Railway deployment command failed." }
Write-Host "Railway deploy triggered successfully for origin/$branch." -ForegroundColor Green
