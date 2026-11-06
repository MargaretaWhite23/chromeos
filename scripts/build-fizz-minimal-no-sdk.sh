#!/usr/bin/env bash
set -Eeuo pipefail
mkdir -p reports output
trap 'rc=$?; printf "EXIT_CODE=%s\n" "$rc" > reports/minimal-build-exit-code.txt' EXIT
echo "=== TARGET CONTEXT ==="
echo "Board: fizz; ChromeOS: 150 / 16700.66.0"
echo "Mode: host-toolchain smoke build only (NOT exact Fizz sysroot)"
echo "=== DISCOVER PUBLIC ARTIFACTS ==="
python3 scripts/inventory-fizz-public-artifacts.py
echo "=== HOST CROSS/ABI INSPECTION ==="
uname -m
clang --version | head -2
ld.lld --version | head -1
echo "=== SMOKE BUILD ==="
clang -O2 -fuse-ld=lld -Wall -Wextra -Werror -o output/fizz-hello-host-abi tests/fizz-hello.c
file output/fizz-hello-host-abi | tee reports/compiled-binary.txt
readelf -h -l -d output/fizz-hello-host-abi > reports/compiled-elf.txt
sha256sum output/fizz-hello-host-abi > reports/compiled-sha256.txt
echo "=== ELF ABI AUDIT ==="
python3 scripts/audit-fizz-elf-abi.py --binary output/fizz-hello-host-abi --output reports/fizz-elf-abi-audit.json
echo "=== STATIC MUSL FIZZ READ-ONLY DIAGNOSTIC ==="
command -v musl-gcc
musl-gcc -O2 -static -Wall -Wextra -Werror -o output/fizz-static-probe tests/fizz-static-probe.c
file output/fizz-static-probe | tee reports/static-binary.txt
sha256sum output/fizz-static-probe > reports/static-sha256.txt
python3 scripts/audit-fizz-static-elf.py --binary output/fizz-static-probe --output reports/fizz-static-elf-audit.json
python3 tests/test-fizz-static-probe.py
echo "STATIC_MUSL_BUILD_PASS"
echo "STATIC_MUSL_CHROMEOS_FIZZ_NOT_TESTED"
echo "=== EXECUTE ON BUILD RUNNER (NOT CHROMEOS TARGET) ==="
output/fizz-hello-host-abi
echo "HOST_ABI_SMOKE_BUILD_PASS"
echo "TARGET_FIZZ_ABI_NOT_VERIFIED"
