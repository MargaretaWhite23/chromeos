# Fizz unattended GitHub Actions → Crostini → ChromeOS host tests

## Status

**Verified on the real ChromeOS Fizz host on 2026-11-06.** The GitHub Actions [post-merge run 42307539843](https://github.com/MargaretaWhite23/chromeos/actions/runs/42307539843) completed successfully, its artifact was staged by the Crostini monitor, the host worker executed it as `chronos`, and the monitor published GitHub commit status `fizz/real-chromeos-host: success` for commit `6f3bcf3a11a43d18a876bc6b8d39e77260127279`. This verifies one complete end-to-end cycle; subsequent builds and reboot recovery are not yet demonstrated. The earlier manual test is documented in [run 42306108497](https://github.com/MargaretaWhite23/chromeos/actions/runs/42306108497) and the [verification report](fizz-end-to-end-verified-42306108497.md).

## Design

- GitHub Actions builds daily at 03:17 UTC, on pushes affecting the workflow, and via manual dispatch. CI runs syntax/stdlib tests; it **cannot** claim actual ChromeOS execution.
- Crostini's systemd **user** timer polls completed successful `main` workflow runs every five minutes, choosing the most recent run. It uses the authenticated `gh` CLI and the existing SHA-256-verifying staging script. It writes one JSON request under shared Downloads (`fizz-automation/requests/run-<ID>.json`). State persists under `~/.local/state/fizz-automation/state.json`. An exclusive local lock avoids duplicate polls. Intermediate failures retain state and retry.
- ChromeOS worker `scripts/fizz-host-worker.py` runs **entirely as chronos (UID 1000)** and polls requests (default every 30 seconds). It checks the requested binary name, run ID and hashes; copies the verified artifact into a private chronos-owned executable directory under `/usr/local/fizz-testing/chronos-run`; and executes it without sudo. The worker writes a run-specific JSON result in `fizz-automation/results`. The existing root-owned interactive host-test shell script is left untouched.
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
mkdir -p /usr/local/fizz-testing/chronos-run
chown chronos:chronos /usr/local/fizz-testing/chronos-run
chmod 700 /usr/local/fizz-testing/chronos-run
/usr/local/bin/python3 -m py_compile /usr/local/fizz-testing/fizz-host-worker.py
sudo -n -u chronos /usr/local/bin/python3 /usr/local/fizz-testing/fizz-host-worker.py --once
```

The first real-host test has passed. The long-lived worker has subsequently been started **as chronos**, polling every 30 seconds. Observed process PID `713182` (ephemeral; do not rely on this PID after restart), command `/usr/lib/python-exec/python3.11/python3 /usr/local/fizz-testing/fizz-host-worker.py --interval 30`, and log lines `FIZZ_HOST_WORKER_STARTED` and repeated `FIZZ_HOST_NO_PENDING_REQUEST`. The worker is launched with `nohup` and a PID file at `/usr/local/fizz-testing/chronos-run/worker.pid`; the log is `worker.log` in that directory. This is **session persistence, not reboot persistence**. ChromeOS uses Upstart; a dedicated auto-start/restart job has **not** been installed because the writable init job search path is not yet established and the root filesystem may be read-only. Do not change the existing `upstart-socket-bridge` service.

## Verified 2026-11-06 execution and reporting

- CI workflow run: `42307539843`, completed `success`; artifact `fizz-minimal-no-sdk-host-abi` (56,854 bytes).
- Crostini monitor: `fizz-crostini-monitor.timer` enabled and active, polling every five minutes; journal recorded `FIZZ_HOST_TEST_REQUESTED RUN_ID=42307539843`, then `FIZZ_HOST_RESULT_PENDING`, then `FIZZ_HOST_RESULT_SUCCESS RUN_ID=42307539843`, followed by `FIZZ_NO_NEW_RUN`.
- Request: `fizz-automation/requests/run-42307539843.json`; binary `fizz-runtime-capabilities`; SHA-256 `f26626681ec8e910fa6aa9e540cb5a29679fc5afa47c7a22fe1c4f4c82f73c77`.
- Real host result: `fizz-automation/results/run-42307539843.json`; `passed: true`, `exit_code: 0`, empty stderr; `RUNTIME_ARCH=x86_64`, kernel `5.4.302-23860-g99bb19cb02b8`, UID/EUID/GID `1000`, effective capabilities `0`, SELinux `u:r:cros_browser:s0`, `FIZZ_RUNTIME_CAPABILITIES_COMPLETE`.
- Crostini state: `{"current": null, "last_completed": 42307539843}`. GitHub commit status API returned `fizz/real-chromeos-host` state `success` with description `ChromeOS Fizz host test success (run 42307539843)`.
- Host worker subsequently confirmed alive as `chronos` PID `713182` with `--interval 30`, reporting `FIZZ_HOST_NO_PENDING_REQUEST` during idle polling. PID is illustrative only.
- **Limitations:** Crostini timer runs only while its user manager/container is active; ChromeOS worker is not automatically restarted after host reboot; no independent signed provenance or cryptographic attestation is provided. No additional future-run automation test is yet documented.

## Troubleshooting

- `FIZZ_NO_NEW_RUN`: there is no more recent completed successful main workflow run.
- `FIZZ_HOST_TEST_REQUESTED`: new run staged for host execution.
- `FIZZ_HOST_RESULT_PENDING`: host has not yet written a result.
- `FIZZ_HOST_WORKER_RESULT ... PASS`: host executed and verified marker output.
- `FIZZ_HOST_RESULT_SUCCESS`: monitor consumed actual host result and submitted success status.
- `FIZZ_MONITOR_ERROR`: inspect `journalctl --user -u fizz-crostini-monitor.service`.
- GitHub status API may reject writes because of repository permissions. In that case the host result remains available locally. The worker writes results in the shared directory, but a shared-file report is **not cryptographic remote attestation**.

## Security boundary

This is intentionally **not a general-purpose remote shell** and it opens no TCP port. Binary name is fixed to `fizz-runtime-capabilities`; requests are strict JSON; no request-supplied executable path or shell command is accepted. The worker never needs root: its persistent process and tested executable both run as chronos UID/EUID 1000. Its executable workspace must be owned by chronos and mode 0700. The real worker-driven host test observed `RUNTIME_UID=1000`, `RUNTIME_EUID=1000`, `STATUS_CapEff: 0000000000000000`, and SELinux context `u:r:cros_browser:s0`.

However, the shared Downloads directory is writable by Crostini/chronos. A party able to alter both an artifact and its accompanying SHA-256 can request execution of arbitrary machine code **as chronos**, but not through a root runner. SHA-256 is transfer integrity, **not publisher authentication**. GitHub statuses derived from files in this shared directory can also be spoofed by local writers. Keep this test system confined to trusted local accounts. Before treating this as a production security boundary, add independent signed artifact provenance verified on the host and authenticated result reporting. Do not run with privileged user-supplied shell commands, add a network listener, or weaken ChromeOS mount/SELinux policy.

## Disable

Crostini:
```sh
systemctl --user disable --now fizz-crostini-monitor.timer
```

ChromeOS: stop the dedicated host worker process if manually launched; this does not affect `upstart-socket-bridge`.
