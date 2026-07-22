#!/usr/bin/env python3
# desc: emits the deterministic skeleton of findings.json from a run's data/*.json (design §3)
"""emit_findings.py — Honest sync reach for apk-archaeology (design §3).

findings.json is the headline source-of-truth artifact for a run. Per
references/findings.schema.json, every field carries an `x-source` tag:
deterministic (mechanically computable from data/*.json), synthesized
(agent-authored judgment/narrative), or mixed (both). This script owns ONLY
the deterministic slice — it reads <work_dir>/data/*.json and fills the
fields genuinely computable from them, leaving every synthesized field as a
null / empty placeholder so the agent that runs next knows exactly what it
still has to author. It never fabricates a value it cannot derive.

What this script actually derives from data/*.json (verified against the
real run-2026-07-17 fixture, see selftest_emit_findings.py):
  - metrics.endpoints.total       <- len(endpoints.json["endpoints"])
  - metrics.graph.nodes/edges     <- len(graph.json["nodes"]/["edges"])
  - metrics.graph.largest_component <- largest connected component, computed
                                        via union-find over graph.json's
                                        nodes+edges (treated as undirected)
  - metrics.graph.kind            <- fixed constant: extract_graph.py only
                                      ever emits an inheritance-only graph
  - metrics.partitions.total/feature/infra <- counted from partitions.json's
                                                "kind" tag (feature vs infra)
  - manifest                      <- one entry per data/*.json this script
                                      actually consumed, path+status only
                                      (status "raw" is a structural fact;
                                      "role" is a one-line description, left
                                      for the agent to author)
  - run.id/date                   <- read off the work_dir folder name
                                      (convention: "run-YYYY-MM-DD"); this is
                                      folder-layout metadata, not narrative

What this script deliberately does NOT derive (checked against the real
classify.json/classify.v1.json — neither carries per-package file counts,
only {bucket, matched_lib}; partitions.json's class_count is keyed by a
different, finer partition prefix than the top-level namespaces
what_it_is.first_party_mass wants, so it cannot be summed into the same
numbers without curation):
  - what_it_is.first_party_mass        -> {} (no per-package counts found)
  - what_it_is.obfuscated_island        -> all 3 fields null (selecting WHICH
                                            known-third-party package is
                                            "the island", not just counting
                                            files in it, is a judgment call)
  - metrics.bridge_capabilities.value/domains  -> null (comes from analysis
                                                   docs, not data/*.json)
  - metrics.bridge_pilot_handlers.value        -> null (same)
  - every metrics.*.note                       -> null (narrative, not count)
  - verdict, migration_shape, blind_spots, next_steps, caveats,
    what_it_is.nature/build_signal               -> null / empty (agent-authored)
  - run.sha256/tooling/mode/package/version      -> null unless passed via CLI
    flags (trivial operator-supplied overrides; still not derivable from
    data/*.json itself)

Pure stdlib. Deterministic: same data/*.json + same CLI flags = same output.

Usage:
  python3 emit_findings.py <work_dir> [--out <path>] [--sha256 ...]
                            [--tooling ...] [--mode ...] [--package ...]
                            [--version ...]
  Without --out, prints JSON to stdout.
"""
import argparse
import json
import os
import re
import sys

SCHEMA_VERSION = "0.1-pilot"

# extract_graph.py (design §5 [4]) only ever reconstructs extends/implements
# edges between business-candidate classes — never a call/import/coupling
# graph. This is a property of the tool, fixed across every run, not a
# per-run measurement.
GRAPH_KIND = "INHERITANCE (extends/implements) ONLY -- not call/import/coupling"

# The raw data artifacts this skill's pipeline produces per run. Manifest
# entries are only emitted for the ones actually present on disk — this
# script never asserts an artifact exists that it didn't check for.
KNOWN_DATA_FILES = [
    "classify.json",
    "endpoints.json",
    "graph.json",
    "partitions.json",
    "coupling.json",
    "layers.json",
    "permissions.json",
]

RUN_ID_DATE_RE = re.compile(r"run-(\d{4}-\d{2}-\d{2})")


def load_json(path):
    if not os.path.isfile(path):
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def largest_connected_component(nodes, edges):
    """Union-find over the inheritance graph, treated as undirected (an
    'extends' or 'implements' edge connects two classes into the same
    component regardless of direction). Returns the size of the largest
    component; isolated nodes each start as their own component of size 1."""
    parent = {n: n for n in nodes}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        # Edge endpoints are expected to already be in `nodes` (extract_graph.py
        # drops edges to types outside its discovered class set) — guard
        # anyway so a malformed/edited graph.json can't KeyError this script.
        parent.setdefault(a, a)
        parent.setdefault(b, b)
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb

    for e in edges:
        union(e["from"], e["to"])

    sizes = {}
    for n in parent:
        root = find(n)
        sizes[root] = sizes.get(root, 0) + 1

    return max(sizes.values()) if sizes else 0


