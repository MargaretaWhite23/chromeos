# Fizz ChromeOS 150 GitHub Actions build

Workflow: [Build ChromeOS Fizz binaries](../.github/workflows/build-chromeos-fizz.yml)

Target: Fizz, ChromeOS 150 / 16700.66.0, x86_64. Runs on GitHub-hosted `ubuntu-24.04` and compiles `examples/hello.c` with Clang against a **supplied** Fizz-compatible sysroot. The workflow never substitutes Ubuntu headers/libraries or `amd64-generic`.

## Why a supplied sysroot is required

ChromiumOS documentation says publicly downloadable Chrome SDK sysroots are available for generic boards, not necessarily official device-specific boards such as Fizz. Do **not** assume that a public official Fizz 16700.66.0 sysroot URL exists. See [ChromiumOS Simple Chrome](https://chromium.googlesource.com/chromiumos/docs/+/HEAD/simple_chrome_workflow.md) and [ChromeOS GS buckets](https://www.chromium.org/chromium-os/developer-library/reference/tools/gsutil/).

A Fizz sysroot must be obtained from a trusted, appropriately licensed source or exported from a matching build environment. **A filesystem copied from the running device is not automatically a complete linkable SDK sysroot**; it may lack development headers, `crt1.o`, unversioned linker libraries, and toolchain files.

## Running

From **Actions → Build ChromeOS Fizz binaries → Run workflow**, provide:

- `sysroot_url`: HTTPS download URL of a tar archive containing the sysroot root directory (`usr/include`, `usr/lib*`, `lib*`) at archive root.
- `sysroot_sha256`: trusted SHA-256 digest for that exact archive.

The job checks HTTP access, verifies SHA-256, rejects path traversal, validates basic headers/runtime/startup objects, then compiles, checks ELF and uploads an artifact. Missing or inaccessible sysroots fail with an explicit GitHub Actions error. **There is no generic-board or Ubuntu fallback.**

**Limitations:** Archive checksum verifies integrity relative to the provided hash, not that the archive is genuinely a Fizz 16700.66.0 sysroot. The current workflow checks structure and emits a target label based on the declared source; it does not cryptographically attest board/version provenance. It uses Ubuntu's Clang driver and target sysroot rather than the official pinned ChromeOS compiler, and the compiler may still need additional target-specific runtime libraries. A successful build does not guarantee compatibility with the host. Review the ELF interpreter, `NEEDED` libraries and symbol versions, then run on the actual ChromeOS machine before deploying.

Do not pass an untrusted sysroot archive. Do not use this workflow to install or modify ChromeOS itself.
