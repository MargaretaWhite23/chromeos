#!/usr/bin/env python3
"""Report pinned source prerequisites, not an SDK/sysroot build."""
import argparse
import json
import pathlib
import subprocess
import xml.etree.ElementTree as ET

parser = argparse.ArgumentParser()
parser.add_argument("--manifest", type=pathlib.Path, required=True)
parser.add_argument("--checkout", type=pathlib.Path, required=True)
parser.add_argument("--output", type=pathlib.Path, required=True)
args = parser.parse_args()

root = ET.parse(args.manifest).getroot()
projects = root.findall("project")
by_name = {p.get("name"): p for p in projects}
selected = [
    "chromiumos/manifest",
    "chromiumos/chromite",
    "chromiumos/overlays/board-overlays",
    "chromiumos/platform/crosutils",
]
entries = []
for name in selected:
    project = by_name.get(name)
    if project is None:
        entries.append({"name": name, "in_manifest": False})
        continue
    location = args.checkout / (project.get("path") or name)
    actual = None
    if (location / ".git").exists() or (location / ".git").is_file():
        result = subprocess.run(
            ["git", "-C", str(location), "rev-parse", "HEAD"],
            capture_output=True, text=True, check=True
        )
        actual = result.stdout.strip()
    entries.append({
        "name": name,
        "in_manifest": True,
        "manifest_path": project.get("path") or name,
        "expected_revision": project.get("revision"),
        "checked_out_revision": actual,
        "matches_pinned_revision": bool(actual and actual == project.get("revision")),
    })
board_entry = next((e for e in entries if e["name"].endswith("/board-overlays")), {})
board_path = args.checkout / board_entry.get("manifest_path", "src/overlays/board-overlays")
paths = [
    board_path / "overlay-fizz",
    board_path / "baseboard-fizz",
    board_path / "overlay-fizz" / "toolchain.conf",
    board_path / "overlay-fizz" / "make.conf",
]
board_files = {str(path.relative_to(args.checkout)): path.exists() for path in paths}
crosutils_entry = next((e for e in entries if e["name"].endswith("/crosutils")), {})
scripts_path = args.checkout / crosutils_entry.get("manifest_path", "src/scripts")
tools = {}
if scripts_path.is_dir():
    for tool in ("setup_board", "cros_sdk", "build_packages"):
        tools[tool] = any(p.name == tool for p in scripts_path.rglob(tool))
report = {
    "target": {"board": "fizz", "public_buildspec": "16700.66.0", "arch": "x86_64"},
    "manifest_projects": len(projects),
    "projects": entries,
    "board_files": board_files,
    "crosutils_tools": tools,
    "sdk_initialized": False,
    "setup_board_executed": False,
    "sysroot_built": False,
    "binary_compiled": False,
    "device_tested": False,
    "note": "Exact PUBLIC buildspec source preflight only; neither official Google ChromeOS equivalence nor ABI compatibility is established.",
    "next_steps": [
        "Choose a persistent builder with enough disk for a complete pinned checkout/SDK.",
        "Initialize the SDK using official ChromiumOS tools.",
        "Run setup_board --board=fizz inside the SDK.",
        "Verify compiler, headers, startup objects and linker against built board sysroot.",
        "Compile and test the binary on the actual Fizz ChromeOS 150 device."
    ],
}
args.output.parent.mkdir(parents=True, exist_ok=True)
args.output.write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps(report, indent=2))
if any(e.get("checked_out_revision") and not e.get("matches_pinned_revision") for e in entries):
    raise SystemExit("ERROR: checked-out project does not match its manifest-pinned revision")
