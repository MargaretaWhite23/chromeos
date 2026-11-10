#!/bin/sh
# Non-destructive ChromeOS host smoke test for the VLC Wayland video window.
# Usage: sh scripts/test-vlc-wayland-host.sh /path/to/extracted/vlc-package /path/to/video.mp4
set -eu
if [ "$#" -ne 2 ]; then
  echo "Usage: $0 VLC_PACKAGE_DIR VIDEO_FILE" >&2
  exit 2
fi
pkg=$(CDPATH= cd -- "$1" && pwd)
video=$2
case "$video" in /*) ;; *) video="$(pwd)/$video";; esac
test -f "$video" || { echo "Missing video: $video" >&2; exit 2; }
test -x "$pkg/vlc-wayland" || { echo "Missing executable vlc-wayland in $pkg" >&2; exit 2; }
test -f "$pkg/rootfs/usr/bin/vlc" || { echo "Missing VLC executable" >&2; exit 2; }
test -f "$pkg/rootfs/usr/lib/vlc/plugins/video_output/libxdg_shell_plugin.so" || {
  echo "Missing XDG shell plugin" >&2; exit 2;
}
test -S /run/chrome/wayland-0 || {
  echo "ChromeOS Wayland socket not found; run on the ChromeOS host" >&2; exit 2;
}
echo "VLC_WAYLAND_HOST_TEST_START"
echo "Package: $pkg"
echo "Video: $video"
echo "Wayland socket: /run/chrome/wayland-0"
echo "Expect a visible VLC video window; confirm manually whether video and audio play."
echo "Test will terminate the VLC child after 30 seconds."
# Keep this test unprivileged and isolated: no installation, reboot, or host modifications.
if (
  cd "$pkg"
  WAYLAND_DISPLAY=/run/chrome/wayland-0 timeout 30 ./vlc-wayland -vv "$video"
); then
  rc=0
else
  rc=$?
fi
echo "VLC_WAYLAND_HOST_EXIT=$rc"
# timeout returns 124 if VLC stayed alive for the whole observation window.
case "$rc" in
  0|124) echo "VLC_WAYLAND_PROCESS_SMOKE_PASS (GUI visibility still requires human verification)";;
  *) echo "VLC_WAYLAND_PROCESS_SMOKE_FAIL" >&2; exit "$rc";;
esac
