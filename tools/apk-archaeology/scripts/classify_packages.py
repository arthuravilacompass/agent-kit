#!/usr/bin/env python3
# desc: classifies packages in a decompiled jadx tree into 3 buckets (spec §5 [2])
"""classify_packages.py — Support dimension of apk-archaeology (design §5 [2]).

Classifies each top-level package (or, for shared namespaces like com/org/br,
the first NON-shared segment) into 3 buckets:
  known-third-party   — matched known-libs.json
  business-candidate  — real, distinctive package name, no known-lib match
  unclassifiable      — 1-2 letter package (R8/ProGuard flatten pattern);
                        could be real business code OR a renamed lib, no way
                        to tell (see spec §6 — a documented fragility, not a bug)

KNOWN LIMITATION (verified against real NewPipe, spec §6): the obfuscation
regex also produces a false positive on a CLEAN app when a real package uses
a short ccTLD-style prefix (e.g. `us.shandian.giga`, a real lib, became
`unclassifiable`). Asymmetric effect: harmless in Dimension B (endpoint
still extracted, just a less precise tag); real loss in Dimension C (class
ends up outside the graph). Not a logic bug — it's the same name-fingerprint
fragility already documented, just in the opposite direction (false positive,
not only false negative).

Pure stdlib. Deterministic: same tree + same known-libs.json = same output.

Usage:
  python3 classify_packages.py <sources_dir> <known_libs_json> [--out <path>]
  Without --out, prints JSON to stdout.
"""
import argparse
import json
import os
import re
import sys

OBFUSCATED_RE = re.compile(r"^[a-z]{1,2}[0-9]?$")
SHARED_ROOTS = {"com", "org", "br", "io", "net", "de", "jp", "co"}
MAX_SHARED_ROOT_DEPTH = 4  # guard against anomalous structure/loop


def load_known_libs(path):
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    entries = []
    for lib in data["libraries"]:
        for prefix in lib["prefixes"]:
            entries.append((tuple(prefix.split(".")), lib["name"]))
    return entries


def match_known_lib(segments, known_libs):
    seg_tuple = tuple(segments)
    for prefix_segments, lib_name in known_libs:
        if seg_tuple == prefix_segments:
            return lib_name
    return None


def classify(sources_dir, known_libs):
    packages = {}

    def walk(dir_path, segments):
        for entry in sorted(os.listdir(dir_path)):
            full = os.path.join(dir_path, entry)
            if not os.path.isdir(full):
                continue
            new_segments = segments + [entry]
            if entry in SHARED_ROOTS and len(new_segments) < MAX_SHARED_ROOT_DEPTH:
                walk(full, new_segments)
                continue
            key = "/".join(new_segments)
            lib = match_known_lib(new_segments, known_libs)
            if lib:
                packages[key] = {"bucket": "known-third-party", "matched_lib": lib}
            elif OBFUSCATED_RE.match(entry):
                packages[key] = {"bucket": "unclassifiable", "matched_lib": None}
            else:
                packages[key] = {"bucket": "business-candidate", "matched_lib": None}

    walk(sources_dir, [])
    return {"packages": packages}


def main():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("sources_dir")
    parser.add_argument("known_libs_json")
    parser.add_argument("--out", default=None)
    args = parser.parse_args()

    known_libs = load_known_libs(args.known_libs_json)
    result = classify(args.sources_dir, known_libs)
    output = json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False)

    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(output + "\n")
    else:
        print(output)


if __name__ == "__main__":
    main()
