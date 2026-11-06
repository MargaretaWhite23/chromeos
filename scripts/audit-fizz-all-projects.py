#!/usr/bin/env python3
"""Audit all pinned commits in the public ChromeOS 16700.66.0 buildspec.

Performs read-only Gitiles metadata checks. Rate limits are transient and are
reported separately from genuinely inaccessible or missing commit revisions.
"""
import collections
import concurrent.futures
import email.utils
import json
import pathlib
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

OUT = pathlib.Path("reports")
OUT.mkdir(exist_ok=True)
URL = "https://storage.googleapis.com/chromiumos-manifest-versions/buildspecs/150/16700.66.0.xml"
MAX_WORKERS = 2
MAX_ATTEMPTS = 7
TRANSIENT_CODES = {408, 429, 500, 502, 503, 504}

try:
    with urllib.request.urlopen(URL, timeout=45) as response:
        buildspec = response.read()
    manifest = ET.fromstring(buildspec)
except (OSError, ET.ParseError) as error:
    print(f"::error::Cannot retrieve the exact public buildspec: {error}")
    raise SystemExit(1)

(OUT / "buildspec.xml").write_bytes(buildspec)
remotes = {r.get("name"): r.get("fetch") for r in manifest.findall("remote")}
default = manifest.find("default")
default_remote = default.get("remote") if default is not None else None
projects = manifest.findall("project")


def retry_after_seconds(header, default_wait):
    if not header:
        return default_wait
    try:
        return min(180.0, max(default_wait, float(header)))
    except (ValueError, OverflowError):
        pass
    try:
        dt = email.utils.parsedate_to_datetime(header)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        seconds = (dt - datetime.now(timezone.utc)).total_seconds()
        return min(180.0, max(default_wait, seconds))
    except (ValueError, TypeError, OverflowError):
        return default_wait


def audit(index, project):
    name = project.get("name", "")
    revision = project.get("revision", "")
    remote = project.get("remote") or default_remote
    fetch = remotes.get(remote, "")
    item = {
        "index": index,
        "name": name,
        "revision": revision,
        "remote": remote,
        "fetch": fetch,
        "status": "unknown",
        "attempts": 0,
    }
    if len(revision) != 40 or any(c not in "0123456789abcdefABCDEF" for c in revision):
        item["status"] = "invalid-revision"
        return item
    if not fetch.startswith("https://"):
        item["status"] = "unsupported-remote"
        return item

    target = fetch.rstrip("/") + "/" + name + "/+/" + revision + "?format=JSON"
    for attempt in range(1, MAX_ATTEMPTS + 1):
        item["attempts"] = attempt
        # Constrain public Gitiles request rate, including successful checks.
        time.sleep(0.65)
        try:
            request = urllib.request.Request(
                target, headers={"User-Agent": "ChromeOS-Fizz-buildspec-audit/2.0"}
            )
            with urllib.request.urlopen(request, timeout=30) as response:
                content = response.read(4096)
            item["status"] = (
                "accessible"
                if b'"commit"' in content and b'"tree"' in content
                else "unexpected-response"
            )
            item.pop("error", None)
            return item
        except urllib.error.HTTPError as error:
            item["http_status"] = error.code
            item["error"] = str(error)
            if error.code == 429:
                item["status"] = "rate-limited"
            elif error.code in TRANSIENT_CODES:
                item["status"] = "transient-http-error"
            else:
                item["status"] = "http-error"
                return item
            wait = retry_after_seconds(
                error.headers.get("Retry-After"), min(120.0, 10.0 * 2 ** (attempt - 1))
            )
        except (OSError, TimeoutError) as error:
            item["status"] = "network-error"
            item["error"] = str(error)[:250]
            wait = min(120.0, 10.0 * 2 ** (attempt - 1))
        if attempt != MAX_ATTEMPTS:
            print(f"RETRY {name} attempt={attempt} status={item['status']} wait={wait:.0f}s", flush=True)
            time.sleep(wait)
    return item


with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
    results = list(pool.map(lambda entry: audit(*entry), enumerate(projects)))

counts = dict(collections.Counter(item["status"] for item in results))
complete = bool(projects) and counts.get("accessible", 0) == len(projects)
summary = {
    "version": "16700.66.0",
    "total": len(projects),
    "counts": counts,
    "complete_public_accessibility": complete,
    "note": (
        "Read-only Gitiles commit metadata accessibility; does not establish "
        "full repo sync, SDK setup or Fizz binary compatibility"
    ),
}
(OUT / "audit-summary.json").write_text(json.dumps(summary, indent=2) + "\n")
(OUT / "audit-all-projects.json").write_text(json.dumps(results, indent=2) + "\n")
print(json.dumps(summary, indent=2))
for item in results:
    if item["status"] != "accessible":
        print("NOT_VERIFIED", json.dumps(item))

if not complete:
    print(
        "::error::Not all pinned commits could be verified; distinguish rate-limited "
        "and transient results from missing commits in reports/audit-all-projects.json"
    )
    raise SystemExit(1)
print("PASS: All pinned commits publicly accessible through Gitiles; sysroot build remains UNVERIFIED.")
