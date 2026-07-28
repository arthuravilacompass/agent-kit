#!/usr/bin/env python3
# desc: enumerates relational claims, anchor problems, manual counts, and anchor-sharing siblings in catalog/findings.yaml for the Relational Fidelity Gate
"""check_relational_claims.py — Relational Fidelity Gate enumerator for apk-archaeology.

Reads a catalog-vivo `findings.yaml` (see catalog/schema.md) and emits a
human-readable worklist for the gate documented in
`plugins/mobile/skills/apk-archaeology/references/method.md`, "The Relational
Fidelity Gate". This script does the ENUMERATION half only — it never judges
whether a claim is true, never edits findings.yaml, and never promotes or
demotes anything. The verification half (opening the two referenced Java
files and deciding whether they really share an instance/field) stays a
human/agent judgment call — same split as extract_permissions.py's
mechanical/interpretive divide.

What it emits, in order:

  (a) RELATIONAL CLAIMS — every finding whose `title` or `notes` matches a
      relational-claim lexicon (mesmo/compartilhado/reutiliza/herda/merge/
      idêntico/same/shared/identical/reuses/...). Discriminator is the FORM
      of the claim, never `confidence` — a cross-validated finding can still
      assert a false identity between two artifacts, and an observed finding
      can assert a true one. Confidence and claim-form are orthogonal axes;
      this script only reads the second one. No skip heuristic by capability
      size either — a finding outside whatever capability is "in scope this
      week" is exactly the kind of finding a size-based cutoff was found (in
      the 2026-07-26 audit) to skip past.

  (b) ANCHOR PROBLEMS — for every `anchor` field that names a `.java` file:
      without `--source-tree`, flags every bare filename (no `/`) as an
      unconfirmed potential ambiguity (a decompiled tree commonly has
      same-named files in different packages — e.g. two `Connection.java` —
      but this cannot be confirmed without walking the tree). With
      `--source-tree`, a bare filename is only flagged when it actually
      collides (more than one file with that name under the tree) — single-
      match bare filenames are dropped as noise, not reported as problems.
      `--source-tree` also flags a named file that does not exist anywhere
      under the tree, or (when a `:N-M` line range is given) a range that
      exceeds the file's actual line count — checked against the FIRST range
      only when an anchor lists more than one comma-separated range (e.g.
      `:77-137,139-156`); a second range that runs past the file's end is not
      caught (see Documented limitations). `logcat:...`-only anchors are
      reported separately, not as problems (they are dynamic-capture
      evidence, not source references).

  (c) MANUAL-COUNT CLAIMS — every `title`/`notes` phrase matching
      `\\d+ (handlers?|tipos?|types?|CTs?|RNs?|findings?|achados?)`. Not a
      verdict — a worklist of counts that were plausibly typed by hand and
      should be re-derived against the artifact they describe before being
      trusted (a "12 handlers" claim is only as good as someone counting the
      actual dispatch-table branches).

  (d) ANCHOR-SHARING SIBLINGS — findings grouped by a normalized anchor
      token (roughly file:method, line ranges stripped). Every group with
      more than one member is a candidate for the failure mode that
      motivated this gate: a correction landing on one finding while a
      sibling that shares the same underlying mechanism keeps the stale
      text. Printed for manual re-read, not auto-diffed — this script does
      not know what "consistent" means for two arbitrary titles.

Documented limitations:
  - `findings.yaml` is read with a hand-rolled line-oriented parser (matches
    `- id: X`, then `  <field>: value` lines), not a YAML library — same
    approach as `suggest-promotions.py`'s `parse_catalog`. It reads `id`,
    `title`, `anchor`, `confidence`, `notes` only; any other field is
    ignored. A finding whose `notes`/`title` value spans multiple physical
    lines (folded YAML block scalars) is read only on its first line — this
    catalog's convention is single-line quoted scalars throughout, so this
    has not been observed to lose data, but it is not a general YAML parser.
  - The relational-claim lexicon and the manual-count pattern are fixed
    regexes in this file (see RELATIONAL_LEXICON / COUNT_RE below) — tuned
    against the AppEvents/Highway/bridge findings this gate was built to
    re-check. A capability with idiom this lexicon does not cover produces
    false negatives silently; it does not produce false positives (a claim
    the lexicon does not recognize is simply absent from the worklist, not
    misclassified).
  - Anchor-existence and line-range checks require `--source-tree` (the
    `jadx/sources` root of a decompile). Without it, section (b) reports
    only the bare-filename-ambiguity check, which needs no filesystem
    access, and says so explicitly rather than silently skipping.
  - Line-range checking reads only the first `N-M` range in a `:N-M,P-Q`
    multi-range anchor. A finding whose second or later range exceeds the
    file's actual length passes silently — not observed in this catalog
    (single ranges throughout), but not general.
  - The sibling grouping in (d) normalizes an anchor by extracting every
    `SomeClass.java` (optionally followed by `:methodName` or `:CONST_NAME`)
    token and stripping numeric line ranges — it does not resolve relative
    vs. full-path anchors to the same key (e.g. `Connection.java` and
    `com/telecorp/.../Connection.java` are DIFFERENT keys here). Section (b)'s
    bare-filename check is what surfaces that ambiguity instead; fixing
    anchors to carry full paths (per L10 in the migration methodology) also
    makes (d)'s grouping exact.

Pure stdlib. Deterministic: same findings.yaml (+ same --source-tree
contents) = same output.

Usage:
  python3 check_relational_claims.py <findings.yaml> [--source-tree <jadx/sources dir>]
"""
import argparse
import os
import re

