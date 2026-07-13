# Kit operations

Scope: operations for whoever maintains and publishes this kit (the owner). Day-to-day installation and use (local marketplace) are in `README.md` — this document covers publishing and distribution (including the consumer side of the GitHub route, which only exists once the owner publishes), permissions, and the gate.

---

## 1. Publishing to GitHub

Owner side, run from `$HOME/dev/agent-kit`:

```bash
git remote add origin git@github.com:<username>/agent-kit.git
git push -u origin main --tags
```

**Mandatory placeholder.** `<username>` is literal — never replace it with a real account name in this file or anywhere else in the repo. `scripts/check-provenance.sh` keeps a denylist that matches account names by substring; a real name here turns the provenance gate red.

Consumer side: swap the local marketplace for an `extraKnownMarketplaces` entry pointing at GitHub, in `settings.json` (project or user):

```json
{
  "extraKnownMarketplaces": {
    "agent-kit": {
      "source": { "source": "github", "repo": "<username>/agent-kit" }
    }
  }
}
```

```bash
claude plugin marketplace add <username>/agent-kit
claude plugin install core@agent-kit
claude plugin install council@agent-kit   # recommended with core
claude plugin install team@agent-kit      # optional: refinement/squad ceremonies
claude plugin install mobile@agent-kit    # only in a Flutter/Dart project
```

There's no mechanical warning hook for this dependency — the SessionStart `require-core.sh` check that used to run in `team`/`council`/`mobile` has been retired. `core` works standalone; installing `council`/`team`/`mobile` alongside it is a prose recommendation only, nothing enforces or measures the pairing at runtime.

The local marketplace (`claude plugin marketplace add "$HOME/dev/agent-kit"`) keeps working as the development path even after the remote is published — the source is edited at `$HOME/dev/agent-kit`; GitHub is the distribution channel, not the place to edit.

Consumer update flow after a new commit to the kit: `claude plugin update core@agent-kit` (and/or `council@agent-kit`, `team@agent-kit`, `mobile@agent-kit`), followed by a session restart — without the restart the update isn't applied.

---

## 2. Composition with the harness's permission mode

The user's `settings.json` permission mode (`defaultMode`, sandbox) owns the approval decision for tool calls, including Bash commands. `core` used to add a narrow Bash-only auto-approve refiner in front of it (`bash-autoapprove-readonly.sh`); it was demoted to `unwired/` in the operator prune (vertical-evolution refactor — §5): a permission convenience, not an epistemic verifier, and its known comment-newline fail-open closes by removal. There's currently no such refining layer in `core` — the harness's permission mode is the only one.

---

## 3. Double-loading note

If this marketplace is installed inside a workspace that already has its own committed copy of equivalent skills/rules (e.g., a monorepo with its own `.claude/skills/`), both sources coexist — Claude Code loads both. Benign coexistence: there's no name conflict, guaranteed because the plugin uses a namespace (`core:`/`council:`/`team:`/`mobile:`); the cost is duplicated context, not incorrect behavior. That's not a reason to skip installing — it's a cost to weigh when deciding whether to keep both sources or migrate the workspace to consume only the plugin.

---

## 4. Quality gate

Five commands, all must come back green before any commit:

```bash
./scripts/check-provenance.sh
claude plugin validate .
./evals/run-evals.sh
python3 scripts/generate_inventory.py --check
./scripts/check-ceiling.sh
```

- `check-provenance.sh` — denylist of company/product/board names and internal paths, run over the whole repo (including `unwired/`, no exception).
- `claude plugin validate .` — validates the marketplace manifest and each plugin's manifest.
- `run-evals.sh` — deterministic Tier 1: runs the real hooks against synthetic payloads. Runs via heredoc; in environments that sandbox temp-file creation (some agent harnesses), run with the sandbox disabled for this specific command.
- `generate_inventory.py --check` — `INVENTORY.md` is generated, never hand-edited; this command fails (red gate) if the repo tree diverges from the recorded inventory. Regenerate with `python3 scripts/generate_inventory.py` and commit the result.
- `check-ceiling.sh` — measures `session-start.sh`'s real output against the always-on tier's byte ceiling, and bans "Promoted from" provenance narration inside `plugins/`. Ceiling and rationale: `docs/GOVERNANCE.md`.

Normative convention behind the inventory: the `# desc:` line (line 2 of every hook/script under `plugins/*/hooks` and `plugins/*/scripts`) is the source of the description shown in `INVENTORY.md`. Any prose header already in the file is free commentary, with no effect on the inventory. When the two diverge, fix the `# desc:` line — not the prose header.

Surface docs (README, this file, and `docs/GOVERNANCE.md`) don't carry dates — history lives in `CHANGELOG.md`. Check: `grep -q` for a year-month pattern (`YYYY-`) over the file must fail to match. Note: `grep -c` exits with code 1 when there's no match — don't use `-c` as a chained pass condition in `&&`.

---

## 5. unwired/ — raw material without proven use

`unwired/` isn't a plugin: nothing there is loaded by Claude Code — zero context cost. It's genericized material from originating projects, scrutinized enough to serve as reference, but without proven real use in this kit. Lifecycle (3-state model, promotion rule, always-on ceiling, conventions): `docs/GOVERNANCE.md`.

