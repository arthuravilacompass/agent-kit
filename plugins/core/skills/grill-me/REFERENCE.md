# grill-me escalation mode — reference

Deterministic, controlled-context escalation at a checkpoint **you** choose. This skill **complements** Claude Code's native advisor (`/advisor`) — it does not replace it.

The native advisor escalates to a stronger model with the **full conversation**, whenever *Claude* decides to consult it. This skill fires at a checkpoint *you* pick, with the context and framing *you* control — including the one thing the native advisor structurally **cannot** do: review **blind**, to break your epistemic bubble instead of inheriting it.

## Two mechanisms, by design

| Mechanism | Context it gets | Who triggers | Used by |
|---|---|---|---|
| **Native advisor** (`/advisor opus`) | Full conversation, always | Claude (model-driven; requestable) | `pre-plan`, `post-plan` |
| **Blind adversarial subagent** (Agent tool, `model: opus`) | Only what you pass (diff + ACs); reads the repo fresh | You, deterministically | `pre-done` |

**Why split:** the native advisor sees everything — ideal when the reviewer needs the whole problem (planning, approach choice). But "sees everything" means it inherits your framing, and a model that shares your blind spot can't catch what you missed (the *self-correction illusion*: models reliably correct **others**, not **themselves**). For the "I think I'm done" check, that correlation is the enemy — so `pre-done` withholds your narrative and gives a fresh reviewer an adversarial mandate.

## Consumer-project config

This skill assumes the consumer project defines:
- **Architecture doc** loaded in `pre-plan` (e.g., `CLAUDE.md §Architecture` or equivalent).
- **Modules directory** used to list the target area's existing structure in `pre-plan`.
- **Rule/lint files** cited as lenses in `post-plan` (e.g., bugfix principles, stack-specific quality rules).
- **Base branch** used in `pre-done` for the `git diff` (default: `main`).
- **Rule categories by change type** in `pre-done` (e.g., state-management rules if stores changed, architecture rules if cross-layer, UI rules if widgets) — used to build the blind reviewer's checklist.
- **Ticket ID pattern**, if the project uses a tracker with its own prefix.

Without these configs, the skill still runs — just with less specialized context loaded automatically.

## Advisor prerequisite

**Prerequisite for `pre-plan` / `post-plan`:** an advisor model must be configured — run `/advisor opus` (persists) or set `"advisorModel": "opus"` in settings. Requires Claude Code ≥ v2.1.98 on the Anthropic API. If no advisor is configured, those modes fall back to a full-context subagent dispatch (`model: opus`) so the checkpoint still runs.

## Ticket source

`pre-plan` and `pre-done` need the ticket text / ACs. **Do not hardcode an MCP tool name.** Resolve the *get-issue* tool available in the session at runtime (e.g. via tool search) — MCP server aliases change over time and a hardcoded name silently breaks the fetch. If no tracker tool is available, ask the user to paste the ticket text / ACs. The skill depends on the **ticket content**, never on a specific integration.

## Steps per mode

### Usage

```
/core:grill-me pre-plan <TICKET> [--greenfield]
/core:grill-me post-plan
/core:grill-me pre-done
```

`--greenfield` (pre-plan only): the work is a **new concept judged on its own merit**. Firewall the advisor from the project's rules/skills so it does not re-anchor the design to what already exists.

### When to Use Each Mode

| Mode | Mechanism | Checkpoint | When |
|---|---|---|---|
| `pre-plan` | native advisor (full ctx) | Before choosing an approach | Before design/approach lock-in; beginning of a track with multiple viable alternatives |
| `post-plan` | native advisor (full ctx) | Plan approved, before coding | Right after a plan is approved and before the first implementation file is touched |
| `pre-done` | blind subagent (diff + ACs only) | "I think I'm done" / "acho que terminei" / "tá pronto" | Right before wrapping up / opening a PR / final review |

`pre-done` carries the mechanical delta — blind dispatch, citation verification, no other checkpoint has either. `pre-plan` and `post-plan` add no new mechanism of their own: they're timing-discipline wrappers over the native `/advisor`, guaranteeing it fires at a specific checkpoint instead of only when Claude decides to consult it.

### Steps

1. **Parse the arguments**

   Validate the first argument is one of: `pre-plan`, `post-plan`, `pre-done`.

   If mode is `pre-plan`, require a ticket ID (e.g., `<TICKET>`) as second argument. If missing, ask: "Which ticket?" Parse the optional `--greenfield` flag (pre-plan only).

   If mode is missing or invalid, show usage and stop.

