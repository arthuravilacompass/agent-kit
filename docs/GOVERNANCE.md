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

## External unvendored skills

Not every tool this kit's methodology relies on lives inside `plugins/`. Some are adopted as-is from the external Claude Code ecosystem — installed globally (`~/.claude/skills/`, via `npx skills add <repo>`), not vendored, not tracked by `INVENTORY.md` (which only covers this repo's own plugin manifests). They sit outside the wired/unwired/deleted model above entirely — that model is for artifacts that live in this repo.

Adopted after hands-on testing on real artifacts, not source-reading alone — evaluation notes live in the maintainer's local session memory, not in this repo:

- **`writing-fragments` / `writing-shape` / `writing-beats`** (from `mattpocock/skills`) — 2-phase explore/exploit writing discipline for turning session raw material into a structured guide/article. `disable-model-invocation: true` in all three — zero always-on cost.
- **`walkthrough`** (from `alexanderop/walkthrough`) — generates a self-contained interactive HTML walkthrough (clickable Mermaid + per-node detail) for explaining a flow/architecture/schema. Model-invoked — always-on cost accepted deliberately.
- **`mermaid-skill`** (from `Agents365-ai/mermaid-skill`) — generates `.mmd` diagrams exported to PNG/SVG. Model-invoked, aggressive auto-trigger description — always-on cost accepted deliberately (low-commitment keep: has a known unresolved subgraph-title clipping bug, `walkthrough` covers the richer "explain this to someone" case, but this one stays for plain diagram-in-a-markdown-doc use).

If one of these earns real, repeated use and the operator wants it to survive an environment reset with edit rights, port it into `plugins/` carrying its external attribution — author, source, license — in the frontmatter's `metadata` field plus an in-body blockquote: the convention `core:orchestrate` used before its removal. One wired skill is vendored from an external source — `core:prompt-optimizer` — and it now carries both halves: an in-body attribution blockquote and the frontmatter field (`grep -n "^metadata:" plugins/core/skills/prompt-optimizer/SKILL.md`). It is the convention's only live example, which is why its shape is flat `key=value; key=value` rather than nested YAML: `scripts/generate_inventory.py`'s frontmatter parser accepts only top-level single-line pairs and exits 1 on an indented one, so a nested `metadata:` block fails the gate even though `claude plugin validate` accepts it.

## Skill vs. standalone tool

A skill has stopped being a skill and should become a standalone tool (invoked by a thin skill) when it accumulates **2 or more** of:

- **(a) its own executable scripts with their own test suite** — not one helper script, a suite with selftests.
- **(b) a dominant fraction of the plugin's files** — the skill outweighs the plugin it's supposed to be one skill within.
- **(c) its own runtime** — dependencies beyond the language stdlib, a venv, or external binaries the method shells out to.

**Verdict**: `apk-archaeology` met all three before this change — 41 of the `mobile` plugin's 79 files (~52%), 10 selftests, external binaries (`jadx`/`apktool`/`adb`). Extracted to `tools/apk-archaeology/`; the skill remains in `plugins/mobile/skills/apk-archaeology/` as a thin conductor that invokes it.

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

`mobile` is the flagship by admission criterion, not by raw volume: it's the vertical the kit's bar for "earns a place" is calibrated against, but of the kit's 31 skills only 11 are Flutter-specific — the other 20 (`core`/`council`/`team`) are stack-agnostic.

## Architecture — 3 layers

| Layer | What it does | Lives in |
|---|---|---|
| **1. Epistemic** | Always-on rules + deterministic gates that don't depend on the model obeying: provenance, `mobile`'s blocking smell-checker, the always-on byte ceiling, plus advisory hooks (codegen-staleness, lifecycle/dispose, DI-mismatch — full list in [INVENTORY.md](../INVENTORY.md)). Council's reasoning postures sit alongside for the judgment calls a gate can't make. | `core` (rules + gates), `mobile` (verifiers), `council` (postures) |
| **2. Conduction — now external** | The kit does not conduct workflow itself. Stage-to-stage conduction lives in CE (`/ce-plan` → `/ce-work` → `/ce-code-review` → `/ce-compound`); discovery lives in `superpowers:brainstorming`. What still crosses this boundary from inside the kit: the mechanism (layer 1) keeps enforcing underneath whichever conductor is running, the vertical (layer 3) fires the same regardless of who conducts, and `council`'s postures wear alongside either — additive, claiming no stage of their own. | CE + `superpowers` (external, not shipped here); `core`/`mobile`/`council` compose with both |
| **3. Verticals** | `mobile` is the flagship: Flutter/Dart review, scaffolding, and the deterministic checks above, calibrated against a real stack. `team` is the secondary vertical (agile ceremonies). | `mobile`, `team` |

## Posture

Deterministic where determinism is possible; agnostic where it isn't. The gates in layer 1 are mechanically verifiable — run them, get a pass/fail, no interpretation required. The broader claim — that any of this improves model behavior in general — is untested; what's real and checked is narrower: the mechanism either fires or it doesn't.

