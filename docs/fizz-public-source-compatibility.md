# Can public ChromiumOS reproduce official Fizz 16700.66.0?

## Findings from public source inspection (2026-11-06)

The public ChromiumOS board-overlays repository has a `release-R150-16700.B` branch and contains `overlay-fizz/` and `baseboard-fizz/`. This is **positive evidence** that public sources exist for the Fizz family at the matching R150 build-number branch.

Source: https://chromium.googlesource.com/chromiumos/overlays/board-overlays/+/refs/heads/release-R150-16700.B

However, this does **not** prove that public sources can reproduce the **official signed** `fizz-release/R150-16700.66.0` build. Exact patch-level source revisions, Google private overlays, package repositories, proprietary components and toolchain provenance may differ. Do not claim ABI equivalence without comparing linked runtime dependencies and executing a binary on the device.

## Automated public source probe

The workflow [probe-fizz-public-sources.yml](../.github/workflows/probe-fizz-public-sources.yml) runs on Ubuntu 24.04 and:

1. Checks `refs/heads/release-R150-16700.B` on the public manifest and board-overlays repositories.
2. Shallow-clones the public branch and records exact Git commits.
3. Checks for `overlay-fizz` and its toolchain configuration.
4. Records public manifest details and uploads a report even if the probe fails.
5. Exits with a clear error if required public sources are inaccessible.

This is intentionally **not** a full ChromiumOS SDK bootstrap. Full `repo sync`, `cros_sdk`, `setup_board --board=fizz` and `cros build-packages` may require substantially more disk, time and resources than a standard GitHub-hosted runner and may encounter unavailable private packages. The probe is a prerequisite gate, not a fabricated build-success signal.

## Next compatibility gates

- Determine whether the public manifest at the release branch resolves all dependencies without private repositories.
- Obtain/build the Fizz SDK sysroot with target headers, startup objects and libraries.
- Verify glibc symbols, ELF interpreter, `NEEDED` libraries and hashes against the running ChromeOS host.
- Run a simple executable on the host and document results.
- Only then supply a trusted sysroot URL and SHA-256 to the existing build workflow.

References: https://www.chromium.org/chromium-os/developer-library/guides/chromiumos-board-porting-guide/ and https://chromium.googlesource.com/chromiumos/overlays/board-overlays/+/refs/heads/release-R150-16700.B
