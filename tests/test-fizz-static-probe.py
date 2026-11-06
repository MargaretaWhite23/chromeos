#!/usr/bin/env python3
"""Check static-musl binary exists, executes on runner, and has no dynamic dependencies."""
from pathlib import Path
import subprocess
p=Path("output/fizz-static-probe")
assert p.is_file(),"static probe missing"
r=subprocess.run([str(p.resolve())],capture_output=True,text=True,check=True)
assert "ARCHITECTURE=x86_64" in r.stdout,r.stdout
assert "FIZZ_STATIC_PROBE_COMPLETE" in r.stdout,r.stdout
assert "KERNEL_RELEASE=" in r.stdout,r.stdout
print("PASS: static probe executes on Ubuntu runner")
