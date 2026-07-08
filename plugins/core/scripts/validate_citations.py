#!/usr/bin/env python3
# desc: Validates finding citations against the session's read-ledger (Layer 1).
"""
validate_citations.py — Deterministic citation validator (Layer 1).

Cross-checks a subagent's findings (each with evidence.file:lineStart-lineEnd) against the
session's read-ledger (what was ACTUALLY read via Read/Grep, recorded by the read-ledger.sh
hook). A tool-output finding whose range doesn't overlap any read → UNVERIFIED. Mechanism,
not instruction: you can't cite code you didn't read.

Verdicts:
  verified     — tool-output claim whose range overlaps a read in the ledger.
  unverified   — tool-output claim with no evidence, or whose range wasn't read this session.
  passthrough  — epistemicSource inference/absence/external: doesn't require citation (annotated, not blocked).

Usage:
  # annotate (default, exit 0): findings via stdin or --findings, ledger auto-discovered
  python3 validate_citations.py --findings findings.json
  cat findings.json | python3 validate_citations.py --session <id> --json

  # hard gate (exit 2 if any unverified) — for bug-report finalization
  python3 validate_citations.py --findings bug_report.json --gate

Input (stdin or --findings): JSON array of findings, OR object {"findings": [...]}.
Each finding: { "claim": "...", "epistemicSource": "tool-output",
                "evidence": {"file": "...", "lineStart": N, "lineEnd": M} }

Ledger: <state-dir>/read-ledger-<session>.jsonl (default: the most recent).
Default <state-dir>: $CLAUDE_PLUGIN_DATA/state if the env var is set (same convention
as the read-ledger.sh hook); otherwise $TMPDIR/agent-kit-core/state. Always
overridable via --state-dir.
"""

import argparse
import glob
import json
import os
import sys

NO_CITATION_SOURCES = {"inference", "absence", "external"}


def default_state_dir():
    base = os.environ.get("CLAUDE_PLUGIN_DATA") or os.path.join(
        os.environ.get("TMPDIR", "/tmp"), "agent-kit-core"
    )
    return os.path.join(base, "state")


# ── Ledger ────────────────────────────────────────────────────────────────────
def discover_ledger(session, ledger_path, state_dir):
    if ledger_path:
        return ledger_path
    if session:
        return os.path.join(state_dir, f"read-ledger-{session}.jsonl")
    candidates = glob.glob(os.path.join(state_dir, "read-ledger-*.jsonl"))
    if not candidates:
        return None
    # Concurrent sessions produce parallel ledgers — auto-discovery may grab the wrong one.
    import time as _t
    recent = [c for c in candidates if _t.time() - os.path.getmtime(c) < 600]
    if len(recent) > 1:
        print(f"WARNING: {len(recent)} ledgers modified <10min ago (concurrent sessions?). "
              "Pass --session for precision; using the most recent.", file=sys.stderr)
    return max(candidates, key=os.path.getmtime)


def load_ledger(path, project_dir):
    """Returns (ranges_by_file, touched_files). Ignores 0-0 ranges for line overlap
    (file seen but range unknown), but still records the file as touched."""
    ranges = {}
    touched = set()
    if not path or not os.path.isfile(path):
        return ranges, touched
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                e = json.loads(line)
            except Exception:
                continue
            fp = normpath(e.get("file", ""), project_dir)
            if not fp:
                continue
            touched.add(fp)
            s, en = e.get("start"), e.get("end")
            if isinstance(s, int) and isinstance(en, int) and en > 0:
                lo, hi = (s, en) if s <= en else (en, s)
                ranges.setdefault(fp, []).append((lo, hi))
    return ranges, touched


def normpath(p, project_dir):
    if not p:
        return ""
    if not os.path.isabs(p):
        p = os.path.join(project_dir, p)
    return os.path.normpath(p)


def overlaps(a_lo, a_hi, b_lo, b_hi):
    return a_lo <= b_hi and b_lo <= a_hi


