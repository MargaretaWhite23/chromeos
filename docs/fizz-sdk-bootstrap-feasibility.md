# Fizz SDK bootstrap feasibility gate

Workflow: \`.github/workflows/fizz-sdk-bootstrap-feasibility.yml\`

This is the next step after source inventory [run 42300102459](https://github.com/MargaretaWhite23/chromeos/actions/runs/42300102459), which found \`cros_sdk\`, \`setup_board\` and \`cros\` under \`infra/chromite-HEAD/bin/\`.

The workflow uses the exact pinned public buildspec \`150/16700.66.0.xml\`, repeats the previously tested bounded project sync, and classifies projects likely to be relevant to the SDK, toolchain, overlays, Portage and manifest. It records runner capacity and SDK command locations to \`reports/fizz-sdk-bootstrap-feasibility.json\`.

The GitHub-hosted Ubuntu runner had approximately 13 GiB free in prior successful runs. This **does not** establish enough capacity for a full 296-project checkout plus the ChromiumOS SDK. The feasibility workflow deliberately does **not** sync all projects, initialize the SDK, attempt \`setup_board\`, or build a sysroot.

Next implementation should select a sufficiently large persistent Linux builder, test \`repo sync\` for the exact pinned buildspec, install and initialize the SDK using the release-appropriate chromite commands, and then invoke \`setup_board --board=fizz\`. Record disk use and errors at each stage. Do not alter the original ChromeOS device or claim that a public buildspec reproduces proprietary Google ChromeOS components.
