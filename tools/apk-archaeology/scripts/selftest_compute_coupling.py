#!/usr/bin/env python3
"""selftest_compute_coupling.py — synthetic fixture: 4 partitions (A/B/C/D)
under a neutral `com.example.app` root, deliberately not modeled on any real
APK. Exercises the collision-handling rule (a node whose files span two
different partitions must be excluded from every metric, never force-
assigned), the intra-partition exclusion (an edge inside one partition must
not count as cross-partition coupling), the degree_strict/degree_raw
divergence (a partition with real cross-partition coupling AND edges to
unmapped generic bases), and the two-pass method-convergence check."""
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(__file__))
from compute_coupling import (  # noqa: E402
    build_prefix_index,
    compute_coupling,
    resolve_node_partition_all,
    resolve_node_partition_single,
)

A = "com/example/app/moduleA"
B = "com/example/app/moduleB"
C = "com/example/app/moduleC"
D = "com/example/app/moduleD"

PARTITIONS = [
    {"prefix": A, "class_count": 2, "kind": "feature"},
    {"prefix": B, "class_count": 2, "kind": "feature"},
    {"prefix": C, "class_count": 1, "kind": "feature"},
    {"prefix": D, "class_count": 1, "kind": "feature"},
]

# node_files keys are bare class names -- graph.json convention
# (extract_graph.py keys nodes by simple class name, not fully-qualified).
NODE_FILES = {
    # module A: an intra-partition edge lives entirely here.
    "ABase1": [f"{A}/ABase1.java"],
    "AImpl1": [f"{A}/AImpl1.java"],
    # module B: a lone node, no edges reference it -- isolated by construction.
    "BBase1": [f"{B}/BBase1.java"],
    # the ONLY multi-file node in this fixture -- a simple-name collision
    # spanning module A and module B. No edges reference it: its exclusion
    # is asserted directly against the resolver functions, not indirectly
    # through a zeroed edge contribution.
    "Collision1": [f"{A}/Collision1.java", f"{B}/Collision1.java"],
    # module C <-> module D: the one real cross-partition edge.
    "CImpl1": [f"{C}/CImpl1.java"],
    "DBase1": [f"{D}/DBase1.java"],
    # GenericBase1/2/3 deliberately absent from node_files: they model
    # generic/base-class edge targets with no known file mapping (e.g. a
    # framework interface) -- always unresolved, regardless of pass.
}

EDGES = [
    {"from": "AImpl1", "to": "ABase1", "kind": "extends"},  # intra-partition (A-A)
    {"from": "CImpl1", "to": "DBase1", "kind": "implements"},  # real cross-partition (C-D)
    {"from": "CImpl1", "to": "GenericBase1", "kind": "extends"},
    {"from": "CImpl1", "to": "GenericBase2", "kind": "implements"},
    {"from": "CImpl1", "to": "GenericBase3", "kind": "implements"},
]

GRAPH = {
    "nodes": sorted(set(NODE_FILES) | {"GenericBase1", "GenericBase2", "GenericBase3"}),
    "node_files": NODE_FILES,
    "edges": EDGES,
    "artifact_warnings": [],
}


def write(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def main():
    with tempfile.TemporaryDirectory() as tmp:
        graph_path = os.path.join(tmp, "graph.json")
        partitions_path = os.path.join(tmp, "partitions.json")
        write(graph_path, json.dumps(GRAPH))
        write(partitions_path, json.dumps(PARTITIONS))

        with open(graph_path, encoding="utf-8") as f:
            graph = json.load(f)
        with open(partitions_path, encoding="utf-8") as f:
            partitions = json.load(f)

        result = compute_coupling(graph, partitions)

        # (a) collision node excluded from both metrics entirely -- proven at
        # the resolver level: its 2 files resolve to 2 DIFFERENT partitions,
        # so it must resolve to None in the ALL-NODES pass too (not force-
        # assigned to A or B), and it has exactly 2 files so the
        # collision-safe pass excludes it by construction as well.
        prefix_index = build_prefix_index(partitions)
        collision_files = NODE_FILES["Collision1"]
        assert resolve_node_partition_all(collision_files, prefix_index) is None, collision_files
        assert resolve_node_partition_single(collision_files, prefix_index) is None, collision_files

        # (b) intra-partition edge (AImpl1 -> ABase1, both module A) does not
        # count as coupling: no pair, degree_strict[A] stays 0. It DOES still
        # count toward degree_raw[A] on both ends (a raw touch, not a
        # coupling claim) -- the two metrics are asserted separately so the
        # distinction documented in the module docstring is proven, not just
        # asserted away.
        assert result["degree_strict"][A] == 0, result["degree_strict"]
        assert result["degree_raw"][A] == 2, result["degree_raw"]
        assert not any(p["a"] == A or p["b"] == A for p in result["pairs"]), result["pairs"]

        # (c) module C: 1 real cross-partition edge (degree_strict) but 3
        # more edges to unmapped generic bases inflate degree_raw well past it.
        assert result["degree_strict"][C] == 1, result["degree_strict"]
        assert result["degree_raw"][C] == 4, result["degree_raw"]
        assert result["degree_raw"][C] > result["degree_strict"][C], result

        # module D: the other side of the one real cross-partition edge.
        assert result["degree_strict"][D] == 1, result["degree_strict"]
        assert result["degree_raw"][D] == 1, result["degree_raw"]

        # the pairs list carries exactly the one C-D cross-partition pair.
        assert result["pairs"] == [{"a": C, "b": D, "count": 1}], result["pairs"]

        # module B: no edges reference it at all -- isolated, and its
        # isolation is a genuine zero (not disguising raw activity).
        assert result["degree_strict"][B] == 0, result["degree_strict"]
        assert result["degree_raw"][B] == 0, result["degree_raw"]

        # isolated == every partition with degree_strict == 0 -- includes A,
        # whose degree_raw is 2, not 0: isolated is a claim about NAMED
        # cross-partition coupling, not about zero inheritance activity.
        assert result["isolated"] == [A, B], result["isolated"]

        # (d) the two pass methods converge on the same distinct-pair count
        # -- the only multi-file node (Collision1) has 0 edges, so it cannot
        # diverge the two passes; every other referenced node has exactly
        # one file and resolves identically in both.
        method_check = result["summary"]["method_check"]
        assert method_check["all_nodes_pairs"] == 1, method_check
        assert method_check["collision_safe_pairs"] == 1, method_check
        assert method_check["all_nodes_pairs"] == method_check["collision_safe_pairs"], method_check

        assert result["summary"]["partitions_total"] == 4, result["summary"]
        assert result["summary"]["edges_total"] == 5, result["summary"]
        assert result["summary"]["cross_partition_pairs"] == 1, result["summary"]

    print(
        "OK: collision node excluded from both metrics, intra-partition edge "
        "excluded from degree_strict but counted in degree_raw, "
        "degree_raw > degree_strict on a partition with generic fan-in, "
        "two-pass method convergence holds"
    )


if __name__ == "__main__":
    main()
