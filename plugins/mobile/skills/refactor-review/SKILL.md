---
name: refactor-review
description: Invoke before committing a refactor that touches shared stores/repositories/coordinators or navigation — 2-phase protocol (regression + quality). Triggers — "review this refactor before I commit", "confirm this refactor didn't break anything", "post-refactor checklist".
---

# Refactor Review

Two phases. Detailed checklists in `CHECKLIST.md` (same folder) — read before running each phase.

## Phase 1 — Regression Analysis

Read `CHECKLIST.md` §§1.1–1.7. Apply each dimension to `git diff --cached` (or `git diff`). Report findings per dimension. Explicitly state "No issues found" for clean dimensions — don't skip any.

## Phase 2 — Code Quality

Read `CHECKLIST.md` §§2.1–2.8. Run `/simplify`, `mobile:code-review-mobile`, and where fragility is flagged, trace the touchpoints manually.

## Output

Use the template at the end of `CHECKLIST.md`.

## After This Skill

1. `/superpowers:verification-before-completion` (or your setup's equivalent)
2. `mobile:code-review-mobile` (skip if already done in Phase 2 with no new changes)
3. If your project has a design tokens system with its own usage rules, check conformance now
4. Your setup's commit/PR flow (e.g. `core:commit` → `gh`/native for the PR)
