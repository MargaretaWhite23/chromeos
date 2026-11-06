#!/usr/bin/env bash
set -Eeuo pipefail
export GIT_TERMINAL_PROMPT=0
export REPO_TRACE=0
mkdir -p reports checkout
ROOT="$PWD"
LOG="$ROOT/reports/checkout.log"
exec > >(tee -a "$LOG") 2>&1
trap 'rc=$?; echo "EXIT_CODE=$rc"; df -h .; du -sh checkout 2>/dev/null || true; printf "%s\n" "$rc" > reports/exit-code.txt' EXIT
echo "=== HOST CAPACITY ==="
df -h .; free -h; git --version; python3 --version
echo "=== FETCH PINNED PUBLIC BUILDSPEC ==="
curl --fail --location --retry 3 --max-time 60 -o reports/buildspec.xml \
  https://storage.googleapis.com/chromiumos-manifest-versions/buildspecs/150/16700.66.0.xml
sha256sum reports/buildspec.xml | tee reports/buildspec.sha256
echo "=== INSTALL REPO LAUNCHER ==="
mkdir -p "$HOME/bin"
curl --fail --location --retry 3 --max-time 60 \
  https://storage.googleapis.com/git-repo-downloads/repo -o "$HOME/bin/repo"
chmod +x "$HOME/bin/repo"
export PATH="$HOME/bin:$PATH"
repo version || true
echo "=== INITIALIZE EXACT PUBLIC BUILDSPEC ==="
cd checkout
# repo's standalone-manifest mode accepts a local manifest path; no source tree is synced at init.
repo init --no-repo-verify --standalone-manifest "file://$ROOT/reports/buildspec.xml"
echo "=== VERIFY MANIFEST PROJECTS ==="
repo list | tee "$ROOT/reports/repo-projects.txt"
echo "=== LIMITED PINNED SOURCE SYNC ==="
# Only a few selected repositories; this is NOT a full ChromiumOS checkout.
# Explicit project names are resolved from the pinned standalone manifest.
repo sync -j2 --fail-fast --no-clone-bundle --no-tags \
  chromiumos/manifest chromiumos/chromite chromiumos/overlays/board-overlays
echo "=== REPORT CHECKOUT ==="
repo forall -c 'printf "%s %s\n" "$REPO_PROJECT" "$(git rev-parse HEAD)"' \
  | tee "$ROOT/reports/checked-out-revisions.txt"
df -h .
du -sh .
echo "PASS: Limited exact-buildspec checkout succeeded. Full checkout and SDK remain UNVERIFIED."
