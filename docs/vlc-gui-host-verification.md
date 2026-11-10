# Native VLC GUI on ChromeOS — host verification and handoff (2026-11-10)

## Status

**Native runtime and H.264 decode: verified. Native Wayland video output initialization: verified. Stable playback and visible video: not yet verified. Shutdown: FAIL (SIGSEGV, exit 139). Full VLC GUI controls: not implemented.**

This document records actual ChromeOS host tests to resume debugging later. Do not describe this build as production-ready.

## Build provenance

- Repository: `MargaretaWhite23/chromeos`
- Source/build branch: `feature/vlc-native-wayland-gui`
- Test/documentation branch: `feature/vlc-gui-host-smoke-test`
- Successful GitHub Actions build: https://github.com/MargaretaWhite23/chromeos/actions/runs/42736588979
- Artifact: `vlc-chromeos-x86_64-musl` (ZIP; checksum validated on host)
- VLC: `3.0.24 Vetinari (3.0.24-rc1-0-g6de05adcba)`, Alpine GCC 15.2.0, x86_64 musl
- Package contains `libxdg_shell_plugin.so`, `libwl_shm_plugin.so` and `vlc-wayland`.
- The launcher uses `-I dummy` and is a video-output launcher, **not a conventional VLC GUI**. Qt/skins2 were disabled in the build.

## ChromeOS environment and staging

- ChromeOS x86_64; compositor socket `/run/chrome/wayland-0` owned by `chronos:wayland` (mode 660).
- `chronos` is uid 1000 and belongs to group `wayland`; SELinux context during successful version test: `u:r:chromeos:s0`.
- Downloads filesystem is `noexec`; executable package was copied to `/usr/local/tmp/vlc-gui-test-20261110` (executable mount).
- Extracted package was approximately 549 MB; available host disk space was approximately 2.5 GB (98% used). Avoid additional large copies.
- The ChromeOS shell bridge executes commands in plain-text `[in]...[/in]` blocks; Crostini shell uses `[vin]...[/vin]`. Protocol repository: https://github.com/MargaretaWhite23/bridge
- Root execution correctly fails: `VLC is not supposed to be run as root`. ChromeOS lacks `su`, `runuser`, and `setpriv`; `sudo -u chronos` works.
- Verified: `sudo -u chronos /bin/sh -c 'cd /usr/local/tmp/vlc-gui-test-20261110 && ./cvlc --version'` returned version 3.0.24, exit 0.
- `gdb` is available at `/usr/local/bin/gdb`, and `strace` at `/usr/local/bin/strace`; `lldb`, `eu-stack`, `addr2line`, `readelf` were not found in PATH. `ulimit -c` was 0.

## Playback reproduction and results

A short existing MP4 (~60 KB) was selected from Downloads. The `vlc-wayland` launcher was run as `chronos` with `WAYLAND_DISPLAY=/run/chrome/wayland-0`, `--vout=wl_shm --no-audio --no-video-title-show -vv` and a 20-second timeout.

Log: `/usr/local/tmp/vlc-wayland-playback.log` (host-local; not uploaded).

Result: `VLC_PLAYBACK_EXIT=139` (segmentation fault). Important ordered observations:

1. `xdg_shell window debug: global 42: xdg_wm_base version 3`
2. `xdg_shell window error: server-side decoration not supported`
3. `main window debug: using vout window module "xdg_shell"`
4. `main vout display debug: using vout display module "wl_shm"`
5. Initial video-converter attempts repeatedly failed with `Too high level of recursion (3)` / `Failed to create video converter`, but a later `swscale` I420-to-RV32 conversion succeeded.
6. `main decoder debug: Received first picture`; decoder wait completed in 65 ms. This proves decoding and output setup, **not visible presentation**.
7. `xdg_shell window error: request 3 not implemented` (relationship to crash unknown).
8. `main input debug: EOF reached`, playlist exits, video output teardown begins.
9. `main vout display debug: removing module "wl_shm"`
10. `timeout: the monitored command dumped core`; `Segmentation fault`.

The short clip reaches EOF; crash appears during teardown, but no backtrace exists yet. A longer-playing clip and a debugger backtrace are required to distinguish teardown, window protocol, buffer lifetime, and decoder-related faults.

The prior attempt to use `fake:// --fake-width=640` failed before playback: this VLC build does not recognize `--fake-width`. Do not reuse that test unchanged.

## Next steps when resuming

1. **Capture GDB backtrace** on ChromeOS as `chronos` using the musl loader and executable. First verify GDB compatibility with the musl process and choose a non-sensitive MP4. Set `set pagination off`, `set confirm off`, `run`, `thread apply all bt`; capture output to a host-local text log. Do not alter system libraries or enable setuid.
2. Reproduce with a longer local clip and compare EOF shutdown versus stopping an active playback session. Record exit status and whether any video window/frame was visibly displayed.
3. Inspect VLC 3.0.24 `modules/video_output/wayland/shm.c` and XDG shell cleanup paths; use the backtrace to choose the patch. Examine `request 3 not implemented` but do not assume it is the crash cause.
4. Investigate the earlier video converter recursion separately. Confirm reliable I420-to-RV32 conversion.
5. Patch in a dedicated branch, run GitHub Actions, verify artifact checksum, and repeat host smoke test. Keep known-good headless build intact.
6. Only after stable video output: implement a native Wayland control surface (play/pause, seek, volume, open file, fullscreen), because `-I dummy` has no controls. Test resizing, audio, A/V sync, repeated launches, and clean shutdown before production readiness.

## Safe host reproduction skeleton

```sh
DIR=/usr/local/tmp/vlc-gui-test-20261110
VIDEO=/path/to/approved-test.mp4
sudo -u chronos /bin/sh -c '
  cd /usr/local/tmp/vlc-gui-test-20261110 || exit 1
  export WAYLAND_DISPLAY=/run/chrome/wayland-0
  timeout 20 ./vlc-wayland --vout=wl_shm --no-audio --no-video-title-show -vv "$1"
' sh "$VIDEO"
```

Never treat exit 124 as proof of rendered video; confirm the window visually. Avoid exposing the private filename or video content in public repository logs.

## Related smoke-test documentation

See `scripts/test-vlc-wayland-host.sh` in this branch. Its checks and assumptions should be reviewed against the verified ChromeOS mount/identity findings above before use.
