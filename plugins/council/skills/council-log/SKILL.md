---
name: council-log
description: Invoke after running a Council posture (council:schrodinger/bohr/epicurus/sagan or agents maxwell/zeno) on a high-cost-to-reverse decision worth remembering — logs the brief to the episodic corpus (~/.claude/epistemic/<posture>.jsonl, append-only). Advisory; never blocks.
---

# /council:council-log — log a deliberation

Persists ONE brief (append-only, under flock). Decides nothing; it's recall infrastructure.

Assemble the brief's JSON object and append it:
```bash
echo '{"posture":"<bohr|schrodinger|epicurus|sagan|maxwell|zeno>","topic":"<1 line>","move":"<the posture's verbatim output>","claim_status":"APOSTA|FATO","mode":"light|escalated","surface_class":"<repository|...|other>","keywords":["..."],"evidence":["file:line"]}' \
  | python3 "${CLAUDE_PLUGIN_ROOT}/skills/council-log/log.py"
```

Rules:
- `claim_status=FATO` **requires** `evidence` (≥1 `file:line`/`doc:section`) — otherwise the script refuses (deliberate asymmetry: a wrong FATO in recall is more damaging than a wrong APOSTA).
- `move` > 800 chars goes to `blobs/<id>.txt`; the JSONL stores the truncated version + `move_blob`.
- Correction = a NEW brief with `supersedes:"<old-id>"` (ONE level; never edit/delete a line).
- **Outcome:** to record how a case ended, log a NEW brief with `outcome:"<what happened>"` + `outcome_of:"<original-brief-id>"` (append-only; never edits the original line). `recall` displays the outcome on the original case but **does not rank by it** (the corpus stays "cases that happened"; you judge).
