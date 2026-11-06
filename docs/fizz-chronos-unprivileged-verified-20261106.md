# ChromeOS Fizz unprivileged static executable verification — 2026-11-06

## Verified result

**PASS:** `fizz-runtime-capabilities`, a static musl x86-64 executable compiled in GitHub Actions without the ChromiumOS SDK, ran on the real ChromeOS Fizz host as the `chronos` user (UID 1000), exiting 0.

- Workflow run: https://github.com/MargaretaWhite23/chromeos/actions/runs/42305434291 (success)
- Artifact: `fizz-minimal-no-sdk-host-abi`
- Executable: `output/fizz-runtime-capabilities`
- SHA-256: `f26626681ec8e910fa6aa9e540cb5a29679fc5afa47c7a22fe1c4f4c82f73c77`
- Staging path in Crostini: `/mnt/chromeos/MyFiles/Downloads/fizz-runtime-capabilities`
- Staging path on ChromeOS: `/home/chronos/user/MyFiles/Downloads/fizz-runtime-capabilities`
- Executable temporary path: `/usr/local/fizz-runtime-test/fizz-runtime-capabilities`
- Invocation: `sudo -n -u chronos /usr/local/fizz-runtime-test/fizz-runtime-capabilities`
- Temporary test copy and directory removed after execution.

## Actual ChromeOS host output

```text
RUNTIME_ARCH=x86_64
RUNTIME_KERNEL=5.4.302-23860-g99bb19cb02b8
RUNTIME_UID=1000
RUNTIME_EUID=1000
RUNTIME_GID=1000
STATUS_Uid: 1000 1000 1000 1000
STATUS_Gid: 1000 1000 1000 1000
STATUS_CapEff: 0000000000000000
STATUS_NoNewPrivs: 0
STATUS_Seccomp: 0
SELINUX_CONTEXT=u:r:cros_browser:s0
FIZZ_RUNTIME_CAPABILITIES_COMPLETE
CHRONOS_RUNTIME_EXIT_CODE=0
FIZZ_UNPRIVILEGED_STATIC_EXECUTION_PASS
FIZZ_RUNTIME_TEST_COMPLETE
```

## Interpretation

The process ran with UID, effective UID and GID 1000, no effective Linux capabilities, and exit code 0. The observed SELinux context was `u:r:cros_browser:s0`, unchanged from the root shell bridge context. `Seccomp: 0` and `NoNewPrivs: 0` describe this specific process only, not other ChromeOS processes.

The Downloads directory was `noexec`; the same verified binary was copied to the existing writable executable `/usr/local` filesystem. No mount flags, SELinux settings, or security policy were changed.

## Limits

This verifies this particular executable, this host, and this launch method. It does not establish compatibility for arbitrary dynamically linked executables or ChromeOS-specific APIs. The host-side shell bridge was initially root and used `sudo -n -u chronos` to launch the program.
