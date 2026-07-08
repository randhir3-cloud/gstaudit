# Install SSH public key on NUC (one-time, prompts for randhir password)
# Usage: .\scripts\install-nuc-ssh-key.ps1

$ErrorActionPreference = "Stop"
$keyPub = Join-Path $env:USERPROFILE ".ssh\id_ed25519.pub"

if (-not (Test-Path $keyPub)) {
    $keyPub = Join-Path $env:USERPROFILE ".ssh\id_ed25519_gkcircle.pub"
}

if (-not (Test-Path $keyPub)) {
    Write-Error @"
Missing SSH public key. Generate one with:
  ssh-keygen -t ed25519 -f `$env:USERPROFILE\.ssh\id_ed25519 -N '""'
"@
}

$remoteCmd = 'mkdir -p ~/.ssh && chmod 700 ~/.ssh && cat >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys && echo KEY_INSTALLED_OK'

Write-Host "Enter randhir@192.168.1.2 password when prompted..."
Get-Content $keyPub | ssh -o StrictHostKeyChecking=accept-new randhir@192.168.1.2 $remoteCmd

Write-Host ""
Write-Host "Testing passwordless login..."
ssh -o BatchMode=yes nuc 'echo SSH_KEY_LOGIN_OK; hostname; whoami'
