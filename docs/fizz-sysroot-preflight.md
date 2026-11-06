# Fizz 16700.66.0: source/sysroot preflight

The full pinned public buildspec audit verified **296/296** accessible Git revisions and the limited checkout passed in [GitHub Actions run 42293926604](https://github.com/MargaretaWhite23/chromeos/actions/runs/42293926604), using approximately 798 MB and leaving around 13 GB on the hosted runner.

## Bounded next step

The new workflow \`probe-fizz-sysroot-prereqs.yml\`:
1. Repeats the pinned three-project checkout with the already tested script.
2. Looks up the exact pinned crosutils project in the release buildspec.
3. Requires at least 5 GiB available, then syncs only that additional project (single worker and a 5-minute timeout).
4. Checks Git revision pins, Fizz overlay paths, and discoverable crosutils SDK/board setup tools.
5. Uploads a JSON diagnostic report and logs.

**It does not run** a full repo sync, cros_sdk, setup_board, build_packages, or a binary compiler. A passing preflight means that more required source components were retrieved and inspected; it is not a sysroot build. The space check is a preflight gate, not a hard quota.

## Actual build requirements

The official ChromiumOS developer guide documents board setup and the board-specific /build/fizz sysroot inside a prepared SDK. Actual release-binary compatibility needs matching toolchain, headers, crt startup objects, libraries and on-device execution checks. The public buildspec is not proof that proprietary Google ChromeOS build components are available.

Reference: https://www.chromium.org/chromium-os/developer-library/guides/development/developer-guide/

Next: estimate full checkout/SDK size, choose an appropriately sized persistent Linux builder, perform pinned repo sync and SDK initialization, and only then attempt setup_board --board=fizz.
