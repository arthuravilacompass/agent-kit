# Decision Ledger — record format

Reference for `core:spec-refine` step 5 (Gap Summary emission). Read together with
`core:grill-me`'s `pre-done` coverage clause (`REFERENCE.md`) and `core:pipeline`'s
append doctrine (§3 Stage notes) — both consume records in this format.

> Adapted from the Interview Ledger in ACT Lite (`CodeWithAndreaPro/agentic-coding-toolkit-lite`, MIT).

## Record

```md
### L3
Status: current | deferred | superseded(→L7)
Question: <the question that was actually asked>
Answer: <operator's answer, verbatim when short>
Decision: <the operational decision>
Source: operator-verbatim | recommendation-accepted | posture:<name> | inference
Negative requirements: <only when the answer forbids behavior>
```

- **`L#`** — sequential across the file, never reused.
- **`Status`** — `current` (in force) · `deferred` (accepted risk, not yet resolved) ·
  `superseded(→L#)` (replaced; the arrow names the record that replaced it).
- **`Question`** — the question actually asked, not a paraphrase.
- **`Answer`** — the operator's answer; verbatim when short enough to quote directly.
- **`Decision`** — the operational decision that follows from the answer. One decision
  per record.
- **`Source`** — see below.
- **`Negative requirements`** — omit the field entirely unless the answer forbids a
  behavior (e.g. "never do X"). Do not write "N/A" or leave it empty.

## Source semantics

| Source | Meaning | Reopens |
|---|---|---|
| `operator-verbatim` | The operator's own words, unprompted or directly quoted. | Hardest — revisit only on new operator input. |
| `recommendation-accepted` | An assistant proposal the operator approved (a "sim"/"ok", or a pick from `AskUserQuestion`). | Easier — the operator endorsed a framing, he didn't author it. |
| `posture:<name>` | A verdict from a Council posture (e.g. `posture:bohr`). | Reopens on a fresh posture run or contradicting evidence. |
| `inference` | Assistant judgment folded into the decision, never individually confirmed by the operator. | Easiest — treat as provisional until confirmed. |

`Source` states how the decision was reached, not how confident it is. A future
session or reviewer reading `Source` alone knows whether to treat the record as
settled or as still open for renegotiation — this is the field that distinguishes
an operator's own call from an assistant recommendation that merely went
unchallenged.

## Append-only rule

Never edit a record's `Decision` in place. A changed decision appends a new `L#`
record and marks the old record `superseded(→L#)`, pointing at the new one. The
ledger is a log, not a mutable table — the same discipline as the Council log
(`~/.claude/epistemic/*.jsonl`).

## Storage

One file per work unit, beside the artifact it serves:

```
docs/superpowers/specs/<date>-<slug>-ledger.md
```

(or the consumer project's own spec directory, same convention). Lifetime = the
delivery's, not global state. Do not create a repo-wide or session-wide ledger
file.

## Example

```md
### L2
Status: current
Question: Which points emit L# records in v1?
Answer: picked "Só spec-refine emite (Recommended)" via AskUserQuestion
Decision: Only spec-refine emits; other decision points get one append-doctrine line in pipeline.
Source: recommendation-accepted
```
