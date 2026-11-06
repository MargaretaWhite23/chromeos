#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$PWD"
mkdir -p "$ROOT/reports"
trap 'rc=$?; printf "EXIT_CODE=%s\n" "$rc" > "$ROOT/reports/sdk-bootstrap-feasibility-exit-code.txt"' EXIT
echo "=== SYNC ONLY VERIFIED PINNED SDK SOURCE PREREQUISITES ==="
timeout --signal=TERM --kill-after=20s 13m bash scripts/probe-fizz-sysroot-prereqs.sh
echo "=== READ-ONLY SDK CAPACITY AND MANIFEST CLASSIFICATION ==="
timeout --signal=TERM --kill-after=10s 2m python3 scripts/assess-fizz-sdk-bootstrap.py
echo "=== DISK CAPACITY ==="
df -h "$ROOT"; du -sh "$ROOT/checkout"
echo "PASS: Fizz SDK feasibility catalogued; full checkout and SDK intentionally NOT attempted."
