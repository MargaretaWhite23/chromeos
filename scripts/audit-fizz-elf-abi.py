#!/usr/bin/env python3
"""Read-only ELF ABI audit. Do not execute target binaries."""
import argparse
import json
from pathlib import Path
import re
import subprocess

VERSION_RE = re.compile(r"\bGLIBC_(\d+)\.(\d+)(?:\.(\d+))?\b")
NEEDED_RE = re.compile(r"\(NEEDED\).*Shared library: \[([^\]]+)\]")
INTERP_RE = re.compile(r"Requesting program interpreter:\s*([^\]]+)")

def run(*args):
    return subprocess.run(args, check=True, text=True, capture_output=True).stdout

def version_tuple(v):
    parts = [int(x) for x in v.split(".")]
    return tuple((parts + [0, 0, 0])[:3])

def inspect(binary):
    head = run("readelf", "-h", binary)
    program = run("readelf", "-l", binary)
    dynamic = run("readelf", "-d", binary)
    version_info = run("readelf", "--version-info", binary)
    requested = sorted(set(m.group(0)[6:] for m in VERSION_RE.finditer(version_info)), key=version_tuple)
    machine = re.search(r"Machine:\s*(.+)", head)
    loader = INTERP_RE.search(program)
    return {
        "machine": machine.group(1).strip() if machine else None,
        "interpreter": loader.group(1).strip() if loader else None,
        "needed_libraries": sorted(set(NEEDED_RE.findall(dynamic))),
        "glibc_versions": requested,
        "maximum_glibc_version": requested[-1] if requested else None
    }

def compare(abi, profile):
    checks = {
        "x86_64": abi["machine"] == "Advanced Micro Devices X86-64",
        "interpreter_present": abi["interpreter"] in profile.get("available_interpreters", []),
        "libraries_present": set(abi["needed_libraries"]).issubset(profile.get("libraries", [])),
        "glibc_version_supported": bool(abi["maximum_glibc_version"] and profile.get("glibc_version") and
            version_tuple(abi["maximum_glibc_version"]) <= version_tuple(profile["glibc_version"]))
    }
    return {"checks": checks, "reported_fields_compatible": all(checks.values()),
            "note": "Passing these checks does not establish full ChromeOS runtime compatibility."}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--binary", required=True)
    parser.add_argument("--profile")
    parser.add_argument("--output", default="reports/fizz-elf-abi-audit.json")
    a = parser.parse_args()
    abi = inspect(a.binary)
    result = {"target": "Fizz 16700.66.0", "host_binary_abi": abi,
              "target_profile_provided": bool(a.profile)}
    if a.profile:
        result["comparison"] = compare(abi, json.loads(Path(a.profile).read_text()))
    else:
        result["comparison"] = {"status": "UNVERIFIED_NO_TARGET_PROFILE"}
    out = Path(a.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2) + "\n")
    print("HOST_GLIBC_MAX=" + str(abi["maximum_glibc_version"]))
    print("HOST_ELF_INTERPRETER=" + str(abi["interpreter"]))
    print("HOST_NEEDED=" + ",".join(abi["needed_libraries"]))
    print("TARGET_ABI_UNVERIFIED_NO_PROFILE" if not a.profile else
          "TARGET_REPORTED_FIELDS_COMPATIBLE=" + str(result["comparison"]["reported_fields_compatible"]).lower())
    print("FIZZ_ELF_AUDIT_COMPLETE")

if __name__ == "__main__":
    main()
