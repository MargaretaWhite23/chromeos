#!/usr/bin/env python3
"""Test the readiness gate, including blocked states, without requiring large disks."""
import json
import os
import pathlib
import tempfile
from unittest.mock import patch
from types import SimpleNamespace
import importlib.util

f=pathlib.Path("scripts/check-fizz-builder-readiness.py")
spec=importlib.util.spec_from_file_location("readiness",str(f))
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

with tempfile.TemporaryDirectory() as d:
    args=SimpleNamespace(workdir=d,min_free_gib=100)
    checks=mod.probe(args)
    assert checks["read_only"] is True
    assert checks["safe_to_start"] is False,checks
    assert "disk_free" in checks["checks"]
    print("PASS: modest disk is rejected")
    with patch.object(mod.os,"statvfs") as stat:
        stat.return_value=SimpleNamespace(f_bavail=200*1024**3,f_frsize=1,
                                           f_blocks=256*1024**3)
        with patch.object(mod.os,"geteuid",return_value=1000):
            big=mod.probe(args)
            assert big["checks"]["disk_free"] is True,big
            if big["checks"]["required_commands"] and big["checks"]["linux_x86_64"]:
                assert big["safe_to_start"] is True,big
            else:
                assert big["safe_to_start"] is False,big
            print("PASS: sufficient storage is accepted when host prerequisites are met")
        with patch.object(mod.os,"geteuid",return_value=0):
            root=mod.probe(args)
            assert root["safe_to_start"] is False,root
            print("PASS: root execution is blocked")
    args=SimpleNamespace(workdir="/this/path/must/not/exist/fizz",min_free_gib=100)
    missing=mod.probe(args)
    assert missing["safe_to_start"] is False,missing
    print("PASS: nonexistent workdir is rejected")
print("FIZZ_READINESS_GATE_TESTS_COMPLETE")
