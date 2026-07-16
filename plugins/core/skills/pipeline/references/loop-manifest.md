# Loop manifest — convention

A **loop manifest** is the explicit state of one unit of substantial work. Instances live at `docs/superpowers/loops/<slug>.md`, **one file per work unit, never global** (same rule as `../../spec-refine/references/ledger-format.md` §Storage — lifetime is the delivery's, not session- or repo-wide state). Like specs and plans, instances are consumer-side gitignored state; this file is the shipped format they follow.

## Why it is not "your own state marker"

`pipeline` §5 forbids ad-hoc state files because progress already lives in artifacts (specs/plans/handoffs) and `git`. The manifest does **not** replace that. **Live detection (pipeline §1, from artifacts + git) is authoritative for the stage.** The manifest only carries what artifacts do not: which roles are active, what is delegated, what is pending, the review mode. Its `stage` field is a **non-authoritative echo** for the human reader — on any conflict, live detection wins, so a stale manifest degrades gracefully and never lies about where the work is.

This subordination is the whole safety argument. It is why a per-work-unit manifest is sanctioned where the reverted global "hat" file (CHANGELOG, core 0.8.0) was not: that file was global, hand-edited, low-frequency, and *authoritative* — three failure modes this convention avoids.

## Lifecycle

- **Origin:** the Orchestrator creates it when a multi-stage route begins (first stage that produces a durable artifact).
- **Writer:** the Orchestrator updates it as part of **closing a stage** (`pipeline` §5 already governs stage-close), never by hook.
- **Discard:** at Capture (`pipeline` §5 "Closing always captures").

## Schema

```
# Loop: <slug>
stage:      <echo of live detection — NON-authoritative, human convenience only>
roles:      <active roles this session, e.g. orchestrator, worker×2>
delegated:  <what is out to a worker, or —>
pending:    <what blocks advancing, or —>
mode:       <route class: feature | bug | investigation | refactor | external-spec>
```

## Documented failure mode

Staleness: the manifest can lag the real state. Mitigated by being short-lived, one-per-unit, and **subordinate** to pipeline §1's live detection (above) — so a stale manifest is corrected on the next docking, not trusted over evidence.
