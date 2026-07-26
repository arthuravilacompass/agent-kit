#!/usr/bin/env python3
"""selftest_check_relational_claims.py — synthetic fixture: 6 findings under
a neutral `com.example.app` root, deliberately not modeled on any real APK.
Exercises the relational-claim lexicon (a Portuguese and an English hit, plus
a clean miss), the manual-count pattern, anchor-sharing sibling grouping
(2 findings sharing one anchor, 1 standing alone), the source-tree checks
(a bare filename with a REAL collision vs. one with none, a missing file,
and a line range that exceeds the real file's length), and the
confidence/claim-form orthogonality the gate is built on (a cross-validated
finding carrying a false-shaped relational claim, and an observed finding
carrying none — confidence must not gate which one gets enumerated)."""
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(__file__))
from check_relational_claims import (  # noqa: E402
    check_anchors,
    find_manual_counts,
    find_relational_claims,
    group_siblings,
    index_source_tree,
    parse_findings,
)

FINDINGS_YAML = """\
- id: CT-01
  title: 'Widget -- roda a request num cliente HTTP compartilhado entre dois módulos'
  type: component
  anchor: 'HttpClient.java:10-20'
  origin: recovered
  confidence: cross-validated
  intent: needs-decision
  source_run: '2000-01-01'
  us: US-EXAMPLE-01
  notes: ''

- id: CT-02
  title: 'Outro componente que reusa the same cache instance across handlers'
  type: component
  anchor: 'HttpClient.java:22-30'
  origin: recovered
  confidence: observed
  intent: needs-decision
  source_run: '2000-01-01'
  us: US-EXAMPLE-01
  notes: ''

- id: CT-03
  title: 'Componente isolado, sem claim relacional nenhuma'
  type: component
  anchor: 'com/example/app/feature/StandaloneWidget.java:5-9'
  origin: recovered
  confidence: observed
  intent: needs-decision
  source_run: '2000-01-01'
  us: US-EXAMPLE-01
  notes: ''

- id: CT-04
  title: 'Dispatch table com 9 handlers mapeados'
  type: component
  anchor: 'com/example/app/core/Dispatcher.java:1-100'
  origin: recovered
  confidence: cross-validated
  intent: needs-decision
  source_run: '2000-01-01'
  us: US-EXAMPLE-01
  notes: ''

- id: CT-05
  title: 'Referencia um arquivo inexistente na árvore'
  type: component
  anchor: 'GhostClass.java:1-5'
  origin: recovered
  confidence: observed
  intent: needs-decision
  source_run: '2000-01-01'
  us: US-EXAMPLE-01
  notes: ''

- id: CT-06
  title: 'Range de linha maior que o arquivo real'
  type: component
  anchor: 'com/example/app/core/Dispatcher.java:1-9999'
  origin: recovered
  confidence: observed
  intent: needs-decision
  source_run: '2000-01-01'
  us: US-EXAMPLE-01
  notes: ''
"""


def write(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def main():
    with tempfile.TemporaryDirectory() as tmp:
        findings_path = os.path.join(tmp, "findings.yaml")
        write(findings_path, FINDINGS_YAML)

        entries = parse_findings(findings_path)
        assert len(entries) == 6, len(entries)

        # --- (a) relational claims: Portuguese + English hit, one clean miss ---
        relational = {eid: matches for eid, _conf, matches in find_relational_claims(entries)}
        assert "CT-01" in relational and "compartilhado" in relational["CT-01"], relational
        assert "CT-02" in relational and "reusa" in relational["CT-02"] and "same" in relational["CT-02"], relational
        assert "CT-03" not in relational, relational

        # --- confidence/claim-form orthogonality: both an observed and a
        # cross-validated finding carry claims; the enumerator must not filter
        # by confidence (that is the whole point of this gate) ---
        confidences = {eid: conf for eid, conf, _m in find_relational_claims(entries)}
        assert confidences["CT-01"] == "cross-validated", confidences
        assert confidences["CT-02"] == "observed", confidences

        # --- (c) manual counts ---
        counts = {eid: matches for eid, matches in find_manual_counts(entries)}
        assert "CT-04" in counts and any("9" in m for m in counts["CT-04"]), counts
        assert "CT-01" not in counts, counts

        # --- (d) sibling grouping: CT-01/CT-02 share HttpClient.java, CT-03 stands alone ---
        siblings = group_siblings(entries)
        assert "HttpClient.java" in siblings, siblings
        assert set(siblings["HttpClient.java"]) == {"CT-01", "CT-02"}, siblings
        assert not any("StandaloneWidget" in k for k in siblings), siblings

        # --- (b) anchors, without --source-tree: bare filenames reported unconfirmed ---
        # CT-06 deliberately carries a full-path anchor (tests line-range only, not
        # bareness) -- it must NOT show up here even without a source tree.
        bare, not_found, out_of_range, _logcat = check_anchors(entries, None)
        bare_ids = {eid for eid, _fname, _n in bare}
        assert {"CT-01", "CT-02", "CT-05"} <= bare_ids, bare_ids
        assert "CT-06" not in bare_ids, bare_ids
        assert not not_found and not out_of_range, (not_found, out_of_range)

        # --- (b) anchors, WITH a synthetic --source-tree ---
        tree = os.path.join(tmp, "sources")
        write(os.path.join(tree, "com/example/app/lib_a/HttpClient.java"), "// a\n" * 5)
        write(os.path.join(tree, "com/example/app/lib_b/HttpClient.java"), "// b\n" * 5)
        write(os.path.join(tree, "com/example/app/feature/StandaloneWidget.java"), "// s\n" * 5)
        write(os.path.join(tree, "com/example/app/core/Dispatcher.java"), "// d\n" * 50)
        index = index_source_tree(tree)

        bare2, not_found2, out_of_range2, _logcat2 = check_anchors(entries, index)
        # CT-01/CT-02: HttpClient.java exists twice -> CONFIRMED collision
        bare2_ids = {eid for eid, _fname, _n in bare2}
        assert bare2_ids == {"CT-01", "CT-02"}, bare2_ids
        for _eid, _fname, n in bare2:
            assert n == 2, bare2
        # CT-05: GhostClass.java doesn't exist -> not_found
        assert ("CT-05", "GhostClass.java") in not_found2, not_found2
        # CT-06: Dispatcher.java exists (50 lines) but claims line 9999 -> out_of_range
        assert any(eid == "CT-06" for eid, _ref, _claimed, _actual in out_of_range2), out_of_range2
        # CT-03/CT-04: full-path anchors, single match each -> never flagged as bare
        assert "CT-03" not in bare2_ids and "CT-04" not in bare2_ids, bare2_ids

    print(
        "OK: relational lexicon (pt+en) matched and confidence-blind, manual-count "
        "pattern matched, sibling grouping correct (2-member + isolated), bare-filename "
        "collision confirmed only with --source-tree evidence, missing file and "
        "out-of-range line both caught"
    )


if __name__ == "__main__":
    main()
