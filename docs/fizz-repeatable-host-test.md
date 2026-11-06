# Repeatable ChromeOS Fizz host test

Build in GitHub Actions. Test on the actual ChromeOS host separately.

Crostini bridge `[vin]`:
```sh
bash scripts/fizz-stage-github-artifact.sh RUN_ID fizz-runtime-capabilities
```
This monitors the run, exits 0 with BUILD_STILL_RUNNING if unfinished, downloads into a unique run-specific directory (preventing GitHub CLI extraction collisions), verifies the artifact checksum, and stages a run-specific binary in shared ChromeOS Downloads.

ChromeOS host bridge `[in]`:
```sh
bash /home/chronos/user/MyFiles/Downloads/fizz-test-on-chromeos.sh RUN_ID fizz-runtime-capabilities SHA256
```
First copy `scripts/fizz-test-on-chromeos.sh` from the repository to ChromeOS Downloads via Crostini. The host script checks SHA256, copies into a unique directory under executable `/usr/local`, invokes `sudo -n -u chronos`, records the exit code, and cleans up. The shell bridge on this device is root, while the target binary runs as UID 1000.

No remounts or security policy changes. This only verifies binaries on the actual ChromeOS host when the host command is run and its output inspected; GitHub runner success alone is insufficient.
