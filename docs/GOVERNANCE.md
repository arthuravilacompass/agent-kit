# Kit governance

Canonical doc for the agent-kit artifact lifecycle. Every normative lifecycle rule lives here and only here; the skill-authoring format lives in this doc's §SKILL.md contract (D14). `README.md`, `unwired/README.md`, and `using-agent-kit` point here. History and dates live in `CHANGELOG.md`; measurements live in the gate (`scripts/check-governance.sh`).

## The 3-state model (D10)

Every artifact that has ever existed in this kit is in one of these three states, never in limbo:

- **wired** — lives in `plugins/<plugin>/` (today: `core`, `council`, `team`, `mobile`). Admitted because it has proven real use (not just "seemed good"). Costs context in every session that loads the plugin.
- **unwired** — lives in `unwired/`. Genericizable, mechanical scrub applied, but no proof of use in the new project. Context cost **zero** — only read if someone opens the file.
- **deleted** — does not exist in the repo. Evaluated and discarded (vestigial, too specific to the origin project to genericize, or replaced by something better).

Never "tested but not wired" — that phantom third category is exactly what this model exists to eliminate.

## Promotion rule

**An item moves up from `unwired/` to `plugins/` (wired) when it has proven real use in the new project — the same admission bar any new skill/agent/hook would have.** Not "seems useful" nor "was used in the origin project" — it's: you invoked it at least once in the new project, it worked, and you want it to survive the next `/clear`.

When promoting:

1. **Rewrite the `description`** with the trigger specific to the new context — the archived description carries the origin project's vocabulary/trigger (sometimes already generic, sometimes not).
2. **Fill in the provenance placeholders** (`<TICKET>`, `<DesignTokens>`, `<BOARD_NAME>`, component names inside `<>`) with the new project's real names. The scrub that put the item in `unwired/` was mechanical, not a rewrite — re-anchoring it in the new domain is your job, not this kit's.
3. **Move the file** to `plugins/<plugin>/` in the standard layout (skills under `skills/<name>/SKILL.md`, agents under `agents/<name>.md`, etc.) and run `claude plugin validate .`.
4. **Delete the copy in `unwired/`** — a promoted item doesn't stay duplicated in both states.

### Exception: provisional promotion under a rotation deadline

When the deallocation of an origin workspace threatens to close the validation window, an item MAY be promoted without proven real use in this kit, provided that: (1) the exception is logged in `CHANGELOG.md` with the reason; (2) the promotion goes through immediate adversarial review of the full diff — the first batch promoted under this exception had 15 defects found in a "purely mechanical" move (logged in `CHANGELOG.md`); (3) the item gets a validation deadline — no real use within 1 new-project cycle sends it back to `unwired/`. A provisional promotion that isn't logged this way is a governance violation, not an exception to it.

### Active provisionals (machine-read)

Items currently wired under the exception above. Line format (contract read by `scripts/generate_inventory.py` and `scripts/check-governance.sh`): `` - `<artifact relative path>` — valid until YYYY-MM-DD ``. Skills are listed by the skill's directory (`plugins/<p>/skills/<name>`), agents by the `.md` file (`plugins/<p>/agents/<name>.md`). An item validated by use leaves the list (becomes fully wired); a missed deadline turns the gate red until a decision is made — validate or demote (D17).

- `plugins/core/skills/bug-report` — valid until 2026-08-06
- `plugins/team/skills/refine-live` — valid until 2026-08-06
- `plugins/team/skills/refine-async` — valid until 2026-08-06
- `plugins/mobile/skills/figma-to-component` — valid until 2026-08-06
- `plugins/council/skills/council` — valid until 2026-08-06
- `plugins/council/skills/bohr` — valid until 2026-08-06
- `plugins/council/skills/sagan` — valid until 2026-08-06
- `plugins/core/agents/cold-reader.md` — valid until 2026-08-06
- `plugins/council/skills/council-log` — valid until 2026-08-06
- `plugins/council/skills/council-recall` — valid until 2026-08-06
- `plugins/council/agents/maxwell.md` — valid until 2026-08-06
- `plugins/council/agents/zeno.md` — valid until 2026-08-06
- `plugins/council/agents/epistemic-council.md` — valid until 2026-08-06

Note: `schrodinger` and `epicurus` do NOT belong here — they were wired in the original extraction with a lineage of use, not under the exception (CHANGELOG, 2026-07-07 batch lists 8 files).

## Meta-principles

