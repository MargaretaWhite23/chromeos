#!/bin/sh
set -eu

runtime=$1
script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
version=3.0.24
archive=vlc-$version.tar.xz
checksum=e7cab503d1d7d5849b89d2cf0e1ee60d0ef6d012407791b644b9cfc0cc225fdf
work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT

apk add --no-cache build-base linux-headers pkgconf curl xz ffmpeg7-dev \
  libgcrypt-dev libxml2-dev zlib-dev patch wayland-dev wayland-protocols
cd "$work"
curl -fsSLO --retry 3 "https://get.videolan.org/vlc/$version/$archive"
printf '%s  %s\n' "$checksum" "$archive" | sha256sum -c -
tar -xf "$archive"
cd "vlc-$version"
patch -p1 < "$script_dir/vlc-stable-xdg-shell.patch"
sed -i 's|unstable/xdg-shell/xdg-shell-unstable-v5.xml|stable/xdg-shell/xdg-shell.xml|g' modules/Makefile.in
CFLAGS="-O2 -fcommon" ./configure \
  --prefix=/usr --disable-static --disable-rpath --disable-nls \
  --disable-qt --disable-skins2 --disable-lua --disable-v4l2 \
  --disable-xcb --enable-wayland --disable-libva --disable-vdpau \
  --disable-alsa \
  --enable-avcodec --enable-avformat --enable-swscale --enable-sout
make -j4
make -j1 DESTDIR="$work/install" appdata_DATA= install

# Keep Alpine's runtime dependencies and replace its VLC code and modules.
rm -rf "$runtime/usr/lib/vlc" "$runtime/usr/share/vlc"
cp -a "$work/install/usr/." "$runtime/usr/"
rm -f "$runtime/usr/lib/vlc/plugins/plugins.dat"
printf 'VideoLAN VLC %s\nSource SHA-256 %s\n' "$version" "$checksum"

# Include the Wayland runtime libraries needed outside Alpine.
for lib in /usr/lib/libwayland-client.so.0 /usr/lib/libffi.so.8; do
  cp -L "$lib" "$runtime/usr/lib/"
done
find "$runtime/usr/lib/vlc/plugins" -name libxdg_shell_plugin.so | grep -q .
find "$runtime/usr/lib/vlc/plugins" -name libwl_shm_plugin.so | grep -q .
cat > "$runtime/../vlc-wayland" <<'EOF'
#!/bin/sh
set -eu
ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/rootfs" && pwd)"
export VLC_PLUGIN_PATH="$ROOT/usr/lib/vlc/plugins"
export WAYLAND_DISPLAY="${WAYLAND_DISPLAY:-/run/chrome/wayland-0}"
exec "$ROOT/lib/ld-musl-x86_64.so.1" \
  --library-path "$ROOT/lib:$ROOT/usr/lib" "$ROOT/usr/bin/vlc" \
  -I dummy --ignore-config --vout wl --play-and-exit "$@"
EOF
chmod +x "$runtime/../vlc-wayland"
