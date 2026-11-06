#!/usr/bin/env python3
import subprocess
from pathlib import Path
p=Path("output/fizz-runtime-capabilities")
assert p.is_file()
r=subprocess.run([str(p.resolve())],check=True,capture_output=True,text=True)
assert "FIZZ_RUNTIME_CAPABILITIES_COMPLETE" in r.stdout
assert "RUNTIME_ARCH=x86_64" in r.stdout
assert "RUNTIME_EUID=" in r.stdout
assert "RUNTIME_KERNEL=" in r.stdout
print("PASS: static runtime capabilities probe on CI runner")
