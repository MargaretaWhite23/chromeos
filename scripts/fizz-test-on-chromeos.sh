#!/bin/bash
set -u
RUN="$1"
NAME="$2"
EXPECTED="$3"
case "$RUN" in *[!0-9]*|"") exit 2;; esac
case "$NAME" in fizz-runtime-capabilities|fizz-static-probe) ;; *) exit 2;; esac
case "$EXPECTED" in *[!0-9a-f]*|"") exit 2;; esac
test "$(printf %s "$EXPECTED" | wc -c)" -eq 64 || exit 2
SOURCE="/home/chronos/user/MyFiles/Downloads/fizz-$RUN-$NAME"
test -f "$SOURCE" || { echo STAGED_FILE_MISSING; exit 1; }
test "$(sha256sum "$SOURCE" | awk '{print $1}')" = "$EXPECTED" || { echo SOURCE_SHA_MISMATCH; exit 1; }
DIR="$(mktemp -d /usr/local/fizz-host-test.XXXXXXXX)" || exit 1
trap 'rm -f -- "$DIR/$NAME"; rmdir -- "$DIR" 2>/dev/null || true' EXIT
cp "$SOURCE" "$DIR/$NAME" || exit 1
chmod 755 "$DIR/$NAME" || exit 1
test "$(sha256sum "$DIR/$NAME" | awk '{print $1}')" = "$EXPECTED" || { echo TARGET_SHA_MISMATCH; exit 1; }
sudo -n -u chronos "$DIR/$NAME"
RC=$?
echo "CHROMEOS_EXIT_CODE=$RC"
if [ "$RC" -eq 0 ]; then echo FIZZ_HOST_TEST_PASS; else echo FIZZ_HOST_TEST_FAIL; fi
exit "$RC"
