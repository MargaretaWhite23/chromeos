#!/usr/bin/env python3
"""Assert that a target candidate is static ELF x86-64 and has no PT_INTERP/NEEDED."""
import argparse
import json
from pathlib import Path
import re
import subprocess

def readelf(*args):
    return subprocess.run(("readelf",)+args,check=True,capture_output=True,text=True).stdout

def audit(path):
    hdr=readelf("-h",path)
    prog=readelf("-l",path)
    dyn=readelf("-d",path)
    machine=re.search(r"Machine:\s*(.+)",hdr)
    arch=machine.group(1).strip() if machine else None
    is_static=not re.search(r"\bINTERP\b|Requesting program interpreter:",prog)
    no_needed=not re.search(r"\(NEEDED\)",dyn)
    ok=(arch=="Advanced Micro Devices X86-64" and is_static and no_needed)
    return {"binary":path,"machine":arch,"no_program_interpreter":is_static,
            "no_needed_shared_libraries":no_needed,"static_elf_x86_64":ok,
            "chromeos_fizz_runtime_verified":False}

def main():
    a=argparse.ArgumentParser()
    a.add_argument("--binary",required=True)
    a.add_argument("--output",default="reports/fizz-static-elf-audit.json")
    args=a.parse_args()
    report=audit(args.binary)
    dest=Path(args.output)
    dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(report,indent=2)+"\n")
    for field in ("no_program_interpreter","no_needed_shared_libraries","static_elf_x86_64"):
        print("STATIC_"+field.upper()+"="+str(report[field]).lower())
    print("CHROMEOS_FIZZ_RUNTIME_NOT_TESTED")
    if not report["static_elf_x86_64"]:
        raise SystemExit("Static ELF audit failed")

if __name__=="__main__":
    main()
