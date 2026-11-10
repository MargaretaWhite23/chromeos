# Native ChromeOS Wayland test handoff

## Build and host

[GitHub Actions run 42729261713](https://github.com/MargaretaWhite23/chromeos/actions/runs/42729261713) passed on 10 November 2026. CI compiled the x86_64 musl Wayland test client, verified the extracted runtime and uploaded the artifact. The updated client was installed on the ChromeOS host under `/usr/local/tmp/native-wayland-v2-42729261713`.

The bundle contains `run-wayland-test`, `native-wayland-window`, `lib/ld-musl-x86_64.so.1`, `usr/lib/libwayland-client.so.0` and `usr/lib/libffi.so.8`. The host compositor socket was `/run/chrome/wayland-0`.

## Host results

| Probe | Observed result |
| --- | --- |
| Original launch | The bridge reported exit 124 after printing the launch banner. It returned no client output. |
| Direct launch with only the bundle's `lib` directory in the search path | Client exit 127. The loader could not find `libwayland-client.so.0` and reported unresolved Wayland symbols. |
| Direct launch with both `lib` and `usr/lib` in the search path | Client requested a window and logged two XDG configure events. The outer timeout escalated to SIGKILL and returned 137. No new kernel segfault messages appeared in the before/after comparison. |

The corrected launch produced:

```text
EXIT_CODE=137
WAYLAND_WINDOW_REQUESTED
WAYLAND_XDG_CONFIGURED
WAYLAND_XDG_CONFIGURED
```

The configure events confirm that the updated client communicated with the compositor and received XDG configuration. This run left frame visibility and clean shutdown unverified. It emitted no `WAYLAND_WINDOW_EXIT` marker. Exit 137 is from the forced termination in this probe.

## Reproduce on the ChromeOS host

Use a plain-text Bridge block with `[in]` and `[/in]` for ChromeOS host commands. Use `[vin]` and `[/vin]` for GitHub CLI commands in Crostini.

```sh
runtime=/usr/local/tmp/native-wayland-v2-42729261713
XDG_RUNTIME_DIR=/run/chrome WAYLAND_DISPLAY=wayland-0 \
    timeout -k 2 8 "$runtime/lib/ld-musl-x86_64.so.1" \
    --library-path "$runtime/lib:$runtime/usr/lib" \
    "$runtime/native-wayland-window"
printf 'EXIT_CODE=%s\n' "$?"
```

## Resume here

1. Give the diagnostic client a short internal deadline using a monotonic clock and a bounded Wayland event wait so it can reach normal cleanup even if no further compositor events arrive.
2. Rebuild and run on ChromeOS with an outer timeout longer than the client's deadline. Capture callback and dispatch diagnostics, the shutdown marker, the exit code and new kernel messages.
3. Confirm that a frame was visibly displayed, the client logged `WAYLAND_WINDOW_EXIT` and exited with code 0, and the kernel logged no new client segfault.
4. After those checks pass, begin integrating VLC video rendering into the native Wayland window.
