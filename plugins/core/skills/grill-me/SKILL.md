---
name: grill-me
description: Invoke when the user asks to "grill me" / press on a design decision, or before calling a plan done (interview mode); or at the deterministic checkpoints pre-plan / post-plan / pre-done to escalate to a stronger reviewer with controlled or blind context (escalation mode, e.g., `/core:grill-me pre-done`).
---

# grill-me — relentless interview + checkpoint escalation

One skill, two modes. Mode selection happens in the first lines of the request:

- **No argument** (or a "grill me" / challenge-my-decision request) → **interview mode**.
- **Argument `pre-plan <TICKET> [--greenfield]` | `post-plan` | `pre-done`** → **escalation mode** (absorbs the former escalation-checkpoint skill; same checkpoint semantics).
- **Route by object, not by phrasing**: escalation reviews *work artifacts* (a plan, a diff, a deliverable). When the material to press on is **operator knowledge** — their intent, domain facts, a decision they own — route to **interview mode** even if the request arrived sounding like a checkpoint: interrogate the operator; don't dispatch a reviewer at what only they know. The converse binds just as hard: when a question's answer sits in the environment — a file, a config, a command's output, a frontmatter field — it is not operator knowledge, and putting it to them as a question is a dispatch that did not happen. Go find it. What only they can settle is intent, preference, and a decision whose cost they carry; everything else is a read.
- Invalid argument → show the usage above and stop.

## Interview mode

> Follows Matt Pocock's "grill me" prompt pattern (`mattpocock/skills`).

Interview me relentlessly about every aspect of this plan until we reach a shared understanding. Walk down each branch of the design tree, resolving dependencies between decisions one-by-one. For each question, provide your recommended answer.

Ask the questions one at a time.

If a question can be answered by exploring the codebase, explore the codebase instead.

Interview mode interrogates a specific decision without producing an artifact — inside a design flow, use `superpowers:brainstorming` instead.

## Escalation mode

Deterministic escalation to a stronger reviewer at a checkpoint YOU pick — breaks the session's epistemic bubble. Complements Claude Code's native advisor (`/advisor`); does not replace it.

Consumer-project config and prerequisites (advisor model, architecture doc, rule files, ticket source) and the mode comparison table (mechanism, checkpoint, when to use each): `REFERENCE.md` in this directory — the skill still runs without the config, with less specialized context.

Inviolable rules of escalation mode:

1. **Propose and stop.** Findings are signal, not decision — present them and ask how to proceed (`address-all` / `address-selected <n,m,...>` / `note-as-followup` / `ignore`). Never apply fixes automatically; never modify code inside this skill.
2. **Confirm before dispatch.** `pre-done` dispatches a subagent — confirm with the user before dispatching whenever the invocation did not come from their explicit command.
3. **The checkpoint is never skipped.** With no advisor configured, fall back to an equivalent subagent (full context for `pre-plan`/`post-plan`) and disclose the substitution.
4. **Narrative withheld in `pre-done`.** The blind subagent gets the diff, the ACs, the rule-file paths, and the plan's `session-settled:` Key Decision entries if it carries any — that last one is the decision *contract*, same epistemic class as the ACs, not the author's narrative. Never the plan itself, the commits, or the session's rationale. It must read cited files with Read/Grep, never Bash, or its citations fail the gate (`REFERENCE.md` step 3).

Full mechanics (per-mode context loading, framings, findings schema, citation verification, presentation format): `REFERENCE.md` in this directory.