def endpoints_metrics(endpoints_data):
    if endpoints_data is None:
        return {"total": None, "note": None}
    if "endpoints" not in endpoints_data:
        raise SystemExit("emit_findings: endpoints.json missing required key 'endpoints'")
    return {"total": len(endpoints_data["endpoints"]), "note": None}


def graph_metrics(graph_data):
    if graph_data is None:
        return {"nodes": None, "edges": None, "kind": GRAPH_KIND, "largest_component": None}
    if "nodes" not in graph_data:
        raise SystemExit("emit_findings: graph.json missing required key 'nodes'")
    if "edges" not in graph_data:
        raise SystemExit("emit_findings: graph.json missing required key 'edges'")
    nodes = graph_data["nodes"]
    edges = graph_data["edges"]
    return {
        "nodes": len(nodes),
        "edges": len(edges),
        "kind": GRAPH_KIND,
        "largest_component": largest_connected_component(nodes, edges),
    }


def partitions_metrics(partitions_data):
    if partitions_data is None:
        return {"total": None, "feature": None, "infra": None}
    total = len(partitions_data)
    feature = sum(1 for p in partitions_data if p.get("kind") == "feature")
    infra = sum(1 for p in partitions_data if p.get("kind") == "infra")
    return {"total": total, "feature": feature, "infra": infra}


def build_manifest(work_dir):
    manifest = {}
    for fname in KNOWN_DATA_FILES:
        full = os.path.join(work_dir, "data", fname)
        if os.path.isfile(full):
            manifest[f"data/{fname}"] = {"role": None, "status": "raw"}
    return manifest


def derive_run_identity(work_dir):
    run_id = os.path.basename(os.path.normpath(work_dir))
    m = RUN_ID_DATE_RE.match(run_id)
    date = m.group(1) if m else None
    return run_id, date


def migration_bucket_placeholder():
    return {"what": None, "size": None, "note": None}


def build_findings(work_dir, overrides=None):
    overrides = overrides or {}

    data_dir = os.path.join(work_dir, "data")
    classify_data = load_json(os.path.join(data_dir, "classify.json"))
    endpoints_data = load_json(os.path.join(data_dir, "endpoints.json"))
    graph_data = load_json(os.path.join(data_dir, "graph.json"))
    partitions_data = load_json(os.path.join(data_dir, "partitions.json"))

    run_id, run_date = derive_run_identity(work_dir)

    # `classify_data` is inspected (loaded) per the design brief even though
    # no field below is currently derived from it: it carries {bucket,
    # matched_lib} per package, not the per-package file counts that
    # what_it_is.first_party_mass / obfuscated_island.files would need. Kept
    # as a variable (not just silently unread) so a future extension that
    # DOES add file counts to classify.json has an obvious place to plug in.
    del classify_data

    return {
        "schema_version": SCHEMA_VERSION,
        "run": {
            "id": run_id,
            "date": run_date,
            "package": overrides.get("package"),
            "version": overrides.get("version"),
            "sha256": overrides.get("sha256"),
            "tooling": overrides.get("tooling"),
            "mode": overrides.get("mode"),
        },
        "verdict": {
            "feasibility": None,
            "one_line": None,
            "confidence": None,
        },
        "what_it_is": {
            "nature": None,
            # No per-package file counts are derivable from classify.json /
            # classify.v1.json (verified: both only carry {bucket,
            # matched_lib}) — left empty rather than fabricated.
            "first_party_mass": {},
            "obfuscated_island": {
                "package": None,
                "files": None,
                "note": None,
            },
            "build_signal": None,
        },
        "migration_shape": {
            "port_native": migration_bucket_placeholder(),
            "stays_webview": migration_bucket_placeholder(),
            "bridge_to_reimplement": migration_bucket_placeholder(),
            "infra_platform": migration_bucket_placeholder(),
        },
        "metrics": {
            "bridge_capabilities": {"value": None, "domains": None, "note": None},
            "partitions": partitions_metrics(partitions_data),
            "endpoints": endpoints_metrics(endpoints_data),
            "graph": graph_metrics(graph_data),
            "bridge_pilot_handlers": {"value": None, "note": None},
        },
        "blind_spots": [],
        "next_steps": [],
        "manifest": build_manifest(work_dir),
        "caveats": [],
    }


def main():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("work_dir", help="Run directory containing data/*.json")
    parser.add_argument("--out", default=None, help="Output path (default: print to stdout)")
    parser.add_argument("--sha256", default=None, help="SHA-256 of the analyzed APK (not derivable from data/)")
    parser.add_argument("--tooling", default=None, help="Toolchain versions string (not derivable from data/)")
    parser.add_argument("--mode", default=None, help="Which passes ran (static-only, static+dynamic, ...)")
    parser.add_argument("--package", default=None, help="Android application package id")
    parser.add_argument("--version", default=None, help="APK version name/code")
    args = parser.parse_args()

    overrides = {
        "sha256": args.sha256,
        "tooling": args.tooling,
        "mode": args.mode,
        "package": args.package,
        "version": args.version,
    }

    result = build_findings(args.work_dir, overrides)
    output = json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False)

    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(output + "\n")
    else:
        print(output)


if __name__ == "__main__":
    main()
