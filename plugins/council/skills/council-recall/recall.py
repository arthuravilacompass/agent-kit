#!/usr/bin/env python3
"""council-recall — retrieves cases that RHYME by DECISION-SHAPE.
Hard filter = posture. Strong signal = matching surface_class. Medium = keyword/topic
overlap. Recency only breaks ties. Top-3 above the threshold; silence if nothing
passes. Standard python3-guard idiom for advisory scripts. ALWAYS exit 0 (advisory)."""
import json, os, sys, argparse, re

SURFACE_STRONG = 3      # matching surface_class
KW_EACH = 1             # each keyword/topic-token in overlap
KW_CAP = 3              # medium-signal cap

def tokens(s):
    # \w is unicode-aware in py3 → preserves accented characters (e.g. pt-BR text
    # a user's own callouts/briefs may still contain, since output mirrors their language)
    return set(t for t in re.split(r"[^\w]+", (s or "").lower()) if len(t) > 2)

def load(posture, base):
    path = os.path.join(base, f"{posture}.jsonl")
    rows = []
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rows.append(json.loads(line))
                except Exception:
                    continue   # malformed JSON: skip it, never crash
    except FileNotFoundError:
        return []
    return rows

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--posture", required=True)
    ap.add_argument("--surface", default="other")
    ap.add_argument("--keywords", default="")
    ap.add_argument("--topic", default="")
    args = ap.parse_args()

    # NB: the "no python3" guard is BASH, in SKILL.md BEFORE invoking this script.
    # In here we're already in python3 — an internal guard would be dead code.
    base = os.path.join(os.path.expanduser("~"), ".claude", "epistemic")
    rows = load(args.posture, base)
    if not rows:
        sys.exit(0)   # silence: empty corpus

    superseded = {r.get("supersedes") for r in rows if r.get("supersedes")}
    rows = [r for r in rows if r.get("id") not in superseded]   # single-level dedup
    outcomes = {r["outcome_of"]: r.get("outcome", "") for r in rows if r.get("outcome_of")}  # D6
    rows = [r for r in rows if not r.get("outcome_of")]   # outcome briefs = annotation, not a case (D6)

    q_surface = args.surface
    q_tokens = set(k.strip().lower() for k in args.keywords.split(",") if k.strip()) | tokens(args.topic)

    try:                                  # advisory: an invalid env var must not crash (B10)
        threshold = int(os.environ.get("COUNCIL_RECALL_MIN", "3"))
    except (ValueError, TypeError):
        threshold = 3
    scored = []
    for r in rows:
        score = 0
        if r.get("surface_class") == q_surface:
            score += SURFACE_STRONG
        r_tokens = set(t.lower() for t in (r.get("keywords") or [])) | tokens(r.get("topic"))
        overlap = len(q_tokens & r_tokens)
        score += min(overlap * KW_EACH, KW_CAP)
        if score >= threshold:
            scored.append((score, int(r.get("ts") or 0), r))   # `or 0`: ts=null doesn't crash (B10)

    if not scored:
        sys.exit(0)   # silence: nothing rhymes above the threshold (never invents a case)

    # relevance dominates; recency (ts) only breaks ties
    scored.sort(key=lambda x: (x[0], x[1]), reverse=True)
    for score, ts, r in scored[:3]:
        ev = ";".join(r.get("evidence") or []) or "—"
        print(f"[{r.get('id')}] score={score} surface={r.get('surface_class')} "
              f"claim={r.get('claim_status')} mode={r.get('mode')}")
        print(f"    topic: {r.get('topic')}")
        print(f"    move:  {r.get('move')}")
        print(f"    evidence: {ev}")
        if r.get("id") in outcomes and outcomes[r["id"]]:   # D6: displays outcome, without ranking
            print(f"    outcome: {outcomes[r['id']]}")
    sys.exit(0)

if __name__ == "__main__":
    main()
