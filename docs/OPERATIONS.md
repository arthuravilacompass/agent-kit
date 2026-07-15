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

The user's `settings.json` permission mode (`defaultMode`, sandbox) owns the approval decision for tool calls, including Bash commands. `core` used to add a narrow Bash-only auto-approve refiner in front of it (`bash-autoapprove-readonly.sh`); it went through the vertical-evolution-refactor prune to `unwired/` and was later deleted in the operator's unwired triage (§5): a permission convenience, not an epistemic verifier, and its known comment-newline fail-open closes by removal. There's currently no such refining layer in `core` — the harness's permission mode is the only one.

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
| `ui-comparison/` | Visual-fidelity skill from an originating project | The method (phases, scoring rubric) is generic; without a real design system to test against, there was no way to prove use here. `figma-to-component`, which lived in this same pair, was promoted — see `plugins/mobile/skills/figma-to-component/` and the record in `CHANGELOG.md`. Promotion trigger for this one: the first real Flutter project with a codified design system to run the rubric against. |
| `pr/` | Wired `core` skill, demoted (not deleted) | Commodity: native `gh pr create` / the platform's own PR UI covers the same job now that `core:commit` owns the real lint+test+approval gate this kit adds on top. Kept as reference rather than deleted in case a future project needs a scripted PR-description assembler (templates, base-branch fallback chain) that its own tooling doesn't already provide. |

**Operator's unwired triage** (distinct from the earlier Phase 2 refactor and vertical-evolution-refactor prunes referenced elsewhere in this doc's history): the operator reviewed the rest of the table above and decided, item by item, to delete rather than keep — 17 items removed (`handoff-gate/`, `WORKFLOW.md`, `conflict_triage.py`, `prune_branches.sh`, `check_merged_imports.py`, `swap_pubspec.py`, `scope-inject.sh`, `context-monitor.sh`, `skills/bug-report/`, `skills/compound/`, `hooks/plan-autoload.sh`, `hooks/bash-autoapprove-readonly.sh`, `hooks/claude-dir-guard.sh`, `hooks/dart-auto-format.sh`, `hooks/dart-analyze-file.sh`, `hooks/package-feedback.sh`, `hooks/demoted-hook-cases.jsonl`). Deleted, not demoted: gone from the working tree, recoverable via git history, not eligible for promotion. `ui-comparison/` is the only item that remains, and it stays dormant per the row above.

Out of scope here: content specific to the originating domain/company (the `scripts/check-provenance.sh` denylist covers `unwired/` with no exception, in addition to the manual check of paths/classes/tickets done on each item's entry) and duplication of something already wired.