- **Code with an ID is born with a validator, or not at all.** Every rule, hook, or skill identified by an ID is born together with the mechanism that verifies its enforcement (gate, hook, script) — never as loose text without enforcement. This doc applies the rule to itself: every D*/R* ID cited in the repo must resolve in the ledger below, verified by `scripts/check-governance.sh` in the gate.
- **A textual rule that keeps failing becomes a mechanism.** Under a finite attention budget, marginal instructions get omitted, not disobeyed — stacking more text reduces aggregate compliance, it doesn't just stop improving it. The rule with the highest failure rate becomes a hook, a mandatory output schema, or a deterministic gate — not more text.
- **An advisory nudge doesn't enter `plugins/` without measurement.** A reminder-only mechanism must prove real conversion before being wired; concrete case: `learning-pulse` (per-item table in `docs/OPERATIONS.md` §5), which measured ~0 conversion in the origin project and only comes back with new measurement that justifies the cost.

## Always-on tier ceiling

The `core` always-on tier — the body of `using-agent-kit` injected per session via `plugins/core/hooks/session-start.sh` — has a ceiling of **16,384 bytes**, measured on the hook's actual output (full JSON; a conservative proxy for the injected payload, envelope and escaping included).

- **Enforcement**: `scripts/check-governance.sh` in the gate — red if the measurement goes over the ceiling.
- **Intended effect**: selection pressure. A new rule in the always-on tier competes for space; when the ceiling tightens, something has to go (becomes an on-demand skill, a mechanism, or gets deleted) — the ceiling doesn't rise for convenience. Raising the ceiling is a governance decision: it requires a new ledger entry.

## SKILL.md contract (D14)

Authoring format for every skill in the kit. Mechanical enforcement: `scripts/check-governance.sh` reads the §Conformity section below.

**Scope**: a new skill is born conformant. An existing skill conforms when it undergoes a *reform* — a change of skeleton, purpose, or structure; on being reformed, it enters §Conformity. A surgical fix (point edits that change neither skeleton, purpose, nor structure) does not constitute a reform and does not force conformity. Translating a skill's body to another language preserves its skeleton, purpose, and structure, so it is **NOT a reform** either, and does not pull the skill into §Conformity or under the line ceiling. No big-bang on the existing stock.

### The three skeletons

Every conformant SKILL.md is one of these three. Each conformed file's skeleton is named in §Conformity.

#### `posture` — in-thread epistemic lens

Changes reasoning in progress; produces no artifact.

1. Frontmatter: `name` + `description` with a quotable situational trigger.
2. Identity (1–3 lines): the question the posture forces.
3. Ritual: Restate Gate → deliberation → opposition device → escalation clause.
4. Output format: the Council's callout (`council:council`).

#### `procedure` — flow with effects

Steps that change state (commit, PR, files, board).

1. Frontmatter.
2. Purpose (1–2 lines).
3. Consumer-project config/prerequisites — what the skill assumes exists and what to do when it's missing.
4. Numbered steps — each with an action and a verifiable criterion; an explicit approval point before any effect that's hard to reverse.
5. Inviolable rules — short final section.

#### `router` — index that points

Maps when to read what; doesn't carry the content.

1. Frontmatter.
2. What this index maps (1–2 lines).
3. Routes: a table or list of "read X when Y".
4. Routing rules, if any.

Inline technical content in a router is a sign of pending extraction to `REFERENCE.md`.

### Language policy

- Body in **English**. `name`, commands, code, paths, and technical terms in English (unchanged).
- `description` in English, with quotable triggers — phrases the user would actually say. Semantic skill-matching still fires on pt-BR prompts; the trigger doesn't have to be in the user's language to match it.
- **Runtime output follows the user's language, default English**: model-generated output (Council callouts, review findings, consumer-simulation, grill-me) mirrors the language of the prompt it responds to; deterministic scripts (gate messages, hook feedback) always emit English. `team:chat-draft` producing pt-BR for a lusophone team is an *instance* of this rule, not an exception to it.

### Line ceiling

- `SKILL.md` ≤ **120 lines** (`wc -l`), verified by the gate for the files in §Conformity.
- Overflow extracts to support files in the same directory — `REFERENCE.md` (full signal, tables, long examples), `PATTERNS.md`, `RECIPES.md`. The model case is `plugins/mobile/skills/mobx/`.
- Cutting criterion: SKILL.md keeps what the model needs to decide **whether** to invoke and **how** to start; the rest is on-demand.
- Exempt: `using-agent-kit` — always-on tier, governed by the byte ceiling (`docs/GOVERNANCE.md` §Always-on tier ceiling).

### Slash-only criterion

`disable-model-invocation: true` when the skill: (a) triggers an effect that's hard to reverse (commit, PR, an external write consumed by third parties, board), (b) has a high execution cost from orchestration (dispatching multiple agents/subagents), or (c) drives a long ceremony that shouldn't start on the model's own initiative. A lens, posture, index, or context-cheap reference stays model-invocable — as does a single-purpose tool triggered by explicit user intent (e.g., driving the app in the simulator), even if it runs a build. Edge cases are decided by the cost of a wrong trigger: a skill that only proposes and stops (`learn`) can be invocable; a skill that runs the whole chain (`bug-report`) is slash-only.

### Prohibitions (repo-wide, not just conformant files)

