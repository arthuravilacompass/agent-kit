# CLAUDE.md

This is **agent-kit** — a Claude Code plugin marketplace (`core`, `council`, `team`, `mobile`) that governs itself with the same discipline it enforces on consumer projects. Working in this repo means editing the kit, not applying it to some other codebase.

`core@agent-kit` is enabled at user scope for the maintainer, so the always-on `using-agent-kit` tier is injected here too, recursively — the kit's own rules apply while developing the kit.

## Map

- **[README.md](README.md)** — what the kit is, day-to-day use, which skill for which job.
- **[docs/INSTALL.md](docs/INSTALL.md)** — install detail: native `claude plugin` commands, non-Claude-Code use, requirements in full.
- **[docs/GOVERNANCE.md](docs/GOVERNANCE.md)** — architecture (3 layers), artifact lifecycle (wired/unwired/deleted), promotion rule, always-on byte ceiling, conventions (language, slash-only, no provenance narration).
- **[docs/OPERATIONS.md](docs/OPERATIONS.md)** — publishing, the quality gate, `unwired/` triage. Owner-only.
- **[CHANGELOG.md](CHANGELOG.md)** — history. Surface docs (this file, README, GOVERNANCE) don't carry dates.

## Before any commit

Run the five-part gate (`docs/OPERATIONS.md` §4):

```bash
./scripts/check-provenance.sh
claude plugin validate .
./evals/run-evals.sh
./scripts/check-ceiling.sh
./scripts/check-readme-pair.sh
```

All five must come back green. There's no separate build/test command — this gate is the repo's CI.

## Commits

`type(scope): short description` — types seen in history: `feat`, `fix`, `docs`, `chore`, `refactor`; scope is a plugin name (`core`, `mobile`, `council`, `team`) or `kit` for a cross-cutting change. When a commit changes a plugin's shipped behavior, the message ends with `(pluginname X.Y.Z)` and the same commit bumps that plugin's `plugin.json` version and adds the `CHANGELOG.md` entry — version and changelog land together with the change, never as a follow-up.

## Agent skills

### Issue tracker

Issues live as markdown files under `.scratch/<feature-slug>/` — part of the gitignored working tree. See `docs/agents/issue-tracker.md` — local, gitignored config, same tier as `.scratch/`, not a kit deliverable.

### Domain docs

Single-context. The kit's real domain docs are `docs/GOVERNANCE.md` and `docs/OPERATIONS.md`; `CONTEXT.md` and `docs/adr/` don't exist here. See `docs/agents/domain.md` — local, gitignored config, same tier as `.scratch/`, not a kit deliverable.

## Watch out

- **Don't force-add under the gitignored working tree.** Which directories, why, and the mechanical safety net: `docs/GOVERNANCE.md`'s "Gitignored working tree" section.
- **Skill/doc bodies are English, always** — even though the maintainer's own environment defaults to Portuguese everywhere else. Runtime output (Council callouts, review findings, `grill-me`) mirrors the user's language; shipped skill/doc content does not.
