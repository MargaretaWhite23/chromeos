# Finding a usable Fizz sysroot

The GitHub Actions build workflow requires an externally supplied sysroot. Official ChromiumOS guidance says publicly downloadable prebuilt SDKs are generally available for **generic boards only**, so we cannot assume a public Fizz 16700.66.0 sysroot exists.

References:
- https://www.chromium.org/chromium-os/developer-library/guides/development/simple-chrome-workflow/
- https://www.chromium.org/chromium-os/developer-library/reference/tools/gsutil/
- https://www.chromium.org/chromium-os/developer-library/reference/tools/cros-tools/

## First: read-only host inventory

Run `scripts/inventory-fizz-build-prereqs.sh` on the ChromeOS host. It reports the OS version, compilers, glibc, headers, startup objects and existing sysroot locations, without modifying anything. It does **not** attempt to create an archive or upload system libraries.

A functioning native development environment needs more than runtime libraries. In particular, linking C executables generally requires C headers, glibc development linker scripts and startup objects (such as `crt1.o`), compiler runtime and a compatible linker.

## Decision

- **All development prerequisites present:** consider constructing a sysroot archive from verified development files, preserving paths and symlinks, and run a test compile locally before using it in GitHub Actions.
- **Only runtime libraries present:** do not label a copy of `/usr` as a build sysroot. Obtain or build a matching sysroot using ChromiumOS SDK/Portage tooling or trusted matching development packages.
- **No verified Fizz 150 sysroot:** keep the workflow failing closed. Do not substitute `amd64-generic` or Ubuntu libraries silently.

The current GitHub workflow verifies an archive checksum and structural prerequisites; those checks alone cannot establish that its content actually corresponds to Fizz 16700.66.0. An actual build and on-device execution test remain necessary.

Do not reboot or update ChromeOS as part of this investigation.
