#!/usr/bin/env python3
# desc: derives partition-to-partition coupling from the inheritance graph, split into a strict and a raw degree metric
"""compute_coupling.py — partition-to-partition coupling for apk-archaeology.

Derives cross-partition coupling from extract_graph.py's inheritance graph
(graph.json: nodes, node_files, edges of kind extends/implements) and a
partition manifest (partitions.json: a list of {prefix, class_count, ...},
one per partition from the per-feature loop's partitioning step). Every
graph node is mapped to a partition by longest-prefix match of its source
file path(s) (graph.json's node_files entries) against partition prefixes.

  degree_strict  — per-partition count of cross-partition edges: both
                   endpoints resolve, unambiguously, to two DIFFERENT named
                   partitions. This is the real coupling signal — what a
                   downstream consumer should read when asking "how
                   entangled is this partition with OTHER partitions."
  degree_raw     — per-partition count of ANY inheritance edge with an
                   endpoint resolving to that partition, including edges
                   whose OTHER endpoint is unmapped (a generic/base-class
                   node with no partition match) or intra-partition. This is
                   a noisier, inflated metric: a thin, standalone module
                   with a large generic public API surface (many classes
                   implementing framework interfaces) can show a degree_raw
                   many multiples of its degree_strict while carrying almost
                   no real coupling to other named partitions.
  pairs          — distinct unordered cross-partition pairs with an edge
                   count (from the same resolution degree_strict uses).
  isolated       — partitions with degree_strict == 0 (candidates for a
                   standalone/strangler-fig extraction). This is a claim
                   about NAMED cross-partition coupling only, not about zero
                   inheritance activity — an isolated partition can still
                   have degree_raw > 0.

Method check (summary.method_check.all_nodes_pairs vs. .collision_safe_pairs):
two independent passes resolve every node to a partition and count distinct
cross-partition pairs. (a) ALL NODES — every node's file(s) are each
longest-prefix-matched; if a node's files disagree on which partition they
belong to (a simple-name collision — graph.json keys nodes by bare class
name, which collides across packages), the node is EXCLUDED, never force-
assigned to one of the colliding partitions. (b) COLLISION-SAFE — only nodes
with exactly one file are resolved at all. The two passes are expected to
converge on the same distinct-pair count; that convergence is the trust
argument for the collision-handling rule in (a) — a naive "pick one file and
assign the node to it anyway" resolution instead inflates cross-partition
edges, because a handful of common collision names carry disproportionate
inheritance fan-in and would get force-assigned to one arbitrary partition.

Documented limitations:
  - graph.json is INHERITANCE ONLY (extends/implements) — extract_graph.py
    never emits a call/import/composition graph. This undercounts real
    coupling: a partition with degree_strict == 0 is not proven decoupled
    at runtime, only at the class-hierarchy level.
  - A collision node (its node_files span >1 different partition) is
    excluded from BOTH degree_strict and degree_raw entirely, for every
    edge it takes part in — not counted toward any partition. This trades a
    small amount of recall (that node's real edges become invisible) for
    precision (no arbitrary assignment); it is a deliberate, bounded blind
    spot, not chased with a tie-break rule.
  - degree_raw is NOT a reliable coupling signal on its own (see above). It
    is provided for transparency — so a reader can see how much of a
    partition's raw inheritance activity is real cross-partition coupling
    vs. generic fan-in — never as the primary metric a downstream
    deliverable ranks partitions by; downstream consumers MUST prefer
    degree_strict for that judgment.
  - Longest-prefix matching treats partitions.json's prefixes as the ground
    truth for node ownership; a node whose file lives outside every listed
    prefix resolves to None exactly like a genuine collision or an unmapped
    generic base — the three cases are indistinguishable in the output, by
    construction (all three are "not attributable to a named partition").

Pure stdlib. Deterministic: same graph.json/partitions.json = same output.

Usage:
  python3 compute_coupling.py <graph_json> <partitions_json> --out <path>
  Default --out is data/coupling.json.
"""
import argparse
import json
import os


def build_prefix_index(partitions):
    """Partition prefixes as (segments-tuple, prefix) pairs, sorted by depth
    (segment count) descending, then alphabetically for a deterministic
    tie-break — used for longest-prefix matching below."""
    index = []
    for p in partitions:
        prefix = p["prefix"]
        segs = tuple(prefix.split("/"))
        index.append((segs, prefix))
    index.sort(key=lambda t: (-len(t[0]), t[1]))
    return index


