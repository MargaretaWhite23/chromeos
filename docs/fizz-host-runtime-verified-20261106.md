# Verified ChromeOS Fizz execution — 2026-11-06

## Result

**PASS:** A statically linked x86-64 musl executable compiled on GitHub Actions without a ChromiumOS SDK or complete ChromiumOS checkout executed successfully on the actual ChromeOS host.

- Source: `tests/fizz-static-probe.c`
- GitHub Actions run: https://github.com/MargaretaWhite23/chromeos/actions/runs/42304793051
- Artifact: `fizz-minimal-no-sdk-host-abi`
- Executable: `output/fizz-static-probe`
- SHA-256: `29b9aca4777f0d72d68a113d5a419c3279b347d20e367a39914d1570678b721d`
- Static ELF audit: x86-64, no PT_INTERP, no DT_NEEDED
- Runner smoke test: passed
- ChromeOS host execution: **exit code 0**, `FIZZ_STATIC_PROBE_COMPLETE`
- Bridge host result: `CHROMEOS_STATIC_BINARY_EXECUTION_PASS`

## Verified host environment

- `CHROMEOS_RELEASE_BOARD=fizz-signed-mp-v21keys`
- `CHROMEOS_RELEASE_BUILDER_PATH=fizz-release/R150-16700.66.0`
- `CHROMEOS_RELEASE_VERSION=16700.66.0`
- `CHROMEOS_RELEASE_CHROME_MILESTONE=150`
- `CHROMEOS_RELEASE_TRACK=ltc-channel`
- `DEVICETYPE=CHROMEBOX`
- `KERNEL_RELEASE=5.4.302-23860-g99bb19cb02b8`
- `ARCHITECTURE=x86_64`

## Execution path and mount behavior

The artifact was downloaded in Crostini with `gh run download` and staged through `/mnt/chromeos/MyFiles/Downloads/fizz-static-probe` to the ChromeOS host. The host SHA-256 matched the CI artifact.

Direct execution from `/home/chronos/user/MyFiles/Downloads/fizz-static-probe` failed with exit 126, `Permission denied`: `/home/chronos/user` was mounted `noexec`. This was **not** a compatibility failure.

The host showed `/usr/local` mounted `rw` without `noexec`. The verified binary was copied to `/usr/local/fizz-static-test/fizz-static-probe` and executed there. The executable printed the kernel/OS-release information and `FIZZ_STATIC_PROBE_COMPLETE`, returning exit code 0. The temporary test copy and directory were removed afterward.

## Scope and limitations

This validates the **specific static musl program** and execution path on this specific ChromeOS host. It does not establish compatibility for arbitrary binaries, shared-library dependencies, privileged APIs, ChromeOS system services, or other boards. The test ran through the ChromeOS host shell bridge, which reported `uid=0(root)` and SELinux context `u:r:cros_browser:s0`; it does **not** establish unprivileged chronos-user execution. No security settings or mount flags were changed.

## Reproduction

1. Build with `.github/workflows/fizz-minimal-no-sdk-build.yml` on GitHub Actions.
2. Download the `fizz-minimal-no-sdk-host-abi` artifact with Crostini `gh run download`.
3. Verify `reports/static-sha256.txt` and ELF audit.
4. Stage the binary into ChromeOS Downloads through Crostini shared files.
5. On the ChromeOS host, verify SHA-256 and check mount options.
6. Execute from an existing writable executable filesystem (observed `/usr/local`) without changing mount options.
7. Confirm `FIZZ_STATIC_PROBE_COMPLETE` and exit 0; remove temporary test copy.
