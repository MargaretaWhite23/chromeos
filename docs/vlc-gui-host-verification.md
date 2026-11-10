# Native VLC GUI: ChromeOS host verification

## Current status

The VLC 3.0.24 musl package builds and passes a headless transcode test.
It contains Wayland XDG shell and wl_shm plugins. The `vlc-wayland`
launcher still uses `-I dummy`; it is **not a full graphical user
interface**. The standalone native Wayland window test is not evidence that
VLC itself can display video.

## Controlled host test

Download the artifact from GitHub Actions run 42736588979 and verify the
included ZIP checksum before extracting. Do not overwrite ChromeOS system
libraries. Extract the package to a writable temporary directory on the
ChromeOS host. Provide a local, non-sensitive MP4 test clip.

Run the script in this branch from a ChromeOS host shell:

```sh
sh scripts/test-vlc-wayland-host.sh /path/to/extracted-package /path/to/test.mp4
```

The script checks the package layout and ChromeOS Wayland socket, launches
the VLC Wayland output for up to 30 seconds, and reports its process result.
A timeout code of 124 means only that the process survived the observation
window, **not** that a video frame was displayed.

Record separately:
- Visible VLC video window and first rendered frame
- Video playback, audio playback and synchronization
- Window resizing and fullscreen
- Seeking, pause/resume and volume (not available as GUI controls yet)
- Clean shutdown, error logs, and reproducibility across ChromeOS sessions

## Next implementation milestone

Create a native Wayland control surface, integrate it with libVLC
playback APIs, and test the combined GUI on real ChromeOS. The current
headless build intentionally disables Qt and skins2, so merely running
`vlc-wayland` does not produce a conventional VLC control panel.
Keep the verified headless package unchanged until GUI functionality passes
its own tests.