def match_partition_for_path(file_path, prefix_index):
    """Longest-prefix match of file_path's segments against partition
    prefixes — a path-SEGMENT match, not a raw substring match (so
    'com/example/foo' does not match a file under 'com/example/foobar/...').
    Returns the matching prefix, or None if no partition prefix matches."""
    path_segs = tuple(file_path.split("/"))
    best = None
    best_depth = 0
    for segs, prefix in prefix_index:
        depth = len(segs)
        if depth <= best_depth:
            # index is sorted by depth desc -- nothing shallower left can
            # beat the best match already found; safe to stop scanning.
            break
        if path_segs[:depth] == segs:
            best = prefix
            best_depth = depth
    return best


def resolve_node_partition_all(files, prefix_index):
    """ALL-NODES resolution: longest-prefix-match each of the node's
    candidate file paths independently, then take the SET of distinct
    partitions that result. Exactly one distinct partition (all files agree,
    or there is only one file) resolves unambiguously. Zero (nothing
    matched) or more than one (the node's files genuinely span different
    partitions -- a simple-name collision) both resolve to None: there is no
    principled way to pick one of several colliding partitions, and forcing
    a pick is what would break convergence with the collision-safe pass (see
    module docstring)."""
    matched = set()
    for fp in files:
        prefix = match_partition_for_path(fp, prefix_index)
        if prefix is not None:
            matched.add(prefix)
    if len(matched) == 1:
        return next(iter(matched))
    return None


def resolve_node_partition_single(files, prefix_index):
    """COLLISION-SAFE resolution: only a node with EXACTLY one candidate
    file is resolved at all; everything else (0 or >1 files) is None."""
    if len(files) != 1:
        return None
    return match_partition_for_path(files[0], prefix_index)


def compute_pairs_and_degrees(edges, node_partition):
    """One pass over the edge list against a node->partition map (values may
    be None for an unresolved node). Returns (pair_counts, degree_strict,
    degree_raw):
      - degree_raw accrues for EITHER endpoint that resolves to a partition,
        regardless of what the other endpoint is -- an unmapped/generic base
        class, or even the SAME partition on both ends. This is "any edge
        touching me", not a coupling claim.
      - pair_counts / degree_strict only accrue when BOTH endpoints resolve,
        to two DIFFERENT partitions. An intra-partition edge (both ends
        resolve to the same partition) contributes to degree_raw on both
        sides but never to a pair or to degree_strict."""
    pair_counts = {}
    degree_strict = {}
    degree_raw = {}
    for e in edges:
        pa = node_partition.get(e["from"])
        pb = node_partition.get(e["to"])
        if pa is not None:
            degree_raw[pa] = degree_raw.get(pa, 0) + 1
        if pb is not None:
            degree_raw[pb] = degree_raw.get(pb, 0) + 1
        if pa is None or pb is None or pa == pb:
            continue
        key = tuple(sorted((pa, pb)))
        pair_counts[key] = pair_counts.get(key, 0) + 1
        degree_strict[pa] = degree_strict.get(pa, 0) + 1
        degree_strict[pb] = degree_strict.get(pb, 0) + 1
    return pair_counts, degree_strict, degree_raw


def compute_coupling(graph, partitions):
    nodes = graph["nodes"]
    edges = graph["edges"]
    node_files = graph.get("node_files", {})
    prefix_index = build_prefix_index(partitions)
    all_prefixes = [p["prefix"] for p in partitions]

    node_partition_all = {
        n: resolve_node_partition_all(node_files.get(n, []), prefix_index) for n in nodes
    }
    node_partition_single = {
        n: resolve_node_partition_single(node_files.get(n, []), prefix_index) for n in nodes
    }

    pairs_all, degree_strict, degree_raw = compute_pairs_and_degrees(edges, node_partition_all)
    pairs_single, _, _ = compute_pairs_and_degrees(edges, node_partition_single)

    for prefix in all_prefixes:
        degree_strict.setdefault(prefix, 0)
        degree_raw.setdefault(prefix, 0)

    isolated = sorted(p for p in all_prefixes if degree_strict.get(p, 0) == 0)

    pairs = [
        {"a": a, "b": b, "count": c}
        for (a, b), c in sorted(pairs_all.items(), key=lambda kv: (-kv[1], kv[0]))
    ]

    return {
        "summary": {
            "partitions_total": len(partitions),
            "edges_total": len(edges),
            "cross_partition_pairs": len(pairs_all),
            "method_check": {
                "all_nodes_pairs": len(pairs_all),
                "collision_safe_pairs": len(pairs_single),
            },
        },
        "pairs": pairs,
        "degree_strict": degree_strict,
        "degree_raw": degree_raw,
        "isolated": isolated,
    }


def main():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("graph_json")
    parser.add_argument("partitions_json")
    parser.add_argument("--out", default="data/coupling.json")
    args = parser.parse_args()

    with open(args.graph_json, encoding="utf-8") as f:
        graph = json.load(f)
    with open(args.partitions_json, encoding="utf-8") as f:
        partitions = json.load(f)

    result = compute_coupling(graph, partitions)
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
