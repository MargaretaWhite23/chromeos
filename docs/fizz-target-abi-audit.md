# Fizz no-SDK ELF ABI audit

The standalone GitHub Actions build records the x86-64 binary's ELF interpreter, shared-library dependencies and GLIBC versioned-symbol requirements in `reports/fizz-elf-abi-audit.json`.

Without a verified device profile, the audit states `UNVERIFIED_NO_TARGET_PROFILE`. A passing Ubuntu-runner build is not proof of target compatibility.

On the actual ChromeOS host (not Crostini), gather read-only evidence using `getconf GNU_LIBC_VERSION`, `readelf -l /bin/sh`, and inspection of the loader and libraries under `/lib64` and `/usr/lib64`. Do not invent profile values.

An optional profile JSON supplies `available_interpreters` (array of absolute paths), `libraries` (array of SONAMEs) and `glibc_version` (string). Compare with `python3 scripts/audit-fizz-elf-abi.py --binary output/fizz-hello-host-abi --profile fizz-profile.json`.

This check covers only reported loader, library and GLIBC requirements, not complete ChromeOS runtime behavior. No SDK or source checkout is required.
