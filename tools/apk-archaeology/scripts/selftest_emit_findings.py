#!/usr/bin/env python3
"""selftest_emit_findings.py — synthetic fixture, no dependency on a real run.

Builds a small synthetic <work_dir>/data/{classify,endpoints,graph,
partitions}.json (shapes learned by inspecting a real run's data/*.json,
values chosen here -- nothing copied), runs build_findings() against it, and
asserts the deterministic outputs against numbers this test controls: 3
endpoints; a 5-node/3-edge graph (chain A-B-C-D plus one isolated node E, so
largest_component == 4 is known by construction); 4 partitions tagged 2
feature + 2 infra. Also proves the non-derivable fields stay null/empty, and
keeps the fail-loud regression coverage for missing required keys."""
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(__file__))
from emit_findings import build_findings, endpoints_metrics, graph_metrics  # noqa: E402

REQUIRED_TOP_LEVEL_KEYS = {
    "schema_version",
    "run",
    "verdict",
    "what_it_is",
    "migration_shape",
    "metrics",
    "blind_spots",
    "next_steps",
    "manifest",
    "caveats",
}


def write_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f)


def make_fixture(work_dir):
    """Write synthetic data/*.json into work_dir. Shapes match the real
    run's data/*.json (classify.json's {bucket, matched_lib} packages map,
    endpoints.json's {endpoints: [...], secrets_redacted}, graph.json's
    {nodes, edges}, partitions.json's list of {kind, ...}) -- values are
    synthetic and chosen so every deterministic count is known up front."""
    data_dir = os.path.join(work_dir, "data")

    write_json(os.path.join(data_dir, "classify.json"), {
        "packages": {
            "com/example/app": {"bucket": "business-candidate", "matched_lib": None},
            "androidx": {"bucket": "known-third-party", "matched_lib": "AndroidX"},
        }
    })

    # 3 endpoints -> metrics.endpoints.total == 3
    write_json(os.path.join(data_dir, "endpoints.json"), {
        "endpoints": [
            {"file": "com/example/app/Api.java", "line": 5, "tag": "business",
             "url": "https://api.example.test/v1/login"},
            {"file": "com/example/app/Api.java", "line": 9, "tag": "business",
             "url": "https://api.example.test/v1/account"},
            {"file": "a/b.java", "line": 3, "tag": "unclassifiable",
             "url": "https://sdk.thirdparty.test/track"},
        ],
        "secrets_redacted": 0,
    })

    # 5 nodes, 3 edges forming a chain A-B-C-D (component size 4) plus one
    # isolated node E (component size 1) -> nodes=5, edges=3,
    # largest_component=4, known by construction.
    write_json(os.path.join(data_dir, "graph.json"), {
        "nodes": ["A", "B", "C", "D", "E"],
        "edges": [
            {"from": "A", "to": "B"},
            {"from": "B", "to": "C"},
            {"from": "C", "to": "D"},
        ],
        "node_files": {},
        "artifact_warnings": [],
    })

    # 4 partitions: 2 feature + 2 infra -> total=4, feature=2, infra=2.
    write_json(os.path.join(data_dir, "partitions.json"), [
        {"prefix": "com/example/app/login", "class_count": 3, "kind": "feature",
         "entry_points": [], "endpoint_files": [], "string_anchors": [],
         "flow_guess": "synthetic login flow", "confidence": "anchored"},
        {"prefix": "com/example/app/account", "class_count": 2, "kind": "feature",
         "entry_points": [], "endpoint_files": [], "string_anchors": [],
         "flow_guess": "synthetic account flow", "confidence": "anchored"},
        {"prefix": "com/example/infra/logging", "class_count": 5, "kind": "infra",
         "entry_points": [], "endpoint_files": [], "string_anchors": [],
         "flow_guess": "synthetic logging infra", "confidence": "anchored"},
        {"prefix": "com/example/infra/update", "class_count": 1, "kind": "infra",
         "entry_points": [], "endpoint_files": [], "string_anchors": [],
         "flow_guess": "synthetic update infra", "confidence": "anchored"},
    ])


