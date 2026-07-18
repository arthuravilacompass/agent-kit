#!/usr/bin/env python3
# desc: gate for render_c4.py — synthetic fixture, bridge-cap numbers, idempotency, AGENT passthrough
"""selftest_render_c4.py — gate for render_c4.py.

Builds a minimal synthetic findings.json carrying only the field
c4.template.mmd actually substitutes (metrics.bridge_capabilities.value/
.domains -- values chosen here, nothing copied from a real run) and renders
it against the REAL c4.template.mmd. Asserts:

  1. The bridge-capability numbers (value + domains) appear in the rendered
     bridge label.
  2. Idempotency: rendering twice from the same inputs is byte-identical.
  3. The AGENT:START/END annotations marker survives untouched.
  4. No unrendered {{ }} placeholder syntax leaks into the output.

Pure stdlib. Exit 0 on pass, non-zero with a clear message on fail.
"""
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(__file__))
from render_c4 import render  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(HERE, "..", "references", "c4.template.mmd")


def make_findings():
    return {
        "metrics": {
            "bridge_capabilities": {"value": 8, "domains": 3, "note": "synthetic"},
        },
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

        # The bridge label must carry the synthetic numbers, substituted.
        assert "JS bridge -- 8 caps in 3 domains" in output1, (
            f"bridge label not correctly substituted (want value=8, domains=3):\n{output1}"
        )

        # AGENT:START/END marker must survive verbatim.
        assert "%% AGENT:START annotations" in output1, "AGENT:START annotations marker did not survive"
        assert "%% AGENT:END annotations" in output1, "AGENT:END annotations marker did not survive"
        assert "Add app-specific engineering interpretation here" in output1, (
            "AGENT block instructional placeholder text did not survive"
        )

        # No leftover template syntax anywhere in the rendered output.
        assert "{{" not in output1, f"unrendered placeholder leaked into output:\n{output1}"

    print(
        "OK: render_c4 synthetic bridge label correct (8 caps / 3 domains), "
        "idempotent, AGENT:annotations marker intact"
    )


if __name__ == "__main__":
    main()
