#!/usr/bin/env bash
set -Eeuo pipefail
BRANCH="release-R150-16700.B"
BASE="https://chromium.googlesource.com/chromiumos"
mkdir -p reports
REPORT="reports/fizz-public-source-probe.txt"
exec > >(tee "$REPORT") 2>&1
echo "Target: fizz ChromeOS 150 / 16700.66.0"
echo "Public source branch: $BRANCH"
echo "Probe date: $(date -u +%FT%TZ)"
echo "This is a source-availability probe, NOT a complete sysroot build."
fail=0
probe() {
  local name="$1" url="$2" dir="$3"
  echo "=== $name ==="
  if ! timeout 90 git ls-remote --exit-code "$url" "refs/heads/$BRANCH" | tee "reports/${name}-ref.txt"; then
    echo "::error::$name branch $BRANCH is not publicly accessible"
    fail=1
    return
  fi
  if ! timeout 180 git clone -q --depth 1 --single-branch --branch "$BRANCH" "$url" "$dir"; then
    echo "::error::$name branch exists but checkout failed"
    fail=1
    return
  fi
  echo "Commit: $(git -C "$dir" rev-parse HEAD)"
}
probe manifest "$BASE/manifest" public-manifest
probe board-overlays "$BASE/overlays/board-overlays" public-overlays
echo "=== Fizz board availability ==="
if [[ -d public-overlays/overlay-fizz ]]; then
  echo "PUBLIC_FIZZ_OVERLAY=present"
  find public-overlays/overlay-fizz -maxdepth 2 -type f | head -35
  if [[ -f public-overlays/overlay-fizz/toolchain.conf ]]; then
    echo "PUBLIC_FIZZ_TOOLCHAIN=present"
    cat public-overlays/overlay-fizz/toolchain.conf
  elif [[ -f public-overlays/baseboard-fizz/toolchain.conf ]]; then
    echo "PUBLIC_FIZZ_BASEBOARD_TOOLCHAIN=present"
    cat public-overlays/baseboard-fizz/toolchain.conf
  else
    echo "::warning::No directly located Fizz toolchain.conf; may be inherited"
  fi
else
  echo "::error::Fizz overlay missing on public release branch"
  fail=1
fi
echo "=== Manifest availability ==="
if [[ -f public-manifest/default.xml ]]; then
  echo "PUBLIC_MANIFEST=present"
  grep -n -E 'private|overlay|revision|remote' public-manifest/default.xml | head -45 || true
else
  echo "::error::default.xml missing from public manifest"
  fail=1
fi
echo "=== Exact official release equivalence ==="
echo "UNVERIFIED: Public branch existence does not establish the exact official 16700.66.0 source manifest, private overlays, binary packages or ABI equivalence."
echo "=== Result ==="
if [[ "$fail" -ne 0 ]]; then
  echo "::error::Public source prerequisites failed. Fizz sysroot build cannot be claimed available."
  exit 1
fi
echo "PASS: Public Fizz release-branch sources found. Exact build compatibility remains UNVERIFIED."
