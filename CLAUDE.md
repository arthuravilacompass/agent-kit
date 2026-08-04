# CLAUDE.md

This is **agent-kit** — a Claude Code plugin marketplace (`core`, `council`, `team`, `mobile`) that governs itself with the same discipline it enforces on consumer projects. Working in this repo means editing the kit, not applying it to some other codebase.

`core@agent-kit` is enabled at user scope for the maintainer, so the always-on `using-agent-kit` tier is injected here too, recursively — the kit's own rules apply while developing the kit.

## Map

- **[README.md](README.md)** — what the kit is, day-to-day use, which skill for which job.
- **[docs/INSTALL.md](docs/INSTALL.md)** — install detail: native `claude plugin` commands, non-Claude-Code use, requirements in full.
- **[docs/OPERATIONS.md](docs/OPERATIONS.md)** — the single governance/operations doc: artifact lifecycle, promotion rule, always-on byte ceiling, publishing, and the quality gate. Owner-only.
- **[CHANGELOG.md](CHANGELOG.md)** — history. Surface docs (this file, README, OPERATIONS) don't carry dates.

## Before publishing

Local commit pays one check: `./scripts/check-provenance.sh`. The full gate runs at publish via CI (`.github/workflows/ci.yml`): provenance, ceiling, readme-pair, shellcheck. `scripts/doctor.sh --maintainer` is the optional local rehearsal — same 4 gates, but `claude plugin validate .` stands in for `shellcheck` (deliberately local-only; the `claude` CLI isn't on CI runners). Detail: `docs/OPERATIONS.md` §2.

## Commits

`type(scope): short description` — types seen in history: `feat`, `fix`, `docs`, `chore`, `refactor`; scope is a plugin name (`core`, `mobile`, `council`, `team`) or `kit` for a cross-cutting change.

## Agent skills

Client-effort work (including its own issue tracking) doesn't happen in this repo — it lives in `~/dev/labs` (`wayfinder/<esforço>/issues/NN-slug.md`, open tickets only — resolved ones die once their gist lands in the effort's `wayfinder/<esforço>/map.md`), a separate local git repo with no remote. The kit's real domain doc is `docs/OPERATIONS.md`; `CONTEXT.md` and `docs/adr/` don't exist here.

## Watch out

- **Don't force-add under the gitignored working tree.** Which directories, why, and the mechanical safety net: `docs/OPERATIONS.md`'s "Gitignored working tree" section.
- **Skill/doc bodies: English preferred for shipped content** — the maintainer's own environment defaults to Portuguese everywhere else, but shipped skill/doc bodies default English. Runtime output (Council callouts, review findings, `grill-me`) mirrors the user's language.
