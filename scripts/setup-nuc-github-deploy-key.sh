#!/usr/bin/env bash
# Run ON the NUC once (interactive): bash scripts/setup-nuc-github-deploy-key.sh
# Creates a passphrase-free deploy key for git@github.com:randhir3-cloud/gstaudit.git

set -euo pipefail

KEY="$HOME/.ssh/id_ed25519_gstaudit_github"
CONFIG="$HOME/.ssh/config"

echo "== GST Audit NUC GitHub deploy key setup =="

if [[ -f "$KEY" ]]; then
  echo "Key already exists: $KEY"
else
  echo "Generating deploy key (no passphrase)..."
  ssh-keygen -t ed25519 -C "nuc-gstaudit-deploy" -f "$KEY" -N ""
fi

mkdir -p "$HOME/.ssh"
chmod 700 "$HOME/.ssh"
chmod 600 "$KEY"
chmod 644 "${KEY}.pub"

if grep -q 'Host github.com-gstaudit' "$CONFIG" 2>/dev/null; then
  echo ""
  echo "NOTE: ~/.ssh/config already has Host github.com-gstaudit."
else
  echo "Appending github.com-gstaudit block to ~/.ssh/config ..."
  cat >>"$CONFIG" <<'EOF'

# GST Audit — GitHub deploy (NUC)
Host github.com-gstaudit
    HostName github.com
    User git
    IdentityFile ~/.ssh/id_ed25519_gstaudit_github
    IdentitiesOnly yes
EOF
  chmod 600 "$CONFIG"
fi

echo ""
echo "=== Add this deploy key to GitHub ==="
echo "Repo: randhir3-cloud/gstaudit → Settings → Deploy keys → Add deploy key"
echo "Title: nuc-gstaudit-deploy"
echo "Allow write access: OFF (read-only is enough for git pull)"
echo ""
cat "${KEY}.pub"
echo ""
echo "Then on the NUC:"
echo "  cd ~/apps/gstaudit"
echo "  git remote set-url origin git@github.com-gstaudit:randhir3-cloud/gstaudit.git"
echo "  ssh -T git@github.com-gstaudit    # expect: Hi randhir3-cloud/gstaudit! ..."
echo "  git pull"
