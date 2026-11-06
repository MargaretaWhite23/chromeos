# Fizz minimal no-SDK build

This GitHub Actions proof of concept targets **ChromeOS 150.0.16700.66.0 (board Fizz, x86-64)** without initializing a ChromiumOS SDK or syncing the 296-project release manifest.

It performs two independent, bounded operations:
1. Lists *candidate* objects using narrow unauthenticated XML-prefix queries to public buckets: `chromiumos-sdk`, `chromiumos-image-archive`, `chromeos-dev-installer` and `chromeos-prebuilt`. Save results in `reports/public-artifact-inventory.json`. Object listing results may be empty or inaccessible without implying artifacts do not exist elsewhere. It never downloads multi-gigabyte SDK tarballs or package archives.
2. Builds `tests/fizz-hello.c` using standalone Ubuntu Clang/LLD, records ELF and SHA-256 diagnostics, executes it only on the Ubuntu runner and uploads the executable.

**Do not mistake this executable for an exact Fizz-compatible binary.** A passing host-ABI build demonstrates the workflow, compiler and packaging pipeline; it does **not** prove ChromeOS compatibility. Before shipping to the device, compare its runtime dependencies, ELF interpreter and GLIBC requirements against the target, and obtain matching development files or an actual release-compatible sysroot.

No ChromeOS root filesystem, shell bridge server, Crostini filesystem, or target device is changed by this workflow.

Run in GitHub Actions: `.github/workflows/fizz-minimal-no-sdk-build.yml`.