def main():
    with tempfile.TemporaryDirectory() as tmp:
        work_dir = os.path.join(tmp, "run-2020-06-15")
        make_fixture(work_dir)

        result = build_findings(work_dir)

        # 1/4 — deterministic values match the synthetic fixture exactly.
        metrics = result["metrics"]
        assert metrics["endpoints"]["total"] == 3, metrics["endpoints"]
        assert metrics["graph"]["nodes"] == 5, metrics["graph"]
        assert metrics["graph"]["edges"] == 3, metrics["graph"]
        assert metrics["graph"]["largest_component"] == 4, metrics["graph"]
        assert metrics["partitions"]["total"] == 4, metrics["partitions"]
        assert metrics["partitions"]["feature"] == 2, metrics["partitions"]
        assert metrics["partitions"]["infra"] == 2, metrics["partitions"]
        assert metrics["graph"]["kind"] == (
            "INHERITANCE (extends/implements) ONLY -- not call/import/coupling"
        ), metrics["graph"]["kind"]

        # 2/4 — the emitter does NOT fabricate what data/*.json cannot
        # support. classify.json only carries {bucket, matched_lib} per
        # package, no file counts -- so first_party_mass / obfuscated_island
        # must stay null/empty regardless of the fixture's contents.
        assert result["what_it_is"]["first_party_mass"] == {}, result["what_it_is"]["first_party_mass"]
        obf = result["what_it_is"]["obfuscated_island"]
        assert obf["package"] is None, obf
        assert obf["files"] is None, obf
        assert obf["note"] is None, obf

        # 3/4 — bridge_capabilities.value/.domains and
        # bridge_pilot_handlers.value come from analysis docs, never from
        # data/*.json -- must stay null.
        assert metrics["bridge_capabilities"]["value"] is None, metrics["bridge_capabilities"]
        assert metrics["bridge_capabilities"]["domains"] is None, metrics["bridge_capabilities"]
        assert metrics["bridge_pilot_handlers"]["value"] is None, metrics["bridge_pilot_handlers"]

        # Synthesized top-level fields stay null/empty placeholders too.
        assert result["verdict"] == {"feasibility": None, "one_line": None, "confidence": None}, result["verdict"]
        assert result["blind_spots"] == [], result["blind_spots"]
        assert result["next_steps"] == [], result["next_steps"]
        assert result["caveats"] == [], result["caveats"]
        for bucket in result["migration_shape"].values():
            assert bucket == {"what": None, "size": None, "note": None}, bucket

        # run.id/date are read off the work_dir folder name convention
        # ("run-YYYY-MM-DD"); package/version/sha256/tooling/mode are not
        # derivable from data/*.json and stay null unless passed as CLI
        # overrides.
        assert result["run"]["id"] == "run-2020-06-15", result["run"]
        assert result["run"]["date"] == "2020-06-15", result["run"]
        for key in ("package", "version", "sha256", "tooling", "mode"):
            assert result["run"][key] is None, result["run"]

        # manifest: one entry per data/*.json this script actually found on
        # disk, each with a deterministic "raw" status and a null
        # (agent-authored) role.
        assert "data/classify.json" in result["manifest"], result["manifest"]
        assert "data/endpoints.json" in result["manifest"], result["manifest"]
        assert "data/graph.json" in result["manifest"], result["manifest"]
        assert "data/partitions.json" in result["manifest"], result["manifest"]
        for entry in result["manifest"].values():
            assert entry["status"] == "raw", entry
            assert entry["role"] is None, entry

        # 4/4 — structural: every schema-required top-level key is present
        # (plain key-presence check, no jsonschema dependency required).
        missing = REQUIRED_TOP_LEVEL_KEYS - set(result.keys())
        assert not missing, f"missing required top-level keys: {missing}"
        extra = set(result.keys()) - REQUIRED_TOP_LEVEL_KEYS
        assert not extra, f"unexpected top-level keys not in schema: {extra}"

    print(
        "OK: emit_findings deterministic values match the synthetic fixture "
        "(endpoints=3, graph nodes=5/edges=3/largest_component=4, "
        "partitions=4 [2 feature/2 infra]); non-derivable fields stay null"
    )


def test_endpoints_missing_key_fails_loud():
    """Regression guard: endpoints.json PRESENT but missing its required
    'endpoints' key must fail loud (SystemExit), never silently emit
    total=0 via .get(key, [])."""
    try:
        endpoints_metrics({"not_endpoints": []})
        raise AssertionError("expected SystemExit for endpoints.json missing 'endpoints' key")
    except SystemExit as e:
        assert "endpoints.json" in str(e), str(e)
        assert "endpoints" in str(e), str(e)
    print("OK: endpoints.json missing required key fails loud, not a silent 0")


def test_graph_missing_key_fails_loud():
    """Same guard for graph.json's required 'nodes'/'edges' keys."""
    try:
        graph_metrics({"nodes": []})  # missing 'edges'
        raise AssertionError("expected SystemExit for graph.json missing 'edges' key")
    except SystemExit as e:
        assert "graph.json" in str(e), str(e)
        assert "edges" in str(e), str(e)
    print("OK: graph.json missing required key fails loud, not a silent 0")


if __name__ == "__main__":
    main()
    test_endpoints_missing_key_fails_loud()
    test_graph_missing_key_fails_loud()
