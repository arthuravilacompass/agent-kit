---
name: grill-me
description: Invoke when the user asks to "grill me" / press on a design decision, or before calling a plan done (interview mode); or at the deterministic checkpoints pre-plan / post-plan / pre-done to escalate to a stronger reviewer with controlled or blind context (escalation mode, e.g., `/core:grill-me pre-done`).
---

# grill-me — relentless interview + checkpoint escalation

One skill, two modes. Mode selection happens in the first lines of the request:

- **No argument** (or a "grill me" / challenge-my-decision request) → **interview mode**.
- **Argument `pre-plan <TICKET> [--greenfield]` | `post-plan` | `pre-done`** → **escalation mode** (absorbs the former escalation-checkpoint skill; same checkpoint semantics).
- Invalid argument → show the usage above and stop.

## Interview mode

Interview me relentlessly about every aspect of this plan until we reach a shared understanding. Walk down each branch of the design tree, resolving dependencies between decisions one-by-one. For each question, provide your recommended answer.

Ask the questions one at a time.

If a question can be answered by exploring the codebase, explore the codebase instead.

For structured interrogation with a formal artifact (Gap Summary) in the tech-breakdown pipeline, see `core:spec-refine` (if available in this kit) instead of this mode.

## Escalation mode

Deterministic escalation to a stronger reviewer at a checkpoint YOU pick — breaks the session's epistemic bubble. Complements Claude Code's native advisor (`/advisor`); does not replace it.

Consumer-project config and prerequisites (advisor model, architecture doc, rule files, ticket source): `REFERENCE.md` in this directory — the skill still runs without them, with less specialized context.

| Mode | Mechanism | When |
|---|---|---|
| `pre-plan <TICKET>` | native advisor (full context) | before choosing an approach; `--greenfield` firewalls the project's rules |
| `post-plan` | native advisor (full context) | plan approved, before coding |
| `pre-done` | blind adversarial subagent (diff + ACs only) | "I think I'm done", before final review |

Inviolable rules of escalation mode:

1. **Propose and stop.** Findings are signal, not decision — present them and ask how to proceed (`address-all` / `address-selected <n,m,...>` / `note-as-followup` / `ignore`). Never apply fixes automatically; never modify code inside this skill.
2. **Confirm before dispatch.** `pre-done` dispatches a subagent — confirm with the user before dispatching whenever the invocation did not come from their explicit command.
3. **The checkpoint is never skipped.** With no advisor configured, fall back to an equivalent subagent (full context for `pre-plan`/`post-plan`) and disclose the substitution.
4. **Narrative withheld in `pre-done`.** The blind subagent gets only diff + ACs + rule-file paths — never the plan, the commits, or the session's rationale.

Full mechanics (per-mode context loading, framings, findings schema, citation verification, presentation format): `REFERENCE.md` in this directory.
