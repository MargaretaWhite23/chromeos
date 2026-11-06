#!/usr/bin/env python3
"""Bounded, unauthenticated discovery of public ChromiumOS artifacts.

No full source checkout, no SDK installation, and no target compatibility claim.
"""
import json
import os
from pathlib import Path
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

OUT=Path("reports")
OUT.mkdir(exist_ok=True)
BUCKETS=("chromiumos-sdk","chromiumos-image-archive","chromeos-dev-installer","chromeos-prebuilt")
LIMIT=25
MAX_BYTES=1024*1024
TIMEOUT=12
def list_bucket(bucket,prefix):
    qs=urllib.parse.urlencode({"prefix":prefix,"max-keys":str(LIMIT)})
    url="https://storage.googleapis.com/"+bucket+"?"+qs
    req=urllib.request.Request(url,headers={"User-Agent":"fizz-minimal-build-artifact-inventory/1.0"})
    result={"bucket":bucket,"prefix":prefix,"url":url,"objects":[],"accessible":False}
    try:
        with urllib.request.urlopen(req,timeout=TIMEOUT) as response:
            payload=response.read(MAX_BYTES+1)
            if len(payload)>MAX_BYTES:
                raise ValueError("response exceeds bounded inventory limit")
            root=ET.fromstring(payload)
            result["accessible"]=True
            result["truncated"]=root.findtext("{*}IsTruncated")=="true"
            for item in root.findall("{*}Contents"):
                key=item.findtext("{*}Key") or ""
                size=int(item.findtext("{*}Size") or "0")
                result["objects"].append({"key":key,"bytes":size,
                    "url":"https://storage.googleapis.com/"+bucket+"/"+urllib.parse.quote(key,safe="/")})
    except (urllib.error.URLError,TimeoutError,ValueError,ET.ParseError) as exc:
        result["error"]=str(exc)
    return result

def main():
    # Prefixes are targeted to avoid massive public bucket listings. A missing object
    # cannot prove an artifact does not exist under another prefix.
    searches=[
      ("chromiumos-sdk","cros-sdk-"),
      ("chromiumos-image-archive","fizz-"),
      ("chromiumos-image-archive","fizz-release/"),
      ("chromeos-dev-installer","fizz/"),
      ("chromeos-prebuilt","fizz/"),
    ]
    output={"target":{"board":"fizz","release":"16700.66.0","milestone":"150"},
      "inventory":[list_bucket(*s) for s in searches],
      "limitations":[
        "Only bounded, public, unauthenticated bucket-prefix listings attempted.",
        "No artifact is presumed release-compatible from its name alone.",
        "Private ChromeOS release artifacts are neither requested nor required.",
        "A source-based ChromiumOS SDK and complete repo checkout were not initialized.",
        "Exact target ABI cannot be established without inspecting the installed target and matching development inputs."
      ]}
    (OUT/"public-artifact-inventory.json").write_text(json.dumps(output,indent=2)+"\n")
    for entry in output["inventory"]:
        print("ARTIFACT_PREFIX="+entry["bucket"]+"/"+entry["prefix"]+
            " accessible="+str(entry["accessible"])+" count="+str(len(entry["objects"]))+
            (" error="+entry["error"][:160] if "error" in entry else ""))
    print("PUBLIC_ARTIFACT_INVENTORY_COMPLETE")
if __name__=="__main__":
    main()