| Item | Origin | Why it isn't wired |
|---|---|---|
| `ui-comparison/` | Visual-fidelity skill from an originating project | The method (phases, scoring rubric) is generic; without a real design system to test against, there was no way to prove use here. `figma-to-component`, which lived in this same pair, was promoted — see `plugins/mobile/skills/figma-to-component/` and the record in `CHANGELOG.md`. |
| `handoff-gate/` | Stop hook that closes the context-monitor's alert→action loop | Deleted during extraction as an orphan ("dead weight that looks alive"); rescued in post-build review — the blind census evaluated the mechanism's merit independently, and with the originating project's clone gone, deleting it meant permanent loss (recorded in the header of `unwired/handoff-gate/handoff-gate.sh`). The criterion doesn't change: it only gets promoted with real use; the script's header lists the rewiring checklist. |
| `WORKFLOW.md` | An operator's manual from an originating project | Genericized (skill names mapped to this kit's vocabulary where an equivalent exists; gaps flagged). Reference/inspiration for the README, not a document Claude Code loads. |
| `conflict_triage.py` | Former `core` script, triaged merge conflicts between a base branch and feature/team branches | Demoted in the Phase 2 refactor: zero consumers found (grep across skills/hooks/docs). |
| `prune_branches.sh` | Former `core` script, listed remote-branch deletion candidates for manual review (never deletes) | Demoted in the Phase 2 refactor: zero consumers found (grep across skills/hooks/docs). |
| `check_merged_imports.py` | Former `mobile` script, checked internal Dart import resolution in a merged git tree without checkout | Demoted in the Phase 2 refactor: zero consumers found (grep). |
| `swap_pubspec.py` | Former `mobile` script, swapped `pubspec.yaml` git-ref dependencies for local path dependencies and back | Demoted in the Phase 2 refactor: zero consumers found (grep). Of the original 5 `mobile` scripts, only `check_merged_imports.py` and this one remain unwired — see `plugins/mobile/scripts/` for the rest (`export_network_logs.py`, `arch_graph.sh`, `arch_violations.py`). |
| `scope-inject.sh` | Former `core` PreToolUse(`Edit\|Write\|MultiEdit`) hook — injected a scope pointer when the edited file matched a project's `.claude/knowledge-map.tsv` | Cut from `plugins/core/hooks/hooks.json` in the Phase 2 refactor, along with its eval cases and fixtures. |
| `context-monitor.sh` | Former `core` PostToolUse(`Bash`) hook — warned when the session transcript grew past a size threshold | Cut from `plugins/core/hooks/hooks.json` in the Phase 2 refactor, along with its eval cases and fixtures. Its loop-partner `handoff-gate/` (above) was already here. |
| `skills/bug-report/` | Former `core` slash-only skill — investigated a bug and gated the final report on a verified-citation mechanism (read-ledger + `validate_citations.py --gate`) | Operator prune (vertical-evolution refactor): its mechanism, the standalone citation gate, was re-scoped to grill-me-internal infrastructure; the skill itself is superseded. |
| `skills/compound/` | Former `core` slash-only skill — end-of-track session handoff: learning capture, resumable handoff doc, graduation candidacy | Operator prune (vertical-evolution refactor): vertical identity — session-handoff prose, not a verifier. |
| `hooks/plan-autoload.sh` | Former `core` SessionStart hook — injected a resume pointer when a recent plan (<72h) existed, feeding `compound`'s handoff | Operator prune (vertical-evolution refactor): pair of `compound` — resume-pointer injector. |
| `hooks/bash-autoapprove-readonly.sh` | Former `core` PreToolUse(`Bash`) hook — auto-approved commands recognized as safe reads, deferring on any ambiguity | Operator prune (vertical-evolution refactor): permission convenience, not a verifier; known comment-newline fail-open closed by removal. |
| `hooks/claude-dir-guard.sh` | Former `core` PreToolUse(`Bash`) hook — blocked `rm` commands touching a `.claude` path segment | Operator prune (vertical-evolution refactor): rm-guard, not a verifier; known substring false-positive/bypass closed by removal. |
| `hooks/dart-auto-format.sh` | Former `mobile` PostToolUse(`Edit\|Write\|MultiEdit`) hook — ran `dart format` on the edited file | Operator prune (vertical-evolution refactor): formatting convenience, not a verifier. |
| `hooks/dart-analyze-file.sh` | Former `mobile` PostToolUse(`Edit\|Write\|MultiEdit`) hook — ran `dart analyze` scoped to the file, feedback always advisory | Operator prune (vertical-evolution refactor): advisory analyze, not a verifier. |
| `hooks/package-feedback.sh` | Former `mobile` PostToolUse(`Edit\|Write`) hook — background `pub get` for an edited `pubspec.yaml`; test reminder for an edited `_test.dart` | Operator prune (vertical-evolution refactor): pub-get/test reminder, not a verifier. |
| `hooks/demoted-hook-cases.jsonl` | Eval cases moved out of `evals/cases/hook-cases.jsonl` for the 6 hooks demoted above | Inert eval cases for the demoted hooks — not run by `run-evals.sh`; move lines back to `evals/cases/hook-cases.jsonl` (fixing hook paths) on re-promotion. |

Out of scope here: content specific to the originating domain/company (the `scripts/check-provenance.sh` denylist covers `unwired/` with no exception, in addition to the manual check of paths/classes/tickets done on each item's entry) and duplication of something already wired.
