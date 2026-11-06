# Fizz unattended GitHub Actions → Crostini → ChromeOS host tests

## Status

**Implementation candidate, not yet proven unattended on the real host.**
The manually initiated end-to-end test has already been verified in [run 42306108497](https://github.com/MargaretaWhite23/chromeos/actions/runs/42306108497) and the [verification report](fizz-end-to-end-verified-42306108497.md).

## Design

- GitHub Actions builds daily at 03:17 UTC, on pushes affecting the workflow, and via manual dispatch. CI runs syntax/stdlib tests; it **cannot** claim actual ChromeOS execution.
- Crostini's systemd **user** timer polls completed successful `main` workflow runs every five minutes, choosing the most recent run. It uses the authenticated `gh` CLI and the existing SHA-256-verifying staging script. It writes one JSON request under shared Downloads (`fizz-automation/requests/run-<ID>.json`). State persists under `~/.local/state/fizz-automation/state.json`. An exclusive local lock avoids duplicate polls. Intermediate failures retain state and retry.
- ChromeOS worker `scripts/fizz-host-worker.py` polls requests (default every 30 seconds), checks the requested binary name, run ID and hashes, and invokes the root-owned, already installed `/usr/local/fizz-testing/fizz-test-on-chromeos.sh`. That script copies the binary into an executable directory and executes the **binary as chronos**, not root. The worker writes a run-specific JSON result in `fizz-automation/results`.
- Crostini reads a matching host result and attempts to publish a GitHub commit status under `fizz/real-chromeos-host`. This depends on GitHub CLI credentials having commit-status write permission. If publication fails, the result remains in the local state and is retried. A GitHub-hosted build success is never itself reported as a real ChromeOS pass.

## Setup on Crostini — using bridge `[vin]`

```sh
gh repo clone MargaretaWhite23/chromeos "$HOME/chromeos" -- --branch main
cd "$HOME/chromeos"
bash scripts/install-fizz-crostini-timer.sh
systemctl --user list-timers fizz-crostini-monitor.timer
systemctl --user start fizz-crostini-monitor.service
journalctl --user -u fizz-crostini-monitor.service -n 60 --no-pager
```

Re-use or update an existing clone rather than running `gh repo clone` over it. The user timer requires the Crostini user manager to be running. It does **not** keep a stopped Crostini container alive or guarantee run-on-reboot across ChromeOS sessions. Do not enable linger or change system services solely to force Crostini to stay running.

## Stage ChromeOS worker from Crostini

```sh
cp "$HOME/chromeos/scripts/fizz-host-worker.py" /mnt/chromeos/MyFiles/Downloads/fizz-host-worker.py
sha256sum "$HOME/chromeos/scripts/fizz-host-worker.py" /mnt/chromeos/MyFiles/Downloads/fizz-host-worker.py
```

## Install and test on ChromeOS — using bridge `[in]`

```sh
test -f /home/chronos/user/MyFiles/Downloads/fizz-host-worker.py
cp /home/chronos/user/MyFiles/Downloads/fizz-host-worker.py /usr/local/fizz-testing/fizz-host-worker.py
chmod 755 /usr/local/fizz-testing/fizz-host-worker.py
/usr/local/bin/python3 -m py_compile /usr/local/fizz-testing/fizz-host-worker.py
/usr/local/bin/python3 /usr/local/fizz-testing/fizz-host-worker.py --once
```

**Do not start the long-lived host worker until the host test is confirmed.** Once validated and approved, it can be launched as a detached session process, with a PID/log under `/usr/local/fizz-testing`. ChromeOS uses Upstart; installing a persistent Upstart job is **not** implemented because the host's writable init job search path is not yet established and the root filesystem may be read-only. A detached worker does not survive reboot.

## Troubleshooting

- `FIZZ_NO_NEW_RUN`: there is no more recent completed successful main workflow run.
- `FIZZ_HOST_TEST_REQUESTED`: new run staged for host execution.
- `FIZZ_HOST_RESULT_PENDING`: host has not yet written a result.
- `FIZZ_HOST_WORKER_RESULT ... PASS`: host executed and verified marker output.
- `FIZZ_HOST_RESULT_SUCCESS`: monitor consumed actual host result and submitted success status.
- `FIZZ_MONITOR_ERROR`: inspect `journalctl --user -u fizz-crostini-monitor.service`.
- GitHub status API may reject writes because of repository permissions. In that case the host result remains available locally. The worker writes results in the shared directory, but a shared-file report is **not cryptographic remote attestation**.

## Security boundary

This is intentionally **not a general-purpose remote shell** and it opens no TCP port. Binary name is fixed to `fizz-runtime-capabilities`; requests are strict JSON; no request-supplied executable path or shell command is accepted. The installed host-test script must be root-owned and not group/other writable. The tested executable runs as UID/EUID 1000 with no effective Linux capabilities, within the observed SELinux context `u:r:cros_browser:s0`.

However, the shared Downloads directory is writable by Crostini/chronos. A party able to alter both an artifact and its accompanying SHA-256 can request execution of arbitrary machine code **as chronos**. SHA-256 is transfer integrity, **not publisher authentication**. GitHub statuses derived from files in this shared directory can also be spoofed by local writers. Keep this test system confined to trusted local accounts. Before treating this as a production security boundary, add independent signed artifact provenance verified on the host and authenticated result reporting. Do not run with privileged user-supplied shell commands, add a network listener, or weaken ChromeOS mount/SELinux policy.

## Disable

Crostini:
```sh
systemctl --user disable --now fizz-crostini-monitor.timer
```

ChromeOS: stop the dedicated host worker process if manually launched; this does not affect `upstart-socket-bridge`.
