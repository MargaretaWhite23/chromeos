#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BIN="$HOME/.local/share/fizz-automation"
USER_UNITS="$HOME/.config/systemd/user"
mkdir -p "$BIN" "$USER_UNITS"
install -m 755 "$ROOT/scripts/fizz-crostini-monitor.py" "$BIN/fizz-crostini-monitor.py"
install -m 755 "$ROOT/scripts/fizz-stage-github-artifact.sh" "$BIN/fizz-stage-github-artifact.sh"
install -m 644 "$ROOT/systemd/fizz-crostini-monitor.service" "$USER_UNITS/fizz-crostini-monitor.service"
install -m 644 "$ROOT/systemd/fizz-crostini-monitor.timer" "$USER_UNITS/fizz-crostini-monitor.timer"
python3 -m py_compile "$BIN/fizz-crostini-monitor.py"
systemctl --user daemon-reload
systemctl --user enable --now fizz-crostini-monitor.timer
echo "FIZZ_CROSTINI_TIMER_INSTALLED"
systemctl --user status --no-pager fizz-crostini-monitor.timer || true