RELATIONAL_LEXICON = re.compile(
    r"\b("
    r"mesm[ao]s?|compartilhad[ao]s?|reutiliz\w*|reusa\w*|herda\w*|mergead[ao]s?"
    r"|id[êe]ntic[ao]s?|"
    r"same|shared|identical|reuses?|merges?|inherits?"
    r")\b",
    re.IGNORECASE,
)

# Deliberately excludes generic English/Portuguese words that happen to overlap
# common prose ("data" is not "dado", etc.) by requiring word boundaries above;
# still tuned against this catalog's idiom (see docstring limitation).

COUNT_RE = re.compile(
    r"\b(\d+)\s+"
    r"(handlers?|tipos?|types?|CTs?|RNs?|findings?|achados?|listas?|canais?|camadas?)\b",
    re.IGNORECASE,
)

FIELD_RE = re.compile(r"^  (\w+):\s?(.*)$")
ID_RE = re.compile(r"^- id:\s*(\S+)")
JAVA_TOKEN_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*\.java(?::[\w().,\-]+)?")
LINE_RANGE_RE = re.compile(r":(\d+)(?:-(\d+))?")


def parse_findings(path):
    entries = []
    current = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            m = ID_RE.match(line)
            if m:
                if current:
                    entries.append(current)
                current = {"id": m.group(1)}
                continue
            m = FIELD_RE.match(line)
            if m and current:
                current[m.group(1)] = m.group(2).strip().strip("'")
    if current:
        entries.append(current)
    return entries


def find_relational_claims(entries):
    hits = []
    for e in entries:
        text = f"{e.get('title', '')} {e.get('notes', '')}"
        matches = sorted(set(m.group(0).lower() for m in RELATIONAL_LEXICON.finditer(text)))
        if matches:
            hits.append((e["id"], e.get("confidence", "?"), matches))
    return hits


def find_manual_counts(entries):
    hits = []
    for e in entries:
        text = f"{e.get('title', '')} {e.get('notes', '')}"
        matches = COUNT_RE.findall(text)
        if matches:
            hits.append((e["id"], [f"{n} {unit}" for n, unit in matches]))
    return hits


def index_source_tree(source_tree):
    """basename (lowercase) -> list of full paths, for ambiguity/existence checks."""
    index = {}
    for root, _dirs, files in os.walk(source_tree):
        for fname in files:
            if fname.endswith(".java"):
                index.setdefault(fname.lower(), []).append(os.path.join(root, fname))
    return index