- **Provenance narration in a skill's body** — "promoted from", "where it came from", "different from the original setup", promotion dates. Provenance lives in `CHANGELOG.md` and the GOVERNANCE ledger. The mechanizable marker (`Promoted from` in `plugins/`) is verified by the gate; the rest is review criterion.
- **Correction history as a section** — the corrected formulation lives where the rule lives; the history lives in git and in `CHANGELOG.md`.

### Descriptions (D16)

The frontmatter `description` answers only **"when to invoke"** — a quotable situational trigger, not a summary of what the skill does nor its history. Ceilings in UTF-8 bytes on the `description:` line's value, verified by `scripts/check-governance.sh` (check 6):

- **≤ 350 bytes** per skill (posture and procedure skeletons).
- **≤ 700 bytes** for the invocation-router class — descriptions that carry the routing-trigger table: `pipeline`, `methodology`, and `mobx`. Cutting a router's trigger degrades the conversion the census measures.
- **Aggregate per plugin**: core ≤ 4096 · team ≤ 1024 · mobile ≤ 3584 bytes. Same selection pressure as the always-on ceiling: a new description competes for space; raising the ceiling is a ledger decision.
- **`plugins/council/` is exempt until the census** — descriptions frozen as a condition of measuring the postures' conversion (§Active provisionals); the ceiling starts applying to council at the census decision.

The form rule (only "when to invoke") is review criterion; the ceilings are the mechanical enforcement.

### Conformity

List read by the gate: each file below exists and respects the line ceiling. Entry format: `` - `<path>` — <skeleton> ``.

- `plugins/council/skills/council/SKILL.md` — router
- `plugins/mobile/skills/mobx/SKILL.md` — router
- `plugins/core/skills/commit/SKILL.md` — procedure
- `plugins/core/skills/archaeology/SKILL.md` — procedure
- `plugins/core/skills/grill-me/SKILL.md` — procedure

## Decision ledger

Record of decisions identified by ID (series `D*` = design decision, `R*` = acceptance requirement) cited in this repo. **A new decision takes the next free ID in the `D` series and is born with an entry in this ledger** — citing an ID without an entry here turns the gate red. Entry format (contract read by the gate): a list item starting with `- **<ID>** — <decision>`.

- **D6** — Council episodic corpus: `outcome` is stored and displayed, never enters scoring/ranking — the corpus records "cases that happened"; interpretation is the reader's. Cited in `plugins/council/skills/council-recall/SKILL.md`.
- **D10** — 3-state model (wired/unwired/deleted) for every artifact in the kit; eliminates the phantom "tested but not wired" category. Normative text: this doc's "The 3-state model" section.
- **D13** — Acceptance metrics for the kit extraction: the `gate-day3-pass` tag and the two-week metric (first real use in a project outside the origin project within the deadline, otherwise the result was "an inventory with a README"). Log and dates: `CHANGELOG.md` §Métricas D13.
- **R2** — Acceptance requirement for the extraction: measure the kit's real payload cost (tokens/turn + session injection) and run a behavioral A/B with and without the kit. Results and known measurement gaps: `CHANGELOG.md` §Aceite final (c).
- **D14** — SKILL.md contract: three named skeletons (posture / procedure / router), language policy (body in English; runtime output follows the user's language, default English; no grandfathered exception), and a 120-line ceiling with extraction to support files. Normative text and conformity list: this doc's §SKILL.md contract; enforcement: `scripts/check-governance.sh` (conformity + prohibition on provenance narration in `plugins/`).
- **D15** — Identity and structure across 4 plugins: `core` (delivery methodology with deterministic enforcement, ticket to PR, any stack), `council` (epistemic lenses for high-reversal-cost decisions), `team` (agile-ceremony copilot — PO refinement, squad communication), `mobile` (Flutter/Dart toolkit). Coherence test for a new skill: doesn't fit any identity sentence ⇒ doesn't enter any plugin. Includes the amendment to D10's text (wired lives in `plugins/<plugin>/`). Census condition preserved in the council extraction: zero internal reform, descriptions identical modulo namespace, `council` installed wherever `core` is (`docs/OPERATIONS.md` §1). Validators: `claude plugin validate .` (manual, outside CI) + `python3 scripts/generate_inventory.py --check` (CI).
- **D16** — Description governance: form rule (description answers only "when to invoke") + per-class ceilings (350 bytes; router 700) + per-plugin aggregate ceiling, with `council` exempt until the census. Normative text: this doc's §SKILL.md contract → Descriptions. Enforcement: `scripts/check-governance.sh` (check 6); aggregate published by `scripts/generate_inventory.py` in `INVENTORY.md`.
- **D17** — Machine-readable wired-provisional marker with a deadline (this doc's §Active provisionals): INVENTORY marks the item, a missed deadline turns the gate red until validated or demoted. Enforcement: `scripts/check-governance.sh` (check 5) + `scripts/generate_inventory.py` (⏳ marker).
