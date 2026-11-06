#!/usr/bin/env bash
# Bounded pinned-source preflight, not a ChromiumOS SDK build.
set -Eeuo pipefail
ROOT="$(pwd)"
mkdir -p "$ROOT/reports"
trap 'rc=$?; printf "EXIT_CODE=%s\n" "$rc" > "$ROOT/reports/sysroot-preflight-exit-code.txt"' EXIT

echo "=== REPEAT VERIFIED EXACT-BUILDSPEC CHECKOUT ==="
bash scripts/checkout-fizz-pinned.sh
# Child shells cannot export PATH back to parent; reuse downloaded repo launcher.
export PATH="$HOME/bin:$PATH"
command -v repo

echo "=== SELECT PINNED CROSUTILS PROJECT ==="
PROJECT="$(python3 - <<'PY'
import xml.etree.ElementTree as ET
root = ET.parse("reports/buildspec.xml").getroot()
names = [p.get("name") for p in root.findall("project") if p.get("name", "").endswith("/platform/crosutils")]
if len(names) != 1:
    raise SystemExit("Expected exactly one pinned crosutils project; found %d" % len(names))
print(names[0])
PY
)"
echo "CROSUTILS_PROJECT=$PROJECT"

echo "=== CAPACITY GATE ==="
df -h "$ROOT"
FREE_KIB=$(df -Pk "$ROOT" | awk 'NR==2 {print $4}')
if (( FREE_KIB < 5 * 1024 * 1024 )); then
  echo "::error::Less than 5 GiB free; refusing further checkout"
  exit 1
fi

echo "=== SYNC ONLY PINNED CROSUTILS PROJECT ==="
(cd checkout && timeout --signal=TERM --kill-after=15s 5m \
  repo sync -j1 --fail-fast --no-clone-bundle --no-tags "$PROJECT")

echo "=== CONFIRM CHECKED-OUT PIN ==="
(cd checkout && repo forall "$PROJECT" -c \
  'printf "PINNED_PROJECT %s %s\n" "$REPO_PROJECT" "$(git rev-parse HEAD)"') \
  | tee "$ROOT/reports/crosutils-revision.txt"

echo "=== ANALYZE FIZZ SOURCE / SDK PREREQUISITES ==="
python3 scripts/report-fizz-sysroot-prereqs.py \
  --manifest "$ROOT/reports/buildspec.xml" \
  --checkout "$ROOT/checkout" \
  --output "$ROOT/reports/sysroot-preflight.json"
df -h "$ROOT"
du -sh "$ROOT/checkout"
echo "PASS: Fizz source prerequisites inspected; SDK and board sysroot NOT built."
