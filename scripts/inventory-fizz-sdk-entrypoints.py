#!/usr/bin/env python3
"""Inventory SDK entrypoints and board build prerequisites from pinned source tree."""
import json
import pathlib
import xml.etree.ElementTree as ET

root=pathlib.Path("checkout")
out=pathlib.Path("reports")
manifest=ET.parse(out/"buildspec.xml").getroot()
projects=manifest.findall("project")
keywords=("chromite","crosutils","portage","overlays","toolchain","build","sdk","platform2")
likely=[{"name":p.get("name"),"path":p.get("path"),"revision":p.get("revision")} for p in projects if any(k in (p.get("name") or "").lower() for k in keywords)]
targets=("cros_sdk","setup_board","build_packages","build_image","cros")
found=[]
# Inspect only selected source directories, avoiding deep recursive walk across huge trees.
for part in ("infra/chromite-HEAD","infra/chromite","src/scripts","src/overlays"):
 base=root/part
 if not base.is_dir(): continue
 for target in targets:
  matches=[]
  for p in base.rglob(target):
   if p.is_file() and len(p.relative_to(base).parts)<=8:
    matches.append(str(p.relative_to(root)))
   if len(matches)>=12:break
  if matches:found.append({"source_dir":part,"command":target,"paths":matches})
board=root/"src/overlays/overlay-fizz"
board_listing=sorted(str(x.relative_to(root)) for x in board.iterdir())[:80] if board.is_dir() else []
report={"release":"16700.66.0","board":"fizz","project_count":len(projects),"likely_build_projects":likely,"entrypoints":found,"board_overlay_entries":board_listing,"not_performed":["SDK initialization","setup_board","sysroot build","binary compilation","device execution"]}
(out/"sdk-entrypoints.json").write_text(json.dumps(report,indent=2)+"\n")
print(json.dumps({"release":report["release"],"board":report["board"],"project_count":len(projects),"likely_project_count":len(likely),"entrypoints":found,"board_overlay_entries":board_listing[:25]},indent=2))
