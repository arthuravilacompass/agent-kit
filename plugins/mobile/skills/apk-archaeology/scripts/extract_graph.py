#!/usr/bin/env python3
# desc: dependency graph (Lakos-style) between business classes (spec §5 [4])
"""extract_graph.py — Dimension C of apk-archaeology (design §5 [4]).

Reference graph (extends/implements) ONLY between classes in business-candidate
packages. It's a RECONSTRUCTION via regex over jadx-decompiled Java, not a real
parser — it carries the decompiler artifacts documented in the spec (erased
generics, synthetic classes like $ExternalSyntheticLambda0, symbols merged/inlined
by R8). Edges to types outside the discovered class set (framework, external lib)
are dropped — this isn't a graph of every dependency, only the ones internal to
business code.

Deliberate asymmetry with extract_endpoints.py: only business-candidate enters
here (unclassifiable never becomes a module-graph node — see spec §5 [4]).

Pure stdlib. Deterministic.

Usage:
  python3 extract_graph.py <sources_dir> <classify_json> [--out <path>]
"""
import argparse
import json
import os
import re
import sys

CLASS_DECL_RE = re.compile(
    r"\b(?:public|private|protected|abstract|final|static|\s)*"
    r"(?:class|interface|enum)\s+(\w+)"
    r"(?:<[^>]*>)?"
    r"(?:\s+extends\s+([\w.,\s<>]+?))?"
    r"(?:\s+implements\s+([\w.,\s<>]+))?"
    r"\s*\{"
)

SYNTHETIC_RE = re.compile(r"\$[A-Za-z0-9_]*(Lambda|Synthetic)")


def business_dirs(classify_result):
    return {
        key
        for key, info in classify_result["packages"].items()
        if info["bucket"] == "business-candidate"
    }


def simple_name(qualified):
    return qualified.strip().split(".")[-1].split("<")[0].strip()


def split_type_list(blob):
    """Splits a comma-separated type list respecting <> depth, so a
    multi-argument generic isn't broken in the middle (e.g.
    `BaseRepo<Response, Handler<Foo>>` is ONE type, not two — a naive
    comma split fabricated a false edge to whatever name was left over
    after the split, if it happened to match a real discovered class;
    review finding)."""
    parts = []
    depth = 0
    current = []
    for ch in blob:
        if ch == "<":
            depth += 1
            current.append(ch)
        elif ch == ">":
            depth -= 1
            current.append(ch)
        elif ch == "," and depth == 0:
            parts.append("".join(current))
            current = []
        else:
            current.append(ch)
    if current:
        parts.append("".join(current))
    return parts


def parse_file(path):
    with open(path, encoding="utf-8", errors="replace") as f:
        content = f.read()
    declarations = []
    for m in CLASS_DECL_RE.finditer(content):
        class_name, extends, implements = m.group(1), m.group(2), m.group(3)
        interfaces = []
        if implements:
            interfaces = [simple_name(i) for i in split_type_list(implements) if i.strip()]
        # extends allows multiple parents: a class only has 1 in practice, but a
        # Java interface allows `interface Foo extends A, B` — we handle both with
        # the same list (review finding: capturing only 1 made the WHOLE match fail
        # when there was a comma, silently dropping the node and all of its edges)
        parents = [simple_name(e) for e in split_type_list(extends) if e.strip()] if extends else []
        declarations.append((class_name, parents, interfaces))
    return declarations


def extract_graph(sources_dir, classify_result):
    business = business_dirs(classify_result)
    all_classes = set()
    raw_edges = []
    artifact_warnings = []

    for pkg_key in sorted(business):
        pkg_dir = os.path.join(sources_dir, pkg_key)
        if not os.path.isdir(pkg_dir):
            continue
        for root, _dirs, files in os.walk(pkg_dir):
            for fname in files:
                if not fname.endswith(".java"):
                    continue
                if SYNTHETIC_RE.search(fname):
                    artifact_warnings.append(f"synthetic class skipped: {fname}")
                    continue
                full = os.path.join(root, fname)
                for class_name, parents, interfaces in parse_file(full):
                    all_classes.add(class_name)
                    for parent in parents:
                        raw_edges.append((class_name, parent, "extends"))
                    for iface in interfaces:
                        raw_edges.append((class_name, iface, "implements"))

    edges = [
        {"from": f, "to": t, "kind": k}
        for (f, t, k) in sorted(set(raw_edges))
        if t in all_classes
    ]

    return {
        "nodes": sorted(all_classes),
        "edges": edges,
        "artifact_warnings": sorted(set(artifact_warnings)),
    }


def main():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("sources_dir")
    parser.add_argument("classify_json")
    parser.add_argument("--out", default=None)
    args = parser.parse_args()

    with open(args.classify_json, encoding="utf-8") as f:
        classify_result = json.load(f)

    result = extract_graph(args.sources_dir, classify_result)
    output = json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False)

    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(output + "\n")
    else:
        print(output)


if __name__ == "__main__":
    main()
