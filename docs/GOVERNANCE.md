# Kit governance

Canonical doc for the agent-kit artifact lifecycle. `README.md`, `unwired/README.md`, and `using-agent-kit` point here. History and dates live in `CHANGELOG.md`; the always-on byte ceiling is measured by `scripts/check-ceiling.sh`.

## The 3-state model (D10)

Every artifact that has ever existed in this kit is in one of these three states, never in limbo:

- **wired** — lives in `plugins/<plugin>/` (today: `core`, `council`, `team`, `mobile`). Admitted because it has proven real use (not just "seemed good"). Costs context in every session that loads the plugin.
- **unwired** — lives in `unwired/`. Genericizable, mechanical scrub applied, but no proof of use in the new project. Context cost **zero** — only read if someone opens the file.
- **deleted** — does not exist in the repo. Evaluated and discarded (vestigial, too specific to the origin project to genericize, or replaced by something better).

Never "tested but not wired" — that phantom third category is exactly what this model exists to eliminate.

## Promotion rule

**An item moves up from `unwired/` to `plugins/` (wired) when it has proven real use in the new project — the same admission bar any new skill/agent/hook would have, no exception for something merely advisory or reminder-only.** Not "seems useful" nor "was used in the origin project" — it's: you invoked it at least once in the new project, it worked, and you want it to survive the next `/clear`.

When promoting:

1. **Rewrite the `description`** with the trigger specific to the new context — the archived description carries the origin project's vocabulary/trigger (sometimes already generic, sometimes not).
2. **Fill in the provenance placeholders** (`<TICKET>`, `<DesignTokens>`, `<BOARD_NAME>`, component names inside `<>`) with the new project's real names. The scrub that put the item in `unwired/` was mechanical, not a rewrite — re-anchoring it in the new domain is your job, not this kit's.
3. **Move the file** to `plugins/<plugin>/` in the standard layout (skills under `skills/<name>/SKILL.md`, agents under `agents/<name>.md`, etc.) and run `claude plugin validate .`.
4. **Delete the copy in `unwired/`** — a promoted item doesn't stay duplicated in both states.

Historically, a few items were promoted under rotation-deadline pressure before proven real use — logged with immediate adversarial review of the diff in `CHANGELOG.md`; that path isn't machine-tracked in this doc anymore.

## Meta-principle

**A textual rule that keeps failing becomes a mechanism.** Under a finite attention budget, marginal instructions get omitted, not disobeyed — stacking more text reduces aggregate compliance, it doesn't just stop improving it. The rule with the highest failure rate becomes a hook, a mandatory output schema, or a deterministic gate — not more text.

## Always-on tier ceiling

The `core` always-on tier — the body of `using-agent-kit` injected per session via `plugins/core/hooks/session-start.sh` — has a ceiling of **16,384 bytes**, measured on the hook's actual output (full JSON; a conservative proxy for the injected payload, envelope and escaping included).

- **Enforcement**: `scripts/check-ceiling.sh` in the gate — red if the measurement goes over the ceiling.
- **Intended effect**: selection pressure. A new rule in the always-on tier competes for space; when the ceiling tightens, something has to go (becomes an on-demand skill, a mechanism, or gets deleted) — the ceiling doesn't rise for convenience. Raising the ceiling is a governance decision.

## What each plugin is

Identity across the kit's 4 plugins — the coherence test for a new skill: if it doesn't fit any sentence below, it doesn't enter any plugin.

- **`core`** — delivery methodology with deterministic enforcement, ticket to PR, any stack.
- **`council`** — epistemic lenses for high-reversal-cost decisions.
- **`team`** — agile-ceremony copilot (PO refinement, squad communication).
- **`mobile`** — Flutter/Dart toolkit.

## Conventions

- **Language**: skill/doc bodies in English; runtime output (Council callouts, review findings, `grill-me`, etc.) mirrors the user's language, default English — deterministic scripts/gates always emit English.
- **Slash-only**: `disable-model-invocation: true` when the cost of a wrong trigger is high — an effect hard to reverse, a high orchestration cost, or a long ceremony that shouldn't start on the model's own initiative.
- **No provenance narration in a shipped body**: a skill/agent/hook doesn't narrate its own history ("Promoted from `unwired/`", origin-project notes) — that lives in git and `CHANGELOG.md`, not in something loaded every session. `check-ceiling.sh`'s grep for "Promoted from" is only the mechanizable half of this rule; the rest is reviewer judgment.

## Decisions worth remembering

- **D6** — Council episodic corpus: `outcome` is stored and displayed, never enters scoring/ranking — the corpus records "cases that happened"; interpretation is the reader's. Cited in `plugins/council/skills/council-recall/SKILL.md`.
