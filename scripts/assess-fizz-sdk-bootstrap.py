#!/usr/bin/env python3
"""Inspect exact 16700.66.0 pinned source manifest for SDK bootstrap feasibility."""
import json
import pathlib
import re
import subprocess
import xml.etree.ElementTree as ET

ROOT=pathlib.Path.cwd()
OUT=ROOT/"reports"
OUT.mkdir(exist_ok=True)
tree=ET.parse(OUT/"buildspec.xml").getroot()
projects=tree.findall("project")
names={p.get("name"):p for p in projects}
paths={p.get("path") or p.get("name"):p.get("name") for p in projects}
ch=root=ROOT/"checkout"/"infra"/"chromite-HEAD"
tools={}
for name in ("cros_sdk","setup_board","cros","build_packages"):
    p=ch/"bin"/name
    tools[name]={"exists":p.is_file(),"path":str(p.relative_to(ROOT)) if p.is_file() else None}
sdk_file=ch/"bin"/"cros_sdk"
sdk_excerpt=[]
if sdk_file.is_file():
    for i,line in enumerate(sdk_file.read_text(errors="replace").splitlines(),1):
        if re.search(r"(bootstrap|chroot|enter|sdk|download|cache|build)",line,re.I):
            sdk_excerpt.append({"line":i,"text":line[:200]})
        if len(sdk_excerpt)>=30:
            break
classification={}
for p in projects:
    name=p.get("name") or ""
    path=p.get("path") or ""
    for needle in ("chromite","crosutils","overlays","portage","toolchain","sdk","build","manifest"):
        if needle in name.lower() or needle in path.lower():
            classification.setdefault(needle,[]).append({"name":name,"path":path,"revision":p.get("revision")})
def run(command):
    r=subprocess.run(command,capture_output=True,text=True)
    return {"exit_code":r.returncode,"stdout":r.stdout[-3000:].strip(),"stderr":r.stderr[-1500:].strip()}
capacity=run(["df","-Pk",str(ROOT)])
report={
"board":"fizz",
"version":"16700.66.0",
"manifest_project_count":len(projects),
"selected_project_groups":classification,
"sdk_tools":tools,
"sdk_script_sample":sdk_excerpt,
"runner_disk":capacity,
"planned_full_repo_sync":False,
"planned_sdk_bootstrap":False,
"sysroot_built":False,
"limitations":[
"Only selected pinned source repositories were synchronized in this diagnostic.",
"The 13 GiB free GitHub-hosted runner is not approved for a full SDK bootstrap.",
"Public manifest availability does not demonstrate exact proprietary Google ChromeOS source equivalence.",
"Disk capacity needed for a full checkout + SDK is not estimated from git metadata; this diagnostic is a classification and capacity gate."
]
}
(OUT/"fizz-sdk-bootstrap-feasibility.json").write_text(json.dumps(report,indent=2)+"\n")
print("FIZZ_PROJECT_COUNT="+str(len(projects)))
print("SDK_TOOL_LOCATIONS="+json.dumps(tools))
print("SDK_SOURCE_GROUP_COUNTS="+json.dumps({k:len(v) for k,v in classification.items()}))
print("FIZZ_SDK_BOOTSTRAP_NOT_ATTEMPTED")