2. **Load context for the mode**

   **`pre-plan <ticket>` (default):**
   - Fetch the ticket text (see **Ticket source** above)
   - Load the project's architecture doc (config)
   - Load relevant project code-review skill content for component/module structure (config)
   - Include: existing module structure of the target area (via Glob on the project's module directory — config)

   **`pre-plan <ticket> --greenfield`:**
   - Fetch the ticket text (see **Ticket source**) — **and nothing else**.
   - Do **NOT** load rules, skills, or module structure. The advisor judges by first principles; existing patterns are optional convenience, never the measuring stick. (Loading the harness as a lens re-anchors a novel concept into what already exists and erases the new design — a documented, repeated failure.)

   **`post-plan`:**
   - Identify the active plan file (most recent `docs/superpowers/plans/*.md`). The native advisor already has the conversation — **point at the plan, do not re-paste it.**
   - Name the project's rule files to weigh as **lenses** (not a compliance gate) — config (e.g. bugfix principles, stack-specific quality rules). Quote them only if they are not already in the conversation.

   **`pre-done`:**
   - Run `git diff <base>...HEAD` where base is the project's default integration branch (config; fallback: `main`)
   - Fetch the ticket ACs (see **Ticket source**) for the work under review
   - Derive affected modules from changed paths and collect the rule files relevant to them (project-specific categories — config; e.g. state-management rules if stores changed, architecture rules if cross-layer, UI rules if widgets). These become the reviewer's **checklist**.
   - Do **NOT** gather your commit messages, the plan, or your own rationale. That narrative is exactly the framing the blind review exists to escape.

3. **Escalate — mechanism per mode**

   **`pre-plan` / `post-plan` — native advisor:**
   - Confirm an advisor model is configured (else fall back to a subagent with `model: opus`).
   - Solicit a consultation with the mode framing below. The advisor sees the full conversation — **do not re-paste context.**

     *`pre-plan` framing (merit-first, NOT "which rule does this violate"):*
     > "I'm about to plan an approach for [ticket]. What's the right abstraction here, on its own terms? What's the highest risk if I pick the wrong approach? If an existing pattern genuinely fits, name it — but don't force the design into one."
     > (`--greenfield`: drop the existing-pattern clause entirely; judge purely on first principles.)

     *`post-plan` framing:*
     > "Review the plan I just produced. What hidden dependencies does it carry? Which assumptions are fragile? Where would a naive implementation violate a project invariant (use the named rules as lenses)? Cite specifics."

   **`pre-done` — blind adversarial subagent:**
   - Dispatch **one** subagent via the Agent tool (`model: opus`). It is blind to your **narrative**, not to the **code** — it reads the repo fresh.
   - Pass it ONLY: the diff, the ticket ACs, and the paths of the rule files for the affected modules (it reads them).
   - Mandate (adversarial):
     > "This change is presented as complete. Assume it is **not**. Find the regression, the dropped behavior, the scope drift, the missing verification. Run the bidirectional trace: **every diff hunk must trace to an AC** (unmatched hunk = scope creep) and **every AC must have a corresponding hunk** (unmatched AC = omission) — list the orphans of both sides explicitly. Work against the diff and read the surrounding code to confirm. For every claim about current code, cite `file:lineStart-lineEnd` and set `epistemicSource`. Return findings as a JSON array."
   - Findings schema (consumed by a citation validator — see project's hook/script setup):
     ```json
     [{ "claim": "...", "epistemicSource": "tool-output",
        "evidence": {"file": "...", "lineStart": N, "lineEnd": M},
        "severity": "critical|warning|consideration", "rule": "CODE|null" }]
     ```
     Use `epistemicSource: "inference"` for judgment calls that don't cite code (validator passes these through).

4. **(`pre-done` only) Verify citations before presenting**

   The read-ledger hook + `validate_citations.py` are grill-me-internal infrastructure (operator decision 2026-07-12): they exist to arm this checkpoint, not as a standalone product; other skills must not depend on them.

   If the project has a citation-verification mechanism (script that checks findings against a session's read-ledger), run it with an **explicit** session id — subagent reads are logged under the parent session, so auto-discovery is unsafe with concurrent sessions.
   - `verified` / `passthrough` → present normally.
   - `unverified` (cited code that overlaps no actual read — likely fabrication) → route to the "⚠️ Unverified" bucket, marked as a hypothesis, **never** as a confirmed finding.

   Complementary, not a substitute: re-read the cited lines and drop findings already addressed in the diff.

## Presentation format

5. **Present findings to the user in the language they've been using, default English**

   Format:
   ```
   ## Advisor Findings (<mode>)

   ### Critical (🔴)
   - <finding> — rule <CODE> — <file>:<line>

   ### Warning (🟡)
   - <finding> — rule <CODE> — <file>:<line>

   ### Considerations (🟣)
   - <finding>

   ### ⚠️ Unverified (<n>)   ← pre-done only
   - <finding> — <file>:<line> (citation doesn't overlap a ledger read — possible fabrication)
   ```

6. **Ask the user how to proceed**

   Never apply findings automatically. Ask: "How should I proceed? Reply: address-all / address-selected <n,m,...> / note-as-followup / ignore"

   - `address-all` — proceed to fix every finding
   - `address-selected` — fix only listed findings
   - `note-as-followup` — create follow-up note (tracker ticket or memory) for later; do not fix now
   - `ignore` — acknowledge and move on

## Important

- Advisor output (native or subagent) is **signal, not decision**. Human approves before any code change.
- `pre-done`'s independence is now **structural** (withheld narrative + adversarial mandate + blind dispatch), not temporal — you no longer need to wait for the bubble to fade; the correlation is broken by construction. (Still fine to `/clear` first if you want.)
- Never modify code inside this skill. It only loads context, escalates, verifies, presents, and asks. Fixes are a separate step taken after user approval.
- Do not commit memory entries or update project docs based on findings — that's a separate capture via skill `core:learn` (or inline write with approval).
- Invocation order in a typical feature track: `pre-plan` (before `superpowers:writing-plans`) → `post-plan` (after plan approval) → `pre-done` (before `core:review-local`).
- **Native advisor vs. this mode:** for a routine second opinion with full context, the native `/advisor` is lighter — Claude calls it on its own. Use grill-me's escalation mode when you need a **guaranteed checkpoint**, **controlled or blind context**, or **citation-verified structured findings**.
