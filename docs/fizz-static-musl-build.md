# Static x86-64 Fizz probe built by GitHub Actions

The GitHub Actions `fizz-minimal-no-sdk-build.yml` workflow now produces two independent executables:

- `output/fizz-hello-host-abi`: the original dynamically linked Ubuntu/GLIBC smoke test; has a GLIBC version requirement (previously 2.34) and a loader dependency.
- `output/fizz-static-probe`: **statically linked with musl** through `musl-gcc -static`. A CI ELF audit verifies its architecture is x86-64 and that `readelf` reports **no PT_INTERP and no DT_NEEDED**. This avoids the target's GLIBC and dynamic-loader dependencies.

The static probe performs only read-only operations: `uname` plus reading `/etc/lsb-release` and `/etc/os-release`, emitting `FIZZ_STATIC_PROBE_COMPLETE`. GitHub Actions executes it **only on the Ubuntu runner** and records its SHA-256 and ELF evidence.

The archive includes `output/fizz-static-probe`, `reports/fizz-static-elf-audit.json` and `reports/static-sha256.txt`. The audit explicitly says `chromeos_fizz_runtime_verified=false`.

## Validation on the actual ChromeOS host

No automatic deployment is performed. After retrieving the artifact, inspect its checksum and executable metadata. Only if you choose to test on the target host, run the binary as an ordinary user in a writable location and compare its read-only diagnostic output. ChromeOS security policies, mount options, kernel features and syscall restrictions may still prevent execution even when the ELF has no shared-library dependencies.

A **static musl** binary is not a substitute for the ChromeOS development sysroot when linking against ChromeOS-specific shared libraries, building kernel modules or replacing system components.

Build remains on GitHub-hosted Ubuntu runners: no full 296-project checkout, no Chromebook SDK installation, no modifications to host partitions.
