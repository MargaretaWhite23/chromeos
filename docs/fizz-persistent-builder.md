# Persistent Fizz SDK builder readiness gate

This repository contains a **read-only capacity check**, not a builder installer. It gates a persistent **Linux x86_64**, non-root environment before attempting a complete pinned 296-project checkout and ChromiumOS SDK bootstrap for board \`fizz\`, public buildspec \`150/16700.66.0\`.

## Run on intended Linux builder

\`\`\`bash
mkdir -p "$HOME/fizz-build"   # choose an existing spacious filesystem
python3 scripts/check-fizz-builder-readiness.py --workdir "$HOME/fizz-build" --min-free-gib 100 --output fizz-builder-readiness.json
\`\`\`

This checks required host utilities, architecture, effective user, existence of working directory and **100 GiB of free filesystem space** (a conservative provisional safety gate, **not** a measured SDK size requirement). It returns 0 when ready and 2 when blocked. It performs no installation, sync, \`cros_sdk\`, \`setup_board\`, disk repartitioning or system changes, apart from optional JSON report creation.

A small GitHub-hosted runner is intentionally expected to be rejected. The workflow \`fizz-builder-readiness.yml\` tests both acceptance and rejection paths and uploads the runner report. Its passing result **does not** mean a full ChromiumOS build environment exists. Readiness is necessary but may not be sufficient; actual storage and SDK dependencies must be measured during incremental builder setup.

When an adequately sized persistent builder is available, independently verify its environment, check its output, and only then proceed with full pinned checkout, actual SDK bootstrap and \`setup_board --board=fizz\`. Keep source and build products outside the ChromeOS host system partition.
