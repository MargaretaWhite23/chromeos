# Exact public buildspec discovery: Fizz 16700.66.0

The public ChromiumOS `release-R150-16700.B` branch is a release-family branch, **not** a pinned snapshot of Google's official `fizz-release/R150-16700.66.0` build.

The workflow [Discover exact Fizz R150 public buildspec](../.github/workflows/discover-fizz-buildspec.yml) tests whether the exact public buildspec is available at:

`https://storage.googleapis.com/chromiumos-manifest-versions/buildspecs/150/16700.66.0.xml`

It checks download accessibility, parses the manifest, records project counts and a SHA-256 digest, and uploads evidence on both success and failure. It fails with a clear error if the file is absent or inaccessible.

This location follows ChromiumOS documentation's public buildspec naming convention, **not** a previously verified file location. The workflow is the availability test; do not report the buildspec as found until the run succeeds.

Even if found, public buildspecs may omit private Fizz overlays, proprietary packages or release-specific Google configuration. Full official image reproduction remains unproven. For standalone manifest checkout, ChromiumOS documentation describes `repo init --standalone-manifest gs://chromiumos-manifest-versions/buildspecs/<milestone>/<version>.xml`, followed by `repo sync`; that is a subsequent, resource-intensive step.

Reference: https://www.chromium.org/chromium-os/developer-library/guides/debugging/recreating-a-snapshot-or-buildspec/
