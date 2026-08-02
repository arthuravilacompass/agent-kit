# Kit operations

Scope: operations for whoever maintains and publishes this kit (the owner). Day-to-day installation and use (local marketplace) are in `README.md` — this document covers publishing and distribution (including the consumer side of the GitHub route, which only exists once the owner publishes), permissions, and the gate.

---

## 1. Publishing to GitHub

Owner side, run from `$HOME/dev/agent-kit`:

```bash
git remote add origin git@github.com:<username>/agent-kit.git
git push -u origin main --tags
```

**Mandatory placeholder.** `<username>` is literal — never replace it with a real account name in this file or anywhere else in the repo. `scripts/check-provenance.sh` matches account names by substring, but that literal tier now lives in the maintainer's local, gitignored `.provenance-deny` (see §4) — present on every local pre-commit run, absent in `.github/workflows/ci.yml`'s checkout. A real name here still turns the local gate red before the commit exists; don't rely on CI alone to catch it.

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
./scripts/check-ceiling.sh
./scripts/check-readme-pair.sh
```

- `check-provenance.sh` — denylist of company/product/board names and internal paths, run over the whole repo, no exception. Two tiers: **structural** patterns (ticket-ID formats, branch-naming conventions — a format identifies nobody) are hardcoded in the script and shipped; **literal** patterns (the actual client name, internal domain, squad name, personal handles) live in `.provenance-deny` at repo root — gitignored, never tracked, populated locally by the maintainer only. `.provenance-deny.example` (tracked) documents the format with no real names; copy it to `.provenance-deny` and fill in real values on a fresh clone that needs the literal tier. Without the file the gate still runs — structural patterns only — and its `OK`/`FAILED` line always states how many local literal patterns loaded (0 if absent), so the local tier being missing is visible in the gate's own output, not silent. This is also the gate's real-world default in CI: `.github/workflows/ci.yml`'s checkout never has `.provenance-deny` (it's gitignored, never pushed), so CI enforces structural patterns only — full literal coverage happens locally, pre-commit, which is where this gate is meant to catch a leak before it's ever committed.
- `claude plugin validate .` — validates the marketplace manifest and each plugin's manifest.
- `run-evals.sh` — deterministic Tier 1: runs the real hooks against synthetic payloads. Runs via heredoc; in environments that sandbox temp-file creation (some agent harnesses), run with the sandbox disabled for this specific command.
- `check-ceiling.sh` — measures `session-start.sh`'s real output against the always-on tier's byte ceiling, bans "Promoted from" provenance narration inside `plugins/`, and (a third, independent function) soft-checks the maintainer's personal `$HOME` `MEMORY.md` index against its own 8192-byte ceiling — this sub-check `SKIP`s (not a failure) when the file is absent, which is the normal state on any other machine or in CI, so it can fail on the maintainer's own machine while CI stays green. Ceiling and rationale: `docs/GOVERNANCE.md`.
- `check-readme-pair.sh` — mechanical invariants of the bilingual README pair: every pt-BR bash fence exists byte-identically in `README.md` or `docs/INSTALL.md`, every referenced SVG asset exists and carries `data-look="handDrawn"`, and both source-of-truth cross-link headers are present.

Normative convention behind hook/script descriptions: the `# desc:` line (line 2 of every hook/script under `plugins/*/hooks` and `plugins/*/scripts`) is the source of truth. Any prose header already in the file is free commentary, with no effect on tooling. When the two diverge, fix the `# desc:` line — not the prose header.

CI (`.github/workflows/ci.yml`) runs the same five commands, plus one check with no local-only equivalent: `shellcheck` over every `.sh` file under `plugins scripts evals tools`.

Surface docs (README, this file, and `docs/GOVERNANCE.md`) don't carry dates — history lives in `CHANGELOG.md`. Check: `grep -q` for a year-month pattern (`YYYY-`) over the file must fail to match. Note: `grep -c` exits with code 1 when there's no match — don't use `-c` as a chained pass condition in `&&`.

---

## 5. unwired/ — retired