def check_anchors(entries, source_tree_index):
    bare_filename = []
    not_found = []
    out_of_range = []
    logcat_only = []
    for e in entries:
        anchor = e.get("anchor", "")
        if not anchor:
            continue
        if "logcat" in anchor.lower() and not JAVA_TOKEN_RE.search(anchor):
            logcat_only.append(e["id"])
            continue
        for tok in JAVA_TOKEN_RE.finditer(anchor):
            java_ref = tok.group(0)
            fname = java_ref.split(":", 1)[0]
            # A full-path reference has a '/' immediately before the filename
            # (e.g. ".../capabilities/Connection.java"); a bare reference doesn't.
            char_before = anchor[tok.start() - 1] if tok.start() > 0 else ""
            is_bare = char_before != "/"
            if source_tree_index is not None:
                matches = source_tree_index.get(fname.lower(), [])
                if not matches:
                    not_found.append((e["id"], fname))
                    continue
                if is_bare and len(matches) > 1:
                    # Real ambiguity: confirmed same-named file in >1 place in the tree.
                    bare_filename.append((e["id"], fname, len(matches)))
                rng = LINE_RANGE_RE.search(java_ref)
                if rng and len(matches) == 1:
                    end_line = int(rng.group(2) or rng.group(1))
                    with open(matches[0], encoding="utf-8", errors="replace") as f:
                        actual_lines = sum(1 for _ in f)
                    if end_line > actual_lines:
                        out_of_range.append((e["id"], java_ref, end_line, actual_lines))
            elif is_bare:
                # No source tree to confirm collision — report as unconfirmed-potential.
                bare_filename.append((e["id"], fname, None))
    return bare_filename, not_found, out_of_range, logcat_only


def group_siblings(entries):
    groups = {}
    for e in entries:
        anchor = e.get("anchor", "")
        for tok in JAVA_TOKEN_RE.finditer(anchor):
            key = re.sub(r":\d[\d,-]*", "", tok.group(0))
            groups.setdefault(key, []).append(e["id"])
    return {k: sorted(set(v)) for k, v in groups.items() if len(set(v)) > 1}


def main():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("findings_yaml")
    parser.add_argument(
        "--source-tree",
        default=None,
        help="jadx/sources root — enables anchor existence/range checks in section (b)",
    )
    args = parser.parse_args()

    entries = parse_findings(args.findings_yaml)
    source_index = index_source_tree(args.source_tree) if args.source_tree else None

    relational = find_relational_claims(entries)
    counts = find_manual_counts(entries)
    bare, not_found, out_of_range, logcat_only = check_anchors(entries, source_index)
    siblings = group_siblings(entries)

    print("=" * 72)
    print(f"RELATIONAL FIDELITY GATE — {args.findings_yaml}")
    print(f"{len(entries)} findings read.")
    print("=" * 72)

    print(f"\n{'─'*72}")
    print(f"(a) RELATIONAL CLAIMS ({len(relational)}) — verify each against source:")
    print(f"{'─'*72}")
    for eid, conf, matches in relational:
        print(f"  ? {eid:<28} [{conf}]  {', '.join(matches)}")
    if not relational:
        print("  (none found)")

    print(f"\n{'─'*72}")
    print(f"(b) ANCHOR PROBLEMS")
    print(f"{'─'*72}")
    if args.source_tree:
        print(f"  Bare filename with CONFIRMED collision in --source-tree: {len(bare)}")
        for eid, fname, n in bare:
            print(f"    ⚠ {eid:<26} {fname} ({n} files with this name in the tree)")
    else:
        print(f"  Bare filename (collision unconfirmed — no --source-tree given): {len(bare)}")
        for eid, fname, _n in bare:
            print(f"    ? {eid:<26} {fname}")
    if args.source_tree:
        print(f"  Not found in --source-tree: {len(not_found)}")
        for eid, fname in not_found:
            print(f"    ✗ {eid:<26} {fname}")
        print(f"  Line range exceeds file length: {len(out_of_range)}")
        for eid, ref, claimed, actual in out_of_range:
            print(f"    ✗ {eid:<26} {ref} (claims line {claimed}, file has {actual})")
    else:
        print("  (--source-tree not given: existence/range checks skipped, not silently — see above)")
    print(f"  logcat-only anchors (not source references): {len(logcat_only)}")

    print(f"\n{'─'*72}")
    print(f"(c) MANUAL-COUNT CLAIMS ({len(counts)}) — re-derive before trusting:")
    print(f"{'─'*72}")
    for eid, matches in counts:
        print(f"  ? {eid:<28} {', '.join(matches)}")
    if not counts:
        print("  (none found)")

    print(f"\n{'─'*72}")
    print(f"(d) ANCHOR-SHARING SIBLINGS ({len(siblings)} groups) — reread every group for contradiction:")
    print(f"{'─'*72}")
    for key, ids in sorted(siblings.items()):
        print(f"  [{key}] {len(ids)}: {', '.join(ids)}")
    if not siblings:
        print("  (none found)")

    print(f"\n{'─'*72}")
    print("NOTE: this script ENUMERATES — it does not judge and does not edit findings.yaml.")
    print("Gate closes when every item above has been read against source and, where wrong, corrected.")
    print("=" * 72)


if __name__ == "__main__":
    main()
