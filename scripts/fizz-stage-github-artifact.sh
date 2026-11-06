#!/usr/bin/env bash
set -Eeuo pipefail
REPO=MargaretaWhite23/chromeos
RUN="$1"
NAME="$2"
case "$RUN" in *[!0-9]*|"") exit 2;; esac
case "$NAME" in fizz-runtime-capabilities|fizz-static-probe) ;; *) exit 2;; esac
CHECKSUM=reports/static-sha256.txt
if [ "$NAME" = fizz-runtime-capabilities ]; then CHECKSUM=reports/runtime-capabilities-sha256.txt; fi
echo "=== GITHUB ACTIONS STATUS ==="
gh run view "$RUN" -R "$REPO" --json status,conclusion,url --jq '{status,conclusion,url}'
STATUS="$(gh run view "$RUN" -R "$REPO" --json status --jq .status)"
if [ "$STATUS" != completed ]; then echo BUILD_STILL_RUNNING; exit 0; fi
test "$(gh run view "$RUN" -R "$REPO" --json conclusion --jq .conclusion)" = success || { echo BUILD_FAILED; exit 1; }
BASE="$HOME/fizz-github-artifacts"
DIR="$BASE/run-$RUN"
if [ ! -f "$DIR/$CHECKSUM" ]; then
  mkdir -p "$BASE"
  TMP="$(mktemp -d "$BASE/.download.XXXXXXXX")"
  trap 'rm -rf -- "$TMP"' EXIT
  gh run download "$RUN" -R "$REPO" --name fizz-minimal-no-sdk-host-abi --dir "$TMP"
  (cd "$TMP" && sha256sum -c "$CHECKSUM")
  if [ -e "$DIR" ]; then echo INCOMPLETE_DOWNLOAD_DIR; exit 1; fi
  mv "$TMP" "$DIR"
  trap - EXIT
fi
(cd "$DIR" && sha256sum -c "$CHECKSUM")
DEST="/mnt/chromeos/MyFiles/Downloads/fizz-$RUN-$NAME"
install -m 755 "$DIR/output/$NAME" "$DEST"
A="$(sha256sum "$DIR/output/$NAME" | awk '{print $1}')"
B="$(sha256sum "$DEST" | awk '{print $1}')"
test "$A" = "$B"
echo "STAGED_FILE=$DEST"
echo "SHA256=$A"
echo FIZZ_ARTIFACT_STAGED
