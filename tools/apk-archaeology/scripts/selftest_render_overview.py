#!/usr/bin/env python3
# desc: gate for render_overview.py — synthetic fixture, deterministic values, idempotency, AGENT passthrough
"""selftest_render_overview.py — gate for render_overview.py.

Builds a small synthetic findings.json (shape learned from
references/findings.schema.json and a real run's findings.json, values
chosen here -- nothing copied) and renders it against the REAL
overview.template.md. Asserts:

  1. Correct synthetic deterministic values appear in the output (package,
     version, sha256, bridge capabilities, partitions, endpoints, graph).
  2. Idempotency: rendering twice from the same inputs is byte-identical.
  3. The AGENT:START/END marker survives untouched (synthesized BLUF section
     is not clobbered).
  4. No unrendered {{ }} placeholder syntax leaks into the output.
  5. The manifest loop expanded (spot-check one row).

Pure stdlib. Exit 0 on pass, non-zero with a clear message on fail.
"""
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(__file__))
from render_overview import render  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(HERE, "..", "references", "overview.template.md")


def make_findings():
    """Small synthetic findings.json carrying every field
    overview.template.md substitutes, plus the other schema-required
    top-level keys as minimal filler. Values are synthetic and distinct
    from any real run's numbers."""
    return {
        "schema_version": "0.1-pilot",
        "run": {
            "id": "run-2020-06-15",
            "date": "2020-06-15",
            "package": "com.example.testapp",
            "version": "1.2.3 (vc 42)",
            "sha256": "0123456789abcdef" * 4,
            "tooling": "jadx 0.0.0, apktool 0.0.0, python 0.0.0",
            "mode": "static-only; synthetic fixture",
        },
        "verdict": {"feasibility": "VIABLE", "one_line": "synthetic verdict", "confidence": "high"},
        "what_it_is": {
            "nature": "synthetic",
            "first_party_mass": {},
            "obfuscated_island": {"package": None, "files": None, "note": None},
            "build_signal": "synthetic",
        },
        "migration_shape": {
            "port_native": {"what": "x", "size": "y", "note": "z"},
            "stays_webview": {"what": "x", "size": "y", "note": "z"},
            "bridge_to_reimplement": {"what": "x", "size": "y", "note": "z"},
            "infra_platform": {"what": "x", "size": "y", "note": "z"},
        },
        "metrics": {
            "bridge_capabilities": {"value": 5, "domains": 2, "note": "synthetic"},
            "partitions": {"total": 4, "feature": 2, "infra": 2},
            "endpoints": {"total": 3, "note": "synthetic"},
            "graph": {
                "nodes": 5,
                "edges": 3,
                "kind": "INHERITANCE (extends/implements) ONLY -- not call/import/coupling",
                "largest_component": 4,
            },
            "bridge_pilot_handlers": {"value": 1, "note": "synthetic"},
        },
        "blind_spots": ["synthetic blind spot"],
        "next_steps": [],
        "manifest": {
            "data/classify.json": {"role": "Synthetic classifier output", "status": "raw"},
            "data/endpoints.json": {"role": "Synthetic endpoint extraction", "status": "raw"},
            "data/graph.json": {"role": "Synthetic inheritance graph", "status": "raw"},
            "data/partitions.json": {"role": "Synthetic partition list", "status": "raw"},
        },
        "caveats": [],
    }


def main():
    with tempfile.TemporaryDirectory() as tmp:
        findings_path = os.path.join(tmp, "findings.json")
        with open(findings_path, "w", encoding="utf-8") as f:
            json.dump(make_findings(), f)

        with open(findings_path, encoding="utf-8") as f:
            findings = json.load(f)
        with open(TEMPLATE, encoding="utf-8") as f:
            template_text = f.read()

        output1 = render(findings, template_text)
        output2 = render(findings, template_text)

        assert output1 == output2, "render is not idempotent -- two runs on the same inputs differ"

        # Deterministic values (metrics + provenance) must be present verbatim.
        assert "com.example.testapp" in output1, "run.package missing from output"
        assert "1.2.3 (vc 42)" in output1, "run.version missing from output"
        assert "0123456789abcdef" * 4 in output1, "run.sha256 missing from output"
        assert "Bridge capabilities: 5 across 2 domains" in output1, (
            "metrics.bridge_capabilities.value/.domains (5/2) missing from output"
        )
        assert "Partitions: 4 total (2 feature / 2 infra)" in output1, (
            "metrics.partitions.total/.feature/.infra (4/2/2) missing from output"
        )
        assert "Endpoints: 3" in output1, "metrics.endpoints.total (3) missing from output"
        assert "Graph: 5 nodes / 3 edges" in output1, (
            "metrics.graph.nodes/.edges (5/3) missing from output"
        )
        assert "largest component 4" in output1, (
            "metrics.graph.largest_component (4) missing from output"
        )
        assert "Bridge-pilot handlers: 1" in output1, (
            "metrics.bridge_pilot_handlers.value (1) missing from output"
        )

        # AGENT:START/END marker must survive verbatim -- synthesized BLUF is
        # never script-filled.
        assert "<!-- AGENT:START bluf -->" in output1, "AGENT:START bluf marker did not survive"
        assert "<!-- AGENT:END bluf -->" in output1, "AGENT:END bluf marker did not survive"
        assert "Write the Q1-Q4 narrative here" in output1, (
            "AGENT block instructional placeholder text did not survive"
        )

        # Manifest loop expanded into real rows (spot-check one known key).
        assert "data/classify.json" in output1, "manifest loop row for data/classify.json missing"
        assert "Synthetic classifier output" in output1, "manifest row 'role' field not substituted"
        assert "raw" in output1, "manifest row 'status' field not substituted"

        # No leftover template syntax anywhere in the rendered output.
        assert "{{" not in output1, f"unrendered placeholder leaked into output:\n{output1}"

    print(
        "OK: render_overview synthetic values correct "
        "(package/version/sha256, 5/2/4/2/2/3/5/3/4/1), idempotent, "
        "AGENT:bluf marker intact, manifest loop expanded"
    )


def test_loop_value_with_literal_placeholder_renders_verbatim():
    """Regression guard: a value inserted during {{# manifest }} loop
    expansion is fully substituted against its OWN item, then must not be
    re-scanned by the top-level scalar pass. Before the fix, an agent-
    authored manifest `role` that happened to contain "{{ run.id }}" text
    got silently rewritten to the real run id by that second pass."""
    findings = make_findings()
    with open(TEMPLATE, encoding="utf-8") as f:
        template_text = f.read()

    findings["manifest"]["data/synthetic.json"] = {
        "role": "see {{ run.id }} here",
        "status": "raw",
    }

    output = render(findings, template_text)

    assert "see {{ run.id }} here" in output, (
        f"loop value containing a literal '{{{{ }}}}' token was rewritten "
        f"instead of rendering byte-for-byte:\n{output}"
    )
    # run.id ("run-2020-06-15") legitimately appears once, substituted into
    # the OVERVIEW header placeholder -- it must NOT appear a second time
    # from the loop value's literal text being re-substituted.
    assert output.count(findings["run"]["id"]) == 1, (
        "run.id substituted more than once -- the loop value's literal "
        "'{{ run.id }}' text was re-scanned by the top-level scalar pass"
    )

    print("OK: loop value with literal '{{ run.id }}' renders verbatim, not re-substituted")


if __name__ == "__main__":
    main()
    test_loop_value_with_literal_placeholder_renders_verbatim()
