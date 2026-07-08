---
name: compound
description: Invoke at the end of a relevant work track — generates the session's structured handoff (state, decisions, next steps) that survives /clear and feeds resumption via plan-autoload.
disable-model-invocation: true
---

# compound — Structural Write-back at Track End

Final gate for any non-trivial track. Ensures what the session learned doesn't evaporate: typed memory, handoff if needed, and graduation candidacy. Doesn't create a parallel store — writes to mechanisms that already exist (typed memory + `docs/superpowers/handoffs/` + `docs/graduation-log.md`).

## Usage

```
compound            # full sweep
compound --quick    # short session: only question 1, no sweep
```

## Steps

1. **Learning capture** — invoke the `core:learn` skill (scans the conversation for corrections, preferences, decisions; inline approval before writing). If nothing is found, state explicitly: *"Nothing to capture this session"* — the statement itself is the fast path, no ceremony.

2. **Handoff (conditional)** — if the session is heavy (context-monitor warning ≥800KB) OR work continues in another session: write `docs/superpowers/handoffs/<YYYY-MM-DD>-<task>.md` with: task, decisions made, next steps, files touched. `plan-autoload` resurfaces it next session. If the track truly ended (PR created), skip.

3. **Graduation candidate (conditional)** — if the session refined a toolkit rule/skill/hook: check the 3 criteria in `docs/graduation-log.md` (recurs ≥2× · stabilized in real use · not specific to a single project). If all 3 hold, **propose** the row for the append-only table — the toolkit owner decides; never add without approval.

4. **Smell log (informational)** — if `docs/engineering/smell-log.txt` gained entries this session, mention it in the summary: which code(s) fired and where. Recurrence of a code is a signal to refine the corresponding rule.

5. **4-line summary** — memories saved/skipped · handoff written (or n/a) · graduation proposed (or n/a) · smells blocked (or n/a).

## Important

- **`--quick` mode**: only step 1, and the `core:learn` skill limited to the last ~20 messages.
- **Approval required** for any memory write (inherited from `core:learn`) and for a graduation-log row.
- Bugfix the harness let through: besides the memory, add a case to `docs/evals/` (see the README there) — closed bugs are evals being born.
- Don't duplicate: if the learning is already in memory/a rule, update instead of creating.
