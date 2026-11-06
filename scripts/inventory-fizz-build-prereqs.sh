#!/bin/sh
# Read-only ChromeOS Fizz native build prerequisites inventory.
set -u
echo '=== ChromeOS release ==='
grep -E '^(CHROMEOS_RELEASE_(BOARD|VERSION|BUILDER_PATH|CHROME_MILESTONE)|GOOGLE_RELEASE)=' /etc/lsb-release 2>/dev/null || true
echo '=== Architecture and glibc ==='
uname -m
getconf GNU_LIBC_VERSION 2>/dev/null || true
echo '=== Toolchain ==='
for cmd in clang clang++ gcc ld.lld ld readelf pkg-config; do
  if command -v "$cmd" >/dev/null 2>&1; then
    printf '%s: ' "$cmd"; command -v "$cmd"
    "$cmd" --version 2>/dev/null | head -1
  else
    echo "$cmd: unavailable"
  fi
done
echo '=== Headers ==='
for f in /usr/include/stdio.h /usr/local/usr/include/stdio.h /usr/include/features.h /usr/local/usr/include/features.h /usr/include/linux/types.h /usr/local/usr/include/linux/types.h; do
  if [ -f "$f" ]; then echo "PRESENT $f"; else echo "MISSING $f"; fi
done
echo '=== Link startup objects ==='
for f in /usr/lib64/crt1.o /usr/lib/crt1.o /usr/local/usr/lib64/crt1.o /usr/local/usr/lib/crt1.o /usr/lib64/crti.o /usr/local/usr/lib64/crti.o; do
  if [ -f "$f" ]; then echo "PRESENT $f"; else echo "MISSING $f"; fi
done
echo '=== libc and linker candidates ==='
for f in /lib64/libc.so.6 /usr/lib64/libc.so.6 /usr/local/lib64/libc.so.6 /usr/lib64/libc.so /usr/local/usr/lib64/libc.so /lib64/ld-linux-x86-64.so.2; do
  if [ -e "$f" ]; then ls -l "$f"; else echo "MISSING $f"; fi
done
echo '=== Portage package locations ==='
for d in /usr/local/var/db/pkg /usr/local/etc/portage /mnt/stateful_partition/dev_image/usr/include /mnt/stateful_partition/dev_image/usr/lib64; do
  if [ -d "$d" ]; then echo "PRESENT $d"; else echo "MISSING $d"; fi
done
echo '=== Existing SDK/sysroot directories ==='
for d in /build/fizz /usr/local/build/fizz /usr/local/usr/x86_64-cros-linux-gnu /usr/local/usr/x86_64-pc-linux-gnu; do
  if [ -d "$d" ]; then echo "PRESENT $d"; else echo "MISSING $d"; fi
done
echo '=== END: no changes made ==='
