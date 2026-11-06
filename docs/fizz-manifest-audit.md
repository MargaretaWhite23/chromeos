# Fizz R150 public-source reproducibility: second gate

The host lacks standard C headers, startup objects and a compiler. Building a sysroot from its runtime filesystem alone is insufficient.

ChromiumOS public release branch `release-R150-16700.B` is a **release family**, not evidence of byte-for-byte equivalence with Google's official `fizz-release/R150-16700.66.0` image. Official documentation notes that partners may need project-specific buildspecs and private project repositories: https://chromium.googlesource.com/chromiumos/config/+/refs/heads/release-R150-16700.B

## Manifest audit workflow

[Audit Fizz R150 manifest dependencies](../.github/workflows/audit-fizz-manifest.yml) downloads the public manifest at the release branch, records its commit, inspects XML project metadata and manifest includes, and publishes `manifest-audit.json`. It fails if manifest XML or direct includes cannot be resolved.

**Scope limitation:** This is a metadata-only gate. It does not resolve nested manifest projects fully, fetch every project, run `repo sync`, bootstrap `cros_sdk`, run `setup_board --board=fizz`, build target packages, or demonstrate exact official 16700.66.0 compatibility. A successful metadata audit does **not** imply that the full public build works.

## Next gate after an audit

Use a large-storage dedicated runner (rather than assuming a standard Ubuntu GitHub-hosted runner has adequate space) to perform a pinned `repo init`/`repo sync` and ChromiumOS SDK setup. Record the manifest revision, toolchain and all unavailable packages. Do not publish a Fizz sysroot as verified until the board setup and compile/link tests pass. Then compare ELF ABI with the host and run a test executable on the real device.

Sources: https://www.chromium.org/chromium-os/developer-library/guides/device/flashing-chromiumos/ and https://chromium.googlesource.com/chromiumos/overlays/board-overlays/
