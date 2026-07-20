#!/usr/bin/env python3
# desc: grades endpoints.json fidelity against the REAL source repo (spec §9, non-circular)
"""grade_fidelity.py — Dimension B scorecard (design §9/§10).

Compares endpoints extracted from the decompiled APK against the literal URLs
that actually exist in the real source repository (a git clone, not the
compound's own output) — non-circular grading. The ground truth MUST come from
a real clone of the source repo, never from the tree the pipeline itself
decompiled.

Known limitations (found in the v0 demo, not fixed in this round — see design
doc, "Demo lessons" section):
- `URL_RE` doesn't distinguish a string literal from a Javadoc comment
  (`<a href="...">` has quotes just like a code literal) — the ground truth
  can include a URL that was never compiled. Manual correction was needed in
  the v0 demo; not encoded here.
- `real_urls()` NEVER redacts what it reads from the real source before
  persisting to `--out` — unlike `extract_endpoints.py` (5 rounds of redaction
  hardening, spec §7). If `real_source_dir` is real client code (not public
  like this demo), a secret in the source becomes a secret in the persisted
  scorecard. No real trigger in the demo (NewPipe is public), but real in use
  against client source — a candidate fix before reuse outside the demo.

Pure stdlib.

Usage:
  python3 grade_fidelity.py <endpoints_json> <real_source_dir> [--out <path>]
"""
import argparse
import json
import os
import re
import sys

URL_RE = re.compile(r'"(https?://[^"\s\\]+)"')


def real_urls(real_source_dir):
    urls = set()
    for root, dirs, files in os.walk(real_source_dir):
        if ".git" in dirs:
            dirs.remove(".git")
        for fname in files:
            if not (fname.endswith(".java") or fname.endswith(".kt")):
                continue
            full = os.path.join(root, fname)
            with open(full, encoding="utf-8", errors="replace") as f:
                for line in f:
                    for m in URL_RE.finditer(line):
                        urls.add(m.group(1))
    return urls


def grade(endpoints_json_path, real_source_dir):
    with open(endpoints_json_path, encoding="utf-8") as f:
        extracted = json.load(f)

    extracted_urls = {e["url"] for e in extracted["endpoints"]}
    truth_urls = real_urls(real_source_dir)

    true_positive = extracted_urls & truth_urls
    false_positive = extracted_urls - truth_urls
    false_negative = truth_urls - extracted_urls

    recall = (len(true_positive) / len(truth_urls)) if truth_urls else None

    return {
        "extracted_count": len(extracted_urls),
        "real_count": len(truth_urls),
        "true_positive_count": len(true_positive),
        "false_positive_count": len(false_positive),
        "false_negative_count": len(false_negative),
        "recall": recall,
        "false_positives": sorted(false_positive),
        "false_negatives": sorted(false_negative),
    }


def main():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("endpoints_json")
    parser.add_argument("real_source_dir")
    parser.add_argument("--out", default=None)
    args = parser.parse_args()

    result = grade(args.endpoints_json, args.real_source_dir)
    output = json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False)

    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(output + "\n")
    else:
        print(output)


if __name__ == "__main__":
    main()
