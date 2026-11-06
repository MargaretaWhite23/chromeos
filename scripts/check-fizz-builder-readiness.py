#!/usr/bin/env python3
"""Read-only readiness assessment for a persistent ChromiumOS Fizz SDK builder."""
import argparse
import json
import os
import pathlib
import platform
import shutil
import subprocess
import sys

def probe(args):
    workdir=pathlib.Path(args.workdir).expanduser().resolve()
    p=argparse.ArgumentParser()
    report={"target":{"board":"fizz","chromeos_release":"150/16700.66.0"},"workdir":str(workdir),"minimum_free_gib":args.min_free_gib,
            "commands":{},"checks":{},"safe_to_start":False,"read_only":True,
            "note":"Capacity gate only; no checkout, SDK bootstrap or sysroot build performed."}
    required=("git","python3","curl","tar","unzip","xz","bash")
    recommended=("sudo","bzip2","zstd","lvm","losetup")
    for cmd in required+recommended:
        report["commands"][cmd]=shutil.which(cmd)
    try:
        stat=os.statvfs(workdir)
        free=stat.f_bavail*stat.f_frsize
        total=stat.f_blocks*stat.f_frsize
        report["storage"]={"free_bytes":free,"total_bytes":total,"free_gib":round(free/(1024**3),2),"total_gib":round(total/(1024**3),2)}
        report["checks"]["disk_free"]=(free >= args.min_free_gib*(1024**3))
    except (OSError,ValueError) as exc:
        report["storage"]={"error":str(exc)}
        report["checks"]["disk_free"]=False
    report["checks"]["required_commands"]=all(report["commands"][cmd] for cmd in required)
    report["checks"]["linux_x86_64"]=(sys.platform.startswith("linux") and platform.machine() in ("x86_64","amd64"))
    report["checks"]["directory_exists"]=workdir.is_dir()
    report["checks"]["not_running_as_root"]=os.geteuid()!=0 if hasattr(os,"geteuid") else False
    report["host"]={"platform":platform.platform(),"architecture":platform.machine(),"python":platform.python_version(),
                    "user_is_root":os.geteuid()==0 if hasattr(os,"geteuid") else None}
    report["safe_to_start"]=all(report["checks"].values())
    return report

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--workdir",default=".")
    p.add_argument("--min-free-gib",type=int,default=100)
    p.add_argument("--output")
    args=p.parse_args()
    if args.min_free_gib<=0: p.error("--min-free-gib must be positive")
    result=probe(args)
    body=json.dumps(result,sort_keys=True,indent=2)+"\n"
    if args.output:
        dest=pathlib.Path(args.output)
        dest.parent.mkdir(parents=True,exist_ok=True)
        dest.write_text(body)
    print(body)
    print("BUILDER_READINESS="+("PASS" if result["safe_to_start"] else "BLOCKED"))
    return 0 if result["safe_to_start"] else 2

if __name__=="__main__":
    sys.exit(main())
