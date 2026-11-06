#!/usr/bin/env python3
"""Bounded public Gitiles accessibility audit of exact pinned buildspec."""
import concurrent.futures, json, pathlib, urllib.request, urllib.error, xml.etree.ElementTree as ET, sys, time
OUT=pathlib.Path("reports");OUT.mkdir(exist_ok=True)
url="https://storage.googleapis.com/chromiumos-manifest-versions/buildspecs/150/16700.66.0.xml"
try:
    with urllib.request.urlopen(url,timeout=35) as r: xml=r.read()
    root=ET.fromstring(xml)
except Exception as e:
    print(f"::error::Unable to fetch or parse exact public buildspec: {e}");sys.exit(1)
(OUT/"exact-buildspec.xml").write_bytes(xml)
remotes={x.get("name"):x.get("fetch") for x in root.findall("remote")}
default=root.find("default")
default_remote=default.get("remote") if default is not None else None
projects=root.findall("project")
names=("chromiumos/overlays/board-overlays","chromiumos/manifest","chromiumos/platform2","chromiumos/third_party/kernel","chromiumos/third_party/portage-stable","chromiumos/third_party/chromiumos-overlay","chromiumos/chromite","chromiumos/platform/crosutils")
chosen=[]
for name in names:
    matches=[p for p in projects if p.get("name")==name]
    if matches: chosen.append(matches[0])
# Include additional deterministic samples, up to 16.
for p in projects:
    if len(chosen)>=16:break
    if p not in chosen:chosen.append(p)
def test(p):
    name=p.get("name","")
    rev=p.get("revision","")
    remote=p.get("remote") or default_remote
    fetch=remotes.get(remote,"")
    result={"name":name,"revision":rev,"remote":remote,"fetch":fetch,"status":"unknown"}
    if not rev or len(rev)!=40 or any(c not in "0123456789abcdefABCDEF" for c in rev):
        result["status"]="invalid-revision";return result
    if not fetch.startswith("https://"):
        result["status"]="unsupported-remote";return result
    repo_url=fetch.rstrip("/")+"/"+name
    check=repo_url+"/+/"+rev+"?format=JSON"
    try:
        req=urllib.request.Request(check,headers={"User-Agent":"fizz-public-buildspec-probe/1.0"})
        with urllib.request.urlopen(req,timeout=25) as response:
            body=response.read(2048)
        result["status"]="accessible" if b'"commit"' in body or b'"tree"' in body else "unexpected-response"
    except Exception as e:
        result["status"]="unavailable";result["error"]=str(e)[:240]
    return result
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
    results=list(pool.map(test,chosen))
summary={"version":"16700.66.0","total_manifest_projects":len(projects),"sample_size":len(results),"accessible":sum(x["status"]=="accessible" for x in results),"results":results,"scope":"Pinned commit accessibility sample; not full repo sync, SDK bootstrap, or Fizz compatibility"}
(OUT/"pinned-project-audit.json").write_text(json.dumps(summary,indent=2)+"\n")
print(json.dumps(summary,indent=2))
if not results or any(x["status"]!="accessible" for x in results):
    print("::error::One or more sampled pinned public projects are inaccessible or unsupported")
    sys.exit(1)
print("PASS: Sampled pinned commits publicly accessible. Full source checkout and Fizz sysroot remain UNVERIFIED.")