`unwired/` no longer exists in the repo. It held genericized material from originating projects, scrutinized enough to serve as reference but without proven real use in this kit — nothing there was ever loaded by Claude Code, zero context cost while it lived. The table below is kept as the historical record of what passed through it and why each item didn't make it to `plugins/`. Lifecycle (3-state model, promotion rule, always-on ceiling, conventions): `docs/GOVERNANCE.md`.

| Item | Origin | Why it isn't wired |
|---|---|---|
| `ui-comparison/` (deleted, operator's unwired triage below) | Visual-fidelity skill from an originating project | The method (phases, scoring rubric) is generic; without a real design system to test against, there was no way to prove use here. `figma-to-component`, which lived in this same pair, was promoted — see `plugins/mobile/skills/figma-to-component/` and the record in `CHANGELOG.md`. Never earned promotion; deleted outright alongside the rest of `unwired/` rather than kept as reference — recoverable via git history, not eligible for promotion. |
| `pr/` (deleted `f6dccac`, 2026-07-24) | Wired `core` skill, demoted, then deleted | Commodity: native `gh pr create` / the platform's own PR UI covers the same job now that `core:commit` owns the real lint+test+approval gate this kit adds on top. Demoted to `unwired/` on that basis; later deleted outright in `f6dccac` alongside `orchestrate/` (234 lines removed) rather than kept as reference — recoverable via git history, not eligible for promotion. |
| `orchestrate/` (deleted `f6dccac`, 2026-07-24) | Wired `core` skill, demoted, then deleted | Duplicated the platform's own fan-out primitive (`superpowers:dispatching-parallel-agents` / native parallel subagents). The decision layer it sequenced (LABOR vs orchestration typing, worker output contract) migrated to the always-on tier (`core:using-agent-kit`, "Dispatch"); the loop mechanics themselves (Frame/Plan/Delegate/Verify/Synthesize, budget, degraded mode, status board) were mechanics the platform already covers. Demoted to `unwired/orchestrate/` (Shubham Saboo attribution, Apache-2.0) first; deleted outright in `f6dccac` alongside `pr/` rather than kept as reference — recoverable via git history, not eligible for promotion. |
| `flutter-migration-lessons.md` (deleted, operator's unwired triage below) | 12 depersonalized incidents from a native→Flutter migration pipeline's own retrospective, kept out of `apk-archaeology` on purpose — that skill covers the origin side of a migration (APK → catalog → backlog) and stops there; these are about the destination side (backlog → real Flutter code), a different boundary | Was never a skill, only preserved raw material: a genuine downstream method needed a 2nd migrated capability to complete all 4 phases before generalizing (only one had, twice — distilling from n=1 family would have repeated the last lesson in the file). Never earned promotion; deleted outright alongside the rest of `unwired/` rather than kept as reference — recoverable via git history, not eligible for promotion. |

**Operator's unwired triage** (distinct from the earlier Phase 2 refactor and vertical-evolution-refactor prunes referenced elsewhere in this doc's history): the operator reviewed the rest of the table above and decided, item by item, to delete rather than keep — 17 items removed (`handoff-gate/`, `WORKFLOW.md`, `conflict_triage.py`, `prune_branches.sh`, `check_merged_imports.py`, `swap_pubspec.py`, `scope-inject.sh`, `context-monitor.sh`, `skills/bug-report/`, `skills/compound/`, `hooks/plan-autoload.sh`, `hooks/bash-autoapprove-readonly.sh`, `hooks/claude-dir-guard.sh`, `hooks/dart-auto-format.sh`, `hooks/dart-analyze-file.sh`, `hooks/package-feedback.sh`, `hooks/demoted-hook-cases.jsonl`). Deleted, not demoted: gone from the working tree, recoverable via git history, not eligible for promotion. `ui-comparison/` and `flutter-migration-lessons.md` were the last two items remaining after that pass; the operator later sentenced both, and the empty `unwired/` directory was removed along with them — no item is eligible for promotion from a tier that no longer exists.

Out of scope here: content specific to the originating domain/company (the `scripts/check-provenance.sh` denylist covered `unwired/` with no exception while it existed, in addition to the manual check of paths/classes/tickets done on each item's entry) and duplication of something already wired.
