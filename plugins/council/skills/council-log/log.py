#!/usr/bin/env python3
"""council-log — validates and appends ONE brief to the episodic corpus (append-only, flock).
Reads a JSON object (the brief) on stdin. Rejects (exit!=0, corpus untouched) an
invalid brief. Advisory: never touches code nor blocks a commit."""
import json, os, sys, time, fcntl, re

ROSTER = {"bohr", "schrodinger", "epicurus", "sagan", "maxwell", "zeno"}
SURFACE = {"repository","datasource","dto","mapper","coordinator","router",
           "entity","state","store","controller","other"}
CLAIM = {"APOSTA", "FATO"}
MODE = {"light", "escalated"}
MOVE_MAX = 800

def fail(msg):
    sys.stderr.write(f"council-log: REJECTED — {msg}\n")
    sys.exit(1)

def main():
    raw = sys.stdin.read()
    try:
        b = json.loads(raw)
    except Exception as e:
        fail(f"invalid JSON: {e}")
    if not isinstance(b, dict):
        fail("brief is not a JSON object")
    posture = b.get("posture")
    if posture not in ROSTER:
        fail(f"posture missing/invalid (roster-6): {posture!r}")
    if b.get("claim_status") not in CLAIM:
        fail("claim_status required ∈ {APOSTA, FATO}")
    if b.get("mode") not in MODE:
        fail("mode required ∈ {light, escalated}")
    if b.get("surface_class") not in SURFACE:
        fail(f"surface_class required ∈ {sorted(SURFACE)}")
    for f in ("topic", "move"):
        if not isinstance(b.get(f), str) or not b[f].strip():
            fail(f"required field missing/empty: {f}")
    if b["claim_status"] == "FATO":
        ev = b.get("evidence")
        if not isinstance(ev, list) or len(ev) < 1:
            fail("claim_status=FATO requires >=1 entry in evidence")
    for opt in ("outcome", "outcome_of"):                 # D6: optional outcome (stores, doesn't rank)
        if opt in b and (not isinstance(b[opt], str) or not b[opt].strip()):
            fail(f"invalid optional field (needs a non-empty str): {opt}")

    ts = int(b.get("ts") or time.time())
    b["ts"] = ts
    slug = re.sub(r"[^a-z0-9]+", "-", b["topic"].lower()).strip("-")[:40] or "x"
    b["id"] = b.get("id") or f"{posture}-{slug}-{ts}"

    base = os.path.join(os.path.expanduser("~"), ".claude", "epistemic")
    blobs = os.path.join(base, "blobs")
    try:
        os.makedirs(blobs, exist_ok=True)
    except Exception as e:
        fail(f"couldn't create corpus directory: {e}")

    # overflow: verbatim move > MOVE_MAX goes to the blob (written UNDER THE SAME
    # flock as the line — advisor fix: a blob outside the lock could be overwritten
    # by a colliding id)
    overflow = len(b["move"]) > MOVE_MAX
    full_move = b["move"]
    if overflow:
        b["move_blob"] = f"blobs/{b['id']}.txt"
        b["move"] = b["move"][:MOVE_MAX]

    target = os.path.join(base, f"{posture}.jsonl")
    line = json.dumps(b, ensure_ascii=False) + "\n"
    try:
        with open(target, "a", encoding="utf-8") as f:
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)   # serializes concurrent appends AND blob writes
            try:
                if overflow:                          # blob under the same lock as the line
                    with open(os.path.join(blobs, f"{b['id']}.txt"), "w", encoding="utf-8") as bf:
                        bf.write(full_move)
                f.write(line)
                f.flush()
            finally:
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)
    except Exception as e:
        fail(f"append failed: {e}")
    print(b["id"])
    sys.exit(0)

if __name__ == "__main__":
    main()