## Conventions

- **Language**: skill/doc bodies in English; runtime output (Council callouts, review findings, `grill-me`, etc.) mirrors the user's language, default English — deterministic scripts/gates always emit English. One exception, scoped to the public face: `README.md` may carry a `README.pt-BR.md` translation pair, cross-linked, with the English file named as source of truth in both headers. The exception does not extend to skill bodies, `docs/`, or anything a plugin loads — and a pt-BR file is the one most likely to collide with `check-provenance.sh`'s deliberately case-sensitive matching (see below), so it earns a manual read against the local denylist, not just a green gate.
- **Slash-only**: `disable-model-invocation: true` when the cost of a wrong trigger is high — an effect hard to reverse, a high orchestration cost, or a long ceremony that shouldn't start on the model's own initiative.
- **`# retire-review:` on a gate whose subject is a model behavior**: the kit governs an artifact's kind, state and size, but not its trajectory — a gate that compensates for how models behave depreciates in relevance as models improve, while staying mechanically correct the whole way down, and a stale *blocking* gate fails loudly (false positives), not quietly. Such a hook carries a `# retire-review:` line beside its `# desc:` naming the behavior it compensates for and the condition for reconsidering it. The line is a marker for a human pass, not a mechanism; nothing in the gate reads it.
- **No provenance narration in a shipped body**: a skill/agent/hook doesn't narrate its own history ("Promoted from `unwired/`", origin-project notes) — that lives in git and `CHANGELOG.md`, not in something loaded every session. `check-ceiling.sh`'s grep for "Promoted from" is only the mechanizable half of this rule; the rest is reviewer judgment.

## Gitignored working tree — a protection, not an omission

Four directories inside this repo are deliberately gitignored and stay that way: `labs/` (local working material), `docs/superpowers/` (discovery specs, plans, handoffs, and loop records), `docs/plans/` (CE plan artifacts), and `docs/ideation/` (CE ideation artifacts). They hold the session material the kit is *developed with*, not the kit itself.

A fifth directory, `apks/`, is gitignored for the same reason — real client APK binaries, per `.gitignore`'s own comment — but is not one of the four above and does not share their mechanism: it holds binaries, not prose, and `check-provenance.sh` greps with `-I`, which treats binary content as non-matching regardless of what literal it contains. The "safety net is already mechanical" claim below is verified true for the four text-bearing directories; it does not extend to `apks/` the same way, since a force-added APK would not trip the same content grep. Whether `apks/` needs a separate, non-text guard is not decided here.

The ignore is load-bearing rather than incidental: files under the text-bearing directories carry client and engagement names — the very literals `check-provenance.sh` exists to keep out of a public repo. Tracking them would not be a tidiness improvement; it would be a provenance incident. Re-derive the current extent rather than trusting a number written here, since both the denylist and the file set move:

```bash
# how many ignored working files would the gate flag if they were tracked
D=$(sed -n "s/^DENY_STRUCTURAL='\(.*\)'\$/\1/p" scripts/check-provenance.sh)
while IFS= read -r p; do case "$p" in ''|\#*) ;; *) D="$D|$p";; esac; done < .provenance-deny
grep -rlEI "$D" docs/superpowers docs/plans docs/ideation | wc -l
```

That command reads the structural patterns out of the gate instead of restating them, for two reasons. It cannot drift from the gate it describes — and a copy pasted into this file would itself trip the gate, since `check-provenance.sh` excludes only *itself* from the scan. Keep the run case-sensitive to match the gate. A case-insensitive variant inflates the count, because at least one local literal is a capitalized proper noun whose lowercase form is an ordinary Portuguese word that appears in normal prose — case is the only thing separating the two, which is why the gate never passes `-i`.

The safety net is already mechanical for the four text-bearing directories, and it is the reason this convention needs no new gate there: `check-provenance.sh` scans `git ls-files`, so a force-add turns an ignored file into a tracked one and the very next gate run fails on it. That makes the rule enforceable without scanning ignored content — the gate guards the boundary, not the working tree behind it. Do not force-add under `labs/`, `docs/superpowers/`, `docs/plans/`, `docs/ideation/`, or `apks/` — the first four are caught by the gate on the next run; `apks/` is not, per the caveat above.

The trade this accepts, stated plainly: plans and specs written in the text-bearing directories drive shipped work from outside every repo gate — nothing reviews them, and nothing catches a claim in them going stale. That cost is accepted knowingly in exchange for keeping client-identifying material out of a public history. The durable record of a decision belongs in `CHANGELOG.md` or a tracked doc, never only in an ignored plan.

## Decisions worth remembering

- **D6** — Council episodic corpus: `outcome` is stored and displayed, never enters scoring/ranking — the corpus records "cases that happened"; interpretation is the reader's. Cited in `plugins/council/skills/council-recall/SKILL.md`.