# ── Validation ──────────────────────────────────────────────────────────────
def validate_finding(finding, ranges, touched, project_dir):
    src = (finding.get("epistemicSource") or "tool-output").lower()
    if src in NO_CITATION_SOURCES:
        return "passthrough", f"epistemicSource={src} — doesn't require citation"

    ev = finding.get("evidence") or {}
    file = ev.get("file", "")
    ls = ev.get("lineStart")
    le = ev.get("lineEnd", ls)
    if not file or not isinstance(ls, int):
        return "unverified", "tool-output claim with no evidence.file:lineStart"

    if not isinstance(le, int):
        le = ls
    lo, hi = (ls, le) if ls <= le else (le, ls)
    fp = normpath(file, project_dir)

    for (rlo, rhi) in ranges.get(fp, []):
        if overlaps(lo, hi, rlo, rhi):
            return "verified", f"range {lo}-{hi} overlaps read {rlo}-{rhi} in the ledger"
    if fp in touched:
        return "unverified", f"file read, but range {lo}-{hi} is outside what was read"
    return "unverified", "file/range never read this session (possible fabrication)"


def load_findings(path):
    raw = open(path, encoding="utf-8").read() if path else sys.stdin.read()
    data = json.loads(raw)
    if isinstance(data, dict) and "findings" in data:
        return data["findings"]
    if isinstance(data, list):
        return data
    raise ValueError("input must be an array of findings or {\"findings\": [...]}")


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    ap = argparse.ArgumentParser(description="Deterministic citation validator (Layer 1).")
    ap.add_argument("--findings", help="JSON findings file (default: stdin)")
    ap.add_argument("--session", help="session id (derives the ledger path)")
    ap.add_argument("--ledger", help="explicit path to the ledger .jsonl")
    ap.add_argument("--state-dir", default=default_state_dir(),
                    help="directory where read-ledger.sh writes the ledgers (default: "
                         "$CLAUDE_PLUGIN_DATA/state or $TMPDIR/agent-kit-core/state)")
    ap.add_argument("--project-dir", default=os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd()),
                    help="project root for resolving relative paths")
    ap.add_argument("--gate", action="store_true",
                    help="hard gate: exit 2 if any finding is unverified (for bug-report)")
    ap.add_argument("--json", action="store_true", help="emit annotated findings as JSON on stdout")
    args = ap.parse_args()

    project_dir = os.path.normpath(args.project_dir)
    ledger_path = discover_ledger(args.session, args.ledger, args.state_dir)
    ranges, touched = load_ledger(ledger_path, project_dir)

    try:
        findings = load_findings(args.findings)
    except Exception as e:
        print(f"error reading findings: {e}", file=sys.stderr)
        sys.exit(1)

    annotated = []
    counts = {"verified": 0, "unverified": 0, "passthrough": 0}
    for fnd in findings:
        verdict, reason = validate_finding(fnd, ranges, touched, project_dir)
        counts[verdict] += 1
        annotated.append({**fnd, "_verdict": verdict, "_reason": reason})

    if args.json:
        print(json.dumps(annotated, ensure_ascii=False, indent=2))
    else:
        led = ledger_path or "(no ledger found)"
        print(f"ledger: {led}")
        print(f"findings: {len(findings)} · ✅ {counts['verified']} verified · "
              f"❌ {counts['unverified']} unverified · ⏭ {counts['passthrough']} passthrough\n")
        for a in annotated:
            mark = {"verified": "✅", "unverified": "❌", "passthrough": "⏭"}[a["_verdict"]]
            claim = (a.get("claim") or "")[:70]
            print(f"  {mark} {a['_verdict'].upper():11} {claim}\n     ↳ {a['_reason']}")

    if args.gate and counts["unverified"] > 0:
        print(f"\nGATE: {counts['unverified']} finding(s) UNVERIFIED — blocked.", file=sys.stderr)
        sys.exit(2)
    sys.exit(0)


if __name__ == "__main__":
    main()
