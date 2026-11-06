# Verified end-to-end GitHub Actions → Crostini → ChromeOS Fizz test

**Result: PASS** — 2026-11-06. The user-provided shell bridge output confirms that the scripts introduced in PR #7 completed the end-to-end test on the real ChromeOS Fizz host.

## GitHub Actions

- Repository: `MargaretaWhite23/chromeos`
- Run: https://github.com/MargaretaWhite23/chromeos/actions/runs/42306108497
- Conclusion: success
- Shell syntax validation, ELF ABI parser test, standalone build and artifact upload: passed
- Artifact: `fizz-minimal-no-sdk-host-abi`

## Crostini `[vin]` staging

The staging script `scripts/fizz-stage-github-artifact.sh` reported:

```text
output/fizz-runtime-capabilities: OK
output/fizz-runtime-capabilities: OK
STAGED_FILE=/mnt/chromeos/MyFiles/Downloads/fizz-42306108497-fizz-runtime-capabilities
SHA256=f26626681ec8e910fa6aa9e540cb5a29679fc5afa47c7a22fe1c4f4c82f73c77
FIZZ_ARTIFACT_STAGED
FIZZ_PIPELINE_CROSTINI_COMPLETE
```

ChromeOS `[in]` independently confirmed the file was visible, 53,088 bytes, owned by chronos, and matched the same SHA-256 (`FIZZ_CHROMEOS_STAGING_VISIBLE`).

## Actual ChromeOS `[in]` execution

The host invoked:

```sh
bash /home/chronos/user/MyFiles/Downloads/fizz-test-on-chromeos.sh \
  42306108497 fizz-runtime-capabilities \
  f26626681ec8e910fa6aa9e540cb5a29679fc5afa47c7a22fe1c4f4c82f73c77
```

Observed output:

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
CHROMEOS_EXIT_CODE=0
FIZZ_HOST_TEST_PASS
FIZZ_PIPELINE_HOST_EXIT_CODE=0
FIZZ_END_TO_END_PIPELINE_PASS
```

The shell emitted a warning about running the **script** from a `noexec` Downloads mount; the script nevertheless completed, and the **binary** ran from a temporary executable location under `/usr/local`. No security policy or mount settings were changed. Future tests can stage the trusted script in `/usr/local` to avoid the warning.

## Scope of verification

This verifies the tested GitHub Actions artifact, Crostini staging and ChromeOS Fizz execution as UID/EUID 1000 with no effective Linux capabilities. The process retained the observed `u:r:cros_browser:s0` SELinux context. The reported seccomp and no-new-privileges settings describe this process, not all ChromeOS processes. It does not prove general binary compatibility, unattended scheduling, or automated host-to-GitHub result publication.
