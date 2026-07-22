#!/usr/bin/env python3
# desc: extracts the raw declared <uses-permission> list from AndroidManifest.xml (mechanical only, no domain/LGPD mapping)
"""extract_permissions.py — declared-permissions extraction for apk-archaeology.

Parses `<apktool_dir>/AndroidManifest.xml` for every `<uses-permission
android:name="..." [android:maxSdkVersion="..."]/>` element and emits the
raw declared list: permission name + its maxSdkVersion, if any.

This is deliberately the MECHANICAL half only. Mapping a declared permission
to a bridge capability, a native partition, or an LGPD-sensitivity tag is a
judgment call against a capability catalog built for one specific app — it
does not generalize, and it belongs in prose (a human/agent synthesis step
downstream), not in this extractor. Same split as extract_persistence.py:
this script extracts a raw fact; a later synthesis step adds interpretive
columns over it, never the other way around.

Documented limitations:
  - Line-anchored regex over the manifest text, not a real XML parser —
    consistent with this script family's style (see extract_harvest.py's
    network_security_config extraction). A `<uses-permission>` element that
    isn't self-closing (no real manifest emits `<uses-permission ...>
    </uses-permission>`, but apktool output isn't validated) is silently
    skipped, not mis-parsed — a false negative, not a corruption.
  - The element is matched as a whole first (`<uses-permission\b[^>]*/>` —
    `[^>]` spans newlines too, no `re.DOTALL` needed), then
    `android:name`/`android:maxSdkVersion` are extracted independently from
    within that matched tag text. This is robust to attribute order and to
    any OTHER attribute present on the same element — including a
    manifest-merger directive like `tools:node="remove"`, a common
    real-world override seen on exactly this element — none of which
    prevent extraction anymore.
  - Duplicate `android:name` declarations (should not occur in a valid
    manifest, but apktool output isn't validated) are de-duplicated,
    keeping the FIRST occurrence's maxSdkVersion — a deliberate, simple
    tie-break, not a merge.
  - An element with no `android:name` attribute at all (malformed) is
    skipped rather than raising — consistent with "false negative, not
    corruption" above.

Verified against a real corpus (a production APK's manifest, outside this
repo): every declared permission on it was extracted correctly. That
manifest carries no extra-attribute `<uses-permission>` entries, so it
didn't exercise the extra-attribute case above — the selftest fixture is
the only positive-path coverage for that (see selftest_extract_permissions.py).

Pure stdlib. Deterministic: same AndroidManifest.xml = same output.

Usage:
  python3 extract_permissions.py <apktool_dir> --out <path>
  Default --out is data/permissions.json.
"""
import argparse
import json
import os
import re

TAG_RE = re.compile(r"<uses-permission\b[^>]*/>")
NAME_RE = re.compile(r'android:name="([^"]+)"')
MAXSDK_RE = re.compile(r'android:maxSdkVersion="(\d+)"')


def extract_permissions(apktool_dir):
    manifest_path = os.path.join(apktool_dir, "AndroidManifest.xml")
    if not os.path.isfile(manifest_path):
        raise SystemExit(
            f"extract_permissions: AndroidManifest.xml not found at {manifest_path}"
        )

    with open(manifest_path, encoding="utf-8", errors="replace") as f:
        content = f.read()

    seen = set()
    permissions = []
    for m in TAG_RE.finditer(content):
        tag = m.group(0)
        name_m = NAME_RE.search(tag)
        if not name_m:
            continue
        name = name_m.group(1)
        if name in seen:
            continue
        seen.add(name)
        maxsdk_m = MAXSDK_RE.search(tag)
        maxsdk = maxsdk_m.group(1) if maxsdk_m else None
        permissions.append(
            {"name": name, "max_sdk_version": int(maxsdk) if maxsdk else None}
        )

    permissions.sort(key=lambda p: p["name"])
    return {
        "summary": {"total_permissions": len(permissions)},
        "permissions": permissions,
    }


def main():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("apktool_dir")
    parser.add_argument("--out", default="data/permissions.json")
    args = parser.parse_args()

    result = extract_permissions(args.apktool_dir)
    output = json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False)

    if args.out:
        out_dir = os.path.dirname(args.out)
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(output + "\n")
    else:
        print(output)


if __name__ == "__main__":
    main()
