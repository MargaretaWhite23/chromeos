#!/usr/bin/env python3
"""Audit every project in the public ChromeOS 16700.66.0 pinned buildspec."""
import concurrent.futures, json, pathlib, urllib.request, urllib.error, xml.etree.ElementTree as ET, sys, os, time, collections
out=pathlib.Path("reports");out.mkdir(exist_ok=True)
url="https://storage.googleapis.com/chromiumos-manifest-versions/buildspecs/150/16700.66.0.xml"
with urllib.request.urlopen(url,timeout=45) as r: data=r.read()
root=ET.fromstring(data)
(out/"buildspec.xml").write_bytes(data)
remotes={r.get("name"):r.get("fetch") for r in root.findall("remote")}
default=root.find("default"); default_remote=default.get("remote") if default is not None else None
projects=root.findall("project")
def audit(index,p):
    name=p.get("name","");rev=p.get("revision","");remote=p.get("remote") or default_remote;fetch=remotes.get(remote,"")
    item={"index":index,"name":name,"revision":rev,"remote":remote,"fetch":fetch,"status":"unknown"}
    if len(rev)!=40 or any(c not in "0123456789abcdefABCDEF" for c in rev):item["status"]="invalid-revision";return item
    if not fetch.startswith("https://"):item["status"]="unsupported-remote";return item
    target=fetch.rstrip("/")+"/"+name+"/+/"+rev+"?format=JSON"
    for attempt in range(3):
        try:
            req=urllib.request.Request(target,headers={"User-Agent":"ChromeOS-Fizz-pinned-source-audit/1.0"})
            with urllib.request.urlopen(req,timeout=22) as response: body=response.read(4096)
            item["status"]="accessible" if b'"commit"' in body and b'"tree"' in body else "unexpected-response"
            return item
        except urllib.error.HTTPError as e:
            item["status"]="http-error";item["error"]=str(e)
            if e.code not in (429,500,502,503,504):return item
        except Exception as e:item["status"]="network-error";item["error"]=str(e)[:250]
        time.sleep(attempt+1)
    return item
with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
    results=list(pool.map(lambda ip:audit(*ip),enumerate(projects)))
counts=dict(collections.Counter(x["status"] for x in results))
summary={"version":"16700.66.0","total":len(projects),"counts":counts,"complete_public_accessibility":len(projects)>0 and counts.get("accessible",0)==len(projects),"note":"Gitiles commit metadata checks only; does not establish full repo sync, SDK setup or Fizz binary compatibility"}
(out/"audit-summary.json").write_text(json.dumps(summary,indent=2)+"\n")
(out/"audit-all-projects.json").write_text(json.dumps(results,indent=2)+"\n")
print(json.dumps(summary,indent=2))
for r in results:
    if r["status"]!="accessible":print("NOT_ACCESSIBLE",json.dumps(r))
if not summary["complete_public_accessibility"]:
    print("::error::Not all pinned projects are publicly accessible by this method; review reports/audit-all-projects.json")
    sys.exit(1)
print("PASS: All pinned project commits accessible through public Gitiles; full repo sync and sysroot build remain UNVERIFIED.")
