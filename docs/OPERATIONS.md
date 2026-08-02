# Kit operations

Scope: how this kit is built, gated, and published — the single governance/operations doc for the owner. Day-to-day installation and use (local marketplace) are in `README.md`.

---

## 1. Publishing to GitHub

Owner side, run from `$HOME/dev/agent-kit`:

```bash
git remote add origin git@github.com:<username>/agent-kit.git
git push -u origin main --tags
```

**Mandatory placeholder.** `<username>` is literal — never replace it with a real account name anywhere in this repo. `scripts/check-provenance.sh` matches account names by substring via the maintainer's local, gitignored `.provenance-deny` — present on every local run, absent in CI's checkout. A real name here still turns the local gate red before the commit exists.

Consumer side: swap the local marketplace for an `extraKnownMarketplaces` entry pointing at GitHub, in `settings.json`:

```json
{
  "extraKnownMarketplaces": {
    "agent-kit": { "source": { "source": "github", "repo": "<username>/agent-kit" } }
  }
}
```

```bash
claude plugin marketplace add <username>/agent-kit
claude plugin install core@agent-kit
claude plugin install council@agent-kit   # recommended with core
claude plugin install team@agent-kit      # optional
claude plugin install mobile@agent-kit    # only in a Flutter/Dart project
```

`core` works standalone; installing `council`/`team`/`mobile` alongside it is a prose recommendation, nothing enforces the pairing. The local marketplace keeps working as the dev path once the remote is published — GitHub is distribution, not where you edit. Consumer update: `claude plugin update <plugin>@agent-kit`, then restart the session.

---

## 2. Commit vs. publish gate

Local commit pays one check: `./scripts/check-provenance.sh` — the one leak cheaper to catch before the commit exists than after. That's the whole commit-time gate.

The full gate runs at **publish**, via CI (`.github/workflows/ci.yml`) and/or `scripts/doctor.sh --maintainer` as the optional local rehearsal:

1. `check-provenance.sh` — structural patterns shipped in the script; literal patterns (real client/product names) from local `.provenance-deny`, gitignored — CI runs structural-only.
2. `check-ceiling.sh` — always-on byte ceiling, see §3.
3. `check-readme-pair.sh` — bilingual README invariants: every pt-BR bash fence byte-identical in the English pair, referenced SVGs exist with `data-look="handDrawn"`, source-of-truth cross-links present.
4. `evals/run-evals.sh` — Tier 1: the real hooks run against synthetic payloads.
5. `shellcheck` over every `.sh` under `plugins scripts evals tools` — CI-only, no local equivalent.

`claude plugin validate .` (marketplace + plugin manifests) is currently local-only, run via `doctor.sh --maintainer`; whether it joins CI is an open operator decision.

Version bumps and the `(plugin X.Y.Z)` changelog trailer move to **publish**, batched across whatever commits accumulated since the last one — not per commit. Going-forward `CHANGELOG.md` entries are 1-3 lines.

---

## 3. Always-on tier ceiling

`using-agent-kit`'s always-on body (injected by `plugins/core/hooks/session-start.sh`) has a hard ceiling of **16,384 bytes**, measured on the hook's real output by `check-ceiling.sh` — no ratchet, just pass/fail against that number. A separate, informational sub-check measures the maintainer's personal `$HOME` `MEMORY.md` index against its own 8,192-byte ceiling — `SKIP`s (not a failure) when the file is absent, the normal state on any other machine or in CI, so it can fail locally while CI stays green.

## 4. Composition with the harness's permission mode

The user's `settings.json` permission mode (`defaultMode`, sandbox) owns the approval decision for tool calls; there is currently no refining layer in front of it in `core`.

## 5. Double-loading note

Installing this marketplace inside a workspace that already has its own committed skills: both sources coexist, no name conflict (namespaced `core:`/`council:`/`team:`/`mobile:`) — the cost is duplicated context, not incorrect behavior.

---

## 6. External skills

Some tools this kit's methodology relies on aren't vendored — they're adopted as-is from the external Claude Code ecosystem at user scope (`~/.claude/skills/`), zero pre-validation. If one proves out with real, repeated use, a 1-line `CHANGELOG.md` note records that it entered the environment; config that only serves the operator's own machine is born gitignored, never tracked.

## 7. Lifecycle

Every artifact — skill, hook, gate — is either wired (`plugins/<plugin>/`, proven real use) or it doesn't exist (deleted, recoverable via git history; no purgatory tier in between). Promotion happens on real use, not "seems useful": rewrite the `description` for the real trigger, fill in provenance placeholders with real names, run `claude plugin validate .`. The meta-principle behind this: **a rule that keeps failing becomes a mechanism** — a hook, a schema, a deterministic gate — and a mechanism with no real catch left becomes a deletion candidate. New ideas are born in `.scratch/` (gitignored) and prove themselves before ever touching `plugins/`. This applies uniformly to skills, hooks, and gates.

**D6** (single load-bearing note): Council's episodic corpus `outcome` is stored and displayed, never scored — cited by `plugins/council/skills/council-recall/SKILL.md`.

## 8. Gitignored working tree — a protection, not an omission

`docs/plans/`, `docs/ideation/`, `docs/agents/`, `docs/superpowers/`, `.scratch/`, and `labs/` are deliberately gitignored: they hold the session material the kit is *developed with* (specs, plans, handoffs, wayfinder config, local scratch) — not the kit itself — and they carry client/engagement names `check-provenance.sh` exists to keep out of a public repo. `apks/` is gitignored for the same client-name reason but is a binary exception: `check-provenance.sh` greps with `-I`, which skips binary content, so the mechanical net below doesn't cover it the same way.

The net for the text-bearing directories needs no separate enforcement: `check-provenance.sh` scans `git ls-files`, so a force-add turns an ignored file into a tracked one and the very next gate run fails on it. Don't force-add under any of the directories above — the text-bearing ones are caught on the next run; `apks/` is not.

---

Surface docs (this file, `README.md`) don't carry dates — history lives in `CHANGELOG.md`.
