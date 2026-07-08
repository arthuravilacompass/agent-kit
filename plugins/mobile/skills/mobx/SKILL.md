---
name: mobx
description: Invoke to review or write any MobX store/controller (Flutter) — smells the linter doesn't catch, from correctness blockers to aspirational architectural direction. Triggers — "is this observable correct?", "should this state be an enum?", "why doesn't this getter update the UI?", "MobX/DI review".
---

# MobX Skill

Single home for MobX/DI/Architecture knowledge for Flutter. Covers smells the linter doesn't detect — from correctness blockers to aspirational architectural direction.

Part of this catalogue (DI001, ARCH001, LOG001) is mechanically enforced by this same plugin's `hooks/smell-checker.sh` hook (exit 2, add-only) — see `## Enforcement` in `REFERENCE.md`. The rest is on-demand knowledge: consulted by review agents, by the advisor, and by fix recipes. There's no file-glob auto-load: all the content here is read on demand (via the skill description, by a review agent, or by explicit citation).

## Three Documents in This Skill

**`REFERENCE.md`** — On-demand blockers + on-demand STANDARD codes + code policy + `## Enforcement` (what the hook covers vs. what stays prose-only).
Read when: a review agent needs the full signal for a code; you want to understand the tier and the *why* of each rule; or you're reviewing a store/controller from scratch.

**`PATTERNS.md`** — Aspirational patterns (FSM001, SSOT001, CMD001, MOBX006, and the narrative forms "a fallible action returns a sealed result" / "a Coordinator-managed store is pure").
Read when: new code introduces flow state, async results, or multi-observable composition. Never blocks bugfix PRs — these are `non-blocker` and directional guidance.

**`RECIPES.md`** — Canonical migration recipes per smell, with ordered steps and examples.
Read when: a smell-hunter (see `mobile:mobx-smell-hunter` for the 4 aspirational codes) reported a specific code and you need the step-by-step to apply the right fix in the right order.

MOBX004 (observable and getter) → `REFERENCE.md` §MOBX004.
Observer not rebuilding with a nested deferred builder → `REFERENCE.md` §Observer and Deferred Builders.
