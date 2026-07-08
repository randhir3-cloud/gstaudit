# Update GST Audit: push local code to GitHub, then git pull on NUC.
#
# Usage:
#   .\scripts\update-project.ps1
#   .\scripts\update-project.ps1 -Message "feat: add gstr1 merge"
#   .\scripts\update-project.ps1 -SkipCommit
#
# NUC path: ~/apps/gstaudit
# Requires: git, GitHub push access, passwordless `ssh nuc`

param(
    [string]$Message = "chore: project update",
    [switch]$SkipCommit
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$NucSshHost = "nuc"
$NucProject = "/home/randhir/apps/gstaudit"

Set-Location $Root

Write-Host "[update-project] Repo: $Root"
Write-Host "[update-project] NUC:  ${NucSshHost}:${NucProject}"

$porcelain = git status --porcelain
if ($porcelain -and -not $SkipCommit) {
    Write-Host "[update-project] Committing local changes..."
    git add -A
    git commit -m $Message
} elseif ($porcelain -and $SkipCommit) {
    Write-Host "[update-project] WARN: Uncommitted changes present (-SkipCommit). Push may not include them."
} else {
    Write-Host "[update-project] Working tree clean (nothing to commit)."
}

$branch = git branch --show-current
Write-Host "[update-project] Pushing branch '$branch' to origin..."
$upstream = git rev-parse --abbrev-ref --symbolic-full-name "@{u}" 2>$null
if (-not $upstream) {
    git push -u origin $branch
} else {
    git push origin $branch
}
if ($LASTEXITCODE -ne 0) {
    Write-Error "git push failed. Fix GitHub auth/branch, then retry."
}

Write-Host "[update-project] GitHub push OK."

$pullScript = @'
set -e
test -d PROJECT_DIR/.git || { echo "ERROR: not a git repo: PROJECT_DIR"; exit 1; }
cd PROJECT_DIR
pwd
echo "[nuc] git pull --ff-only..."
if ! git diff --quiet || ! git diff --cached --quiet; then
  echo "[nuc] stashing local changes before pull..."
  git stash push -u -m "update-project auto-stash $(date -Iseconds)" || true
fi
git pull --ff-only
echo "[nuc] HEAD: $(git rev-parse --short HEAD) — $(git log -1 --format=%s)"
'@.Replace('PROJECT_DIR', $NucProject)

Write-Host "[update-project] Pulling on NUC at $NucProject ..."
$lf = $pullScript.Replace("`r", "")
$lf | ssh $NucSshHost "bash -s"
if ($LASTEXITCODE -ne 0) {
    Write-Error @"
NUC git pull failed.

On the NUC, ensure GitHub deploy key is configured:
  bash ~/apps/gstaudit/scripts/setup-nuc-github-deploy-key.sh
  ssh -T git@github.com
  cd ~/apps/gstaudit && git pull
"@
}

Write-Host ""
Write-Host "[update-project] Done."
Write-Host "  GitHub:  origin/$branch pushed"
Write-Host "  NUC:     $NucProject updated"
Write-Host ""
Write-Host "To rebuild containers on NUC after code changes:"
Write-Host "  .\scripts\deploy-nuc-remote.ps1"
