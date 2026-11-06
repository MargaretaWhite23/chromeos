#!/usr/bin/env python3
"""Read-only ChromiumOS manifest dependency audit; no repo sync or build."""
import os, subprocess, pathlib, xml.etree.ElementTree as ET, json, sys
base=pathlib.Path("public-manifest")
out=pathlib.Path("reports");out.mkdir(exist_ok=True)
report={"target":"fizz","release":"16700.66.0","branch":"release-R150-16700.B","manifest_files":[],"projects":0,"private_like":[],"unresolved":[],"status":"UNVERIFIED"}
if not base.is_dir():
    print("::error::public-manifest checkout missing");sys.exit(1)
files=list(base.glob("*.xml"))
if not files:
    print("::error::No manifest XML files found");sys.exit(1)
for file in files:
    try: root=ET.parse(file).getroot()
    except ET.ParseError as e:
        report["unresolved"].append(f"{file}: XML parse error {e}");continue
    report["manifest_files"].append(str(file))
    for p in root.findall("project"):
        report["projects"]+=1
        name=p.get("name","")
        if "private" in name.lower() or "internal" in name.lower():
            report["private_like"].append(name)
    for inc in root.findall("include"):
        target=base/inc.get("name","")
        if not target.is_file():
            report["unresolved"].append(f"{file}: include {inc.get('name')} absent")
    for sub in root.findall("submanifest"):
        report["unresolved"].append(f"{file}: submanifest {sub.get('name')} requires recursive resolution")
report["status"]="SOURCE_METADATA_ONLY"
(out/"manifest-audit.json").write_text(json.dumps(report,indent=2)+"\n")
print(json.dumps(report,indent=2))
if report["unresolved"]:
    print("::error::Manifest dependencies not fully resolved; cannot claim reproducible public checkout")
    sys.exit(1)
print("::warning::Manifest syntax checks passed; public accessibility of every project, private package availability, exact official buildspec and ABI remain UNVERIFIED.")
