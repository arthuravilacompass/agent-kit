---
name: review-remote
description: Invoke to review code without depending on external plugins — pre-push of your own work (Flow A) or review of someone else's PR via `--branch` (Flow B), with scope comparison against a ticket via `--ticket`. Sequential, plugin-free.
disable-model-invocation: true
---

# review-remote — Code Review (plugin-free, sequential)

> **Which to use**: this skill is plugin-free and sequential. With the `pr-review-toolkit` plugin active, prefer `core:review-local` (parallel). **Divergence**: `core:review-local` BLOCKS on analyze-fail; this one reports it as a finding and continues.

Code review for the team, with no dependency on external plugins.

## Project config

This skill assumes the consumer project defines:
- **Default base branch** (fallback if `--base` isn't passed; e.g., `main`).
- **Lint command** and **test command** (Flow A, Step 2).
- **Layer 1 checklist** — universal review items always applied (config: quantity and content depend on the project; e.g. a `CHECKLIST.md` file from the project's own code-review skill).
- **Layer 2 checklist** — contextual triggers (UI, state management, lists, i18n, images, animations, navigation) and the skill that applies them.
- **Stack-specific state-management/architecture rules** (Step 5), if the project uses a framework with its own patterns (e.g. a reactive-state lib with mutation conventions).
- **Comment prefixes and output destination** (Flow B Step 8) — e.g. `blocker:`/`non-blocker:` for Bitbucket, or GitHub's native review format.

Without these configs, the skill still runs the Steps structure below, just without the stack-specific checklists.

## Usage

```
review-remote                                             # Flow A: pre-push of your own work
review-remote --base <branch>                             # Flow A with an explicit base
review-remote --branch feat/<something>                    # Flow B: review someone else's PR
review-remote --branch feat/<something> --base <base>       # Flow B with a different base
review-remote --branch feat/<something> --ticket <TICKET>    # Flow B + scope comparison with a ticket
```

Parameters:
- `--branch` — the PR's remote branch; without this flag = Flow A (pre-push)
- `--base` — the diff's base branch (default: config above)
- `--ticket` — ticket identifier for scope comparison (only with `--branch`)

---

## Step 0 — Detect mode

Parse `$ARGUMENTS`:
- `--branch` present → **Flow B** (go to the Flow B section below)
- `--branch` absent → **Flow A** (continue below)

---

## Flow A — Pre-push (no `--branch`)

### Step 1 — Resolve scope

```bash
git diff origin/<base>...HEAD --stat
```

If the output is empty: stop. Report "No changes relative to `origin/<base>`."

Show the `--stat` output so the author confirms scope before proceeding.

### Step 2 — Precondition

Run the project's lint command and test command in sequence (config).

Report the results (errors, warnings, test failures). **Do not block** — failures become review findings, they don't stop the flow.

### Step 3 — Layer 1

Get the full diff: `git diff origin/<base>...HEAD`

Apply the project's Layer 1 checklist (config) against all changed files. Document each violation found with file path and line number.

### Step 4 — Layer 2

Check for contextual triggers present in the diff (config — typical examples): UI/components, state-management reactions, lists/collections, i18n/l10n (new strings, formatting), network images, animations, navigation. For each true trigger, invoke the project's code-review skill configured for that dimension.

### Step 5 — Stack rules (if applicable)

For each state/controller file present in the diff, read the project's stack-specific quality rules (config) — both the always-applied codes and the aspirational ones.

### Step 6 — Aggregate

**Mandatory Verification Discipline:** before including any finding in the report, re-read the file's exact lines. Discard findings for problems already fixed.

Consolidate all findings, grouped by severity (config: the project's severity names/prefixes — e.g. `blocker:` / `non-blocker:`). Output mirrors the user's language, default English.

Finding format: `<prefix>: CODE — description (File.ext:line)`

### Step 7 — Close

Present the report and ask: **"How should I proceed?"**

The author decides the next steps: fix before pushing, suppress with justification, or create a follow-up ticket.

---

## Flow B — Remote PR (with `--branch`)

### Step 1 — Resolve scope

Check whether `origin/<branch>` is already available locally:
```bash
git branch -r | grep "origin/<branch>"
```

If not found:
```bash
git fetch origin <branch>
```

Compute and show the diff:
```bash
git diff origin/<base>...origin/<branch> --stat
```

If empty: stop. Report "Branch `<branch>` has no changes relative to `<base>`."

### Step 2 — (no precondition)

The reviewer doesn't check out the branch. Lint and tests are the branch's CI's responsibility.

### Step 3 — Layer 1

Get the diff: `git diff origin/<base>...origin/<branch>`

Apply the project's Layer 1 checklist (config). Document violations with file path and line.

### Step 4 — Layer 2

Same triggers as Flow A. Invoke the project's code-review skill for each true trigger in the diff.

### Step 5 — Stack rules (if applicable)

For each state/controller file in the diff, read the project's stack-specific quality rules (config).

### Step 6 — Ticket (if `--ticket` provided)

Compare the ticket's acceptance criteria against the diff's actual scope. Point out divergences:
- Functionality requested in the ticket that doesn't appear in the diff
- Changes in the diff that weren't requested in the ticket

### Step 7 — Aggregate

**Mandatory Verification Discipline:** re-read each finding's file:line before including it.

Exclude findings marked 🟣 pre-existing — not this PR's responsibility.

### Step 8 — Output

Produce a copy-pasteable block in the configured destination's format (config — e.g. Bitbucket, GitHub review comment). **Do not ask "how should I proceed"** — the reviewer doesn't edit code.

```
=== Comments for PR <branch> ===

blocker: CODE — problem description (File.ext:line)
blocker: CODE — description (File.ext:line, :line2)

non-blocker: CODE — suggestion (File.ext:line)
```

Text language: mirrors the user's language, default English. Rule codes: in whatever format the project already uses.
