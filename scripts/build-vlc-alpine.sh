#!/bin/sh
set -eu

runtime=$1
version=3.0.24
archive=vlc-$version.tar.xz
checksum=e7cab503d1d7d5849b89d2cf0e1ee60d0ef6d012407791b644b9cfc0cc225fdf
work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT

apk add --no-cache build-base pkgconf curl xz ffmpeg7-dev \
  libgcrypt-dev libxml2-dev zlib-dev
cd "$work"
curl -fsSLO --retry 3 "https://get.videolan.org/vlc/$version/$archive"
printf '%s  %s\n' "$checksum" "$archive" | sha256sum -c -
tar -xf "$archive"
cd "vlc-$version"
CFLAGS="-O2 -fcommon" ./configure \
  --prefix=/usr --disable-static --disable-rpath --disable-nls \
  --disable-qt --disable-skins2 --disable-lua --disable-v4l2 \
  --disable-xcb --disable-wayland --disable-libva --disable-vdpau \
  --enable-avcodec --enable-avformat --enable-swscale --enable-sout
make -j4
make -j1 DESTDIR="$work/install" install

# Keep Alpine's runtime dependencies and replace its VLC code and modules.
rm -rf "$runtime/usr/lib/vlc" "$runtime/usr/share/vlc"
cp -a "$work/install/usr/." "$runtime/usr/"
rm -f "$runtime/usr/lib/vlc/plugins/plugins.dat"
printf 'VideoLAN VLC %s\nSource SHA-256 %s\n' "$version" "$checksum"
