#!/usr/bin/env bash
set -Eeuo pipefail
mkdir -p reports
exec > >(tee reports/buildspec-discovery.log) 2>&1
version="16700.66.0"
path="buildspecs/150/${version}.xml"
url="https://storage.googleapis.com/chromiumos-manifest-versions/${path}"
echo "Looking for exact public ChromiumOS buildspec: ${path}"
echo "Source: ${url}"
echo "NOTE: availability of public buildspec does not establish private Fizz overlay equivalence."
if ! curl --fail --location --retry 2 --connect-timeout 15 --max-time 120 --silent --show-error \
    --output reports/buildspec.xml "$url"; then
  echo "::error::Exact public buildspec ${path} is unavailable through unauthenticated HTTPS. It may not be published, may use another location, or may require permissions."
  echo "BUILDSPEC_AVAILABLE=no" | tee reports/result.txt
  exit 1
fi
python3 - <<'PY'
from pathlib import Path
import xml.etree.ElementTree as ET
p=Path("reports/buildspec.xml")
try:
    root=ET.parse(p).getroot()
except ET.ParseError as e:
    raise SystemExit(f"::error::Downloaded buildspec is not valid XML: {e}")
if root.tag!="manifest":
    raise SystemExit(f"::error::Unexpected root element {root.tag!r}")
projects=root.findall("project")
if not projects:
    raise SystemExit("::error::Manifest has no project elements; not a usable pinned buildspec")
unfixed=[p.get("name","?") for p in projects if not p.get("revision")]
print(f"Public buildspec parsed: {len(projects)} projects, {len(unfixed)} without explicit project revision")
if unfixed:
    print("::warning::Some projects lack an explicit revision; investigate manifest defaults and includes before declaring fully pinned")
Path("reports/summary.txt").write_text(f"project_count={len(projects)}\nmissing_explicit_revision={len(unfixed)}\n")
PY
sha256sum reports/buildspec.xml | tee reports/buildspec.sha256
echo "BUILDSPEC_AVAILABLE=yes" | tee reports/result.txt
echo "PUBLIC_BUILDSPEC_FOUND; FIZZ_OFFICIAL_EQUIVALENCE_UNVERIFIED"
