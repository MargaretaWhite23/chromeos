#!/usr/bin/env python3
"""ABI audit parser tests, no ChromeOS hardware required."""
import importlib.util
spec = importlib.util.spec_from_file_location("audit", "scripts/audit-fizz-elf-abi.py")
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)
assert audit.version_tuple("2.2.5") < audit.version_tuple("2.34")
abi = {"machine":"Advanced Micro Devices X86-64",
       "interpreter":"/lib64/ld-linux-x86-64.so.2",
       "needed_libraries":["libc.so.6"],"maximum_glibc_version":"2.34"}
target = {"available_interpreters":["/lib64/ld-linux-x86-64.so.2"],
          "libraries":["libc.so.6"],"glibc_version":"2.35"}
assert audit.compare(abi,target)["reported_fields_compatible"]
target["glibc_version"] = "2.31"
assert not audit.compare(abi,target)["reported_fields_compatible"]
target["glibc_version"] = "2.35"
target["available_interpreters"] = []
assert not audit.compare(abi,target)["reported_fields_compatible"]
print("PASS: ABI version and loader/library compatibility gate")
