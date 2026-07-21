# CLAUDE.md

This is **agent-kit** — a Claude Code plugin marketplace (`core`, `council`, `team`, `mobile`) that governs itself with the same discipline it enforces on consumer projects. Working in this repo means editing the kit, not applying it to some other codebase.

`core@agent-kit` is enabled at user scope for the maintainer, so the always-on `using-agent-kit` tier is injected here too, recursively — the kit's own rules apply while developing the kit.

## Map

- **[README.md](README.md)** — what the kit is, install, day-to-day use, which skill for which job.
- **[docs/GOVERNANCE.md](docs/GOVERNANCE.md)** — architecture (3 layers), artifact lifecycle (wired/unwired/deleted), promotion rule, always-on byte ceiling, conventions (language, slash-only, no provenance narration).
- **[docs/OPERATIONS.md](docs/OPERATIONS.md)** — publishing, the quality gate, `unwired/` triage. Owner-only.
- **[INVENTORY.md](INVENTORY.md)** — generated catalog of every skill/agent/hook/script. Never hand-edit; regenerate with `python3 scripts/generate_inventory.py`.
- **[CHANGELOG.md](CHANGELOG.md)** — history. Surface docs (this file, README, GOVERNANCE) don't carry dates.

## Before any commit

Run the five-part gate (`docs/OPERATIONS.md` §4):

```bash
./scripts/check-provenance.sh
claude plugin validate .
./evals/run-evals.sh
python3 scripts/generate_inventory.py --check
./scripts/check-ceiling.sh
```

All five must come back green. There's no separate build/test command — this gate is the repo's CI.

## Commits

`type(scope): short description` — types seen in history: `feat`, `fix`, `docs`, `chore`, `refactor`; scope is a plugin name (`core`, `mobile`, `council`, `team`) or `kit` for a cross-cutting change. When a commit changes a plugin's shipped behavior, the message ends with `(pluginname X.Y.Z)` and the same commit bumps that plugin's `plugin.json` version and adds the `CHANGELOG.md` entry — version and changelog land together with the change, never as a follow-up.

## Watch out

- **`labs/` is gitignored on purpose.** It holds local working material that must never reach the repo — that's what `check-provenance.sh` guards against for anything that *does* get tracked. Don't force-add anything under `labs/`.
- **Skill/doc bodies are English, always** — even though the maintainer's own environment defaults to Portuguese everywhere else. Runtime output (Council callouts, review findings, `grill-me`) mirrors the user's language; shipped skill/doc content does not.
