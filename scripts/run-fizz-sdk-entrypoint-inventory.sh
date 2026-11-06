#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$PWD"
mkdir -p reports
trap 'rc=$?; echo "EXIT_CODE=$rc" > "$ROOT/reports/sdk-entrypoints-exit-code.txt"' EXIT
echo "=== PINNED SOURCE CHECKOUT AND SDK PREREQUISITES ==="
timeout --signal=TERM --kill-after=30s 12m bash scripts/probe-fizz-sysroot-prereqs.sh
echo "=== SDK ENTRYPOINT INVENTORY ==="
timeout --signal=TERM --kill-after=10s 90s python3 scripts/inventory-fizz-sdk-entrypoints.py
echo "=== RUNNER CAPACITY ==="
df -h .; du -sh checkout
echo "PASS: SDK source entrypoints inventoried. SDK and sysroot remain UNBUILT."
