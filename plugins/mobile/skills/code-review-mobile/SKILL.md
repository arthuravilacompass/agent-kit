---
name: code-review-mobile
description: Invoke to review a Flutter PR/diff — universal Layer 1 checklist (17 items, always) + contextual Layer 2 (UI, Observer, lists, l10n, navigation, tests) + module/component structure reference. Triggers — "review this Flutter PR", "mobile review checklist", "where should this widget/store live".
---

# Code Review Mobile — Single Home for Flutter Review

This skill is the single home for generic Flutter/MobX review knowledge (stack: Flutter + MobX + get_it/injectable + go_router + dartz `Either`). Companions in the same folder:

| Companion | Content |
|---|---|
| `CHECKLIST.md` | Verification discipline + workflow + Layer 1 (17 items) + comment prefixes + Layer 2 (items 18–50) |
| `STRUCTURE.md` | Module/component structure: folder layout, naming, barrel files, widget extraction, modal sheets, import org, formatting |
| `STANDARDS.md` | STANDARD codes in prose (team agreements — generic, adapt to your project's convention) |
| `COOKBOOK.md` | Canonical examples (DI, navigation, testing, Either pattern, security checklist, page template) |

## Project Config

This skill assumes the Flutter + MobX + `get_it`/`injectable` + `go_router` + `dartz` (`Either`) stack — swap the examples if your project uses a different state-management/DI/navigation stack. It also assumes the project defines:
- Its own **design tokens system** (if any) — Layer 2 items that mention "visual tokens" point to your design system's config, not to a specific one.
- **Supported locales** (if the app is multi-language) — l10n items assume you fill in the real list.
- **Base branch** for `git diff` (suggested default: `main`).

## Layer 1 + Workflow

Read `CHECKLIST.md` §Layer 1 for the universal 17-item checklist, PR workflow, and comment prefixes (`blocker:` / `non-blocker:`). Apply before Layer 2.

## Layer 2 — Contextual Checks

Read `CHECKLIST.md` §Layer 2 (items 18–50). Apply only when the trigger condition in the "When" column is present in the diff.

## Standards Reference

Read `STANDARDS.md` when the check involves any STANDARD-tier code — team agreements that are usually worth adopting, but aren't universal like Layer 1.

Read `CHECKLIST.md` §Standards when the check involves: Dart language patterns (late, final, switch expressions, records, sealed classes), widget keys, race condition patterns, or navigation guards.

## Component Structure Reference

Read `STRUCTURE.md` when the check involves: module folder layout, naming conventions, barrel files, widget extraction rules, modal bottom sheets, import organization, or formatting.

## Canonical Examples

Read `COOKBOOK.md` for DI, navigation, testing patterns, Either pattern, security checklist, and page template.

## After This Skill

1. `/superpowers:verification-before-completion` (or your setup's equivalent)
2. `mobile:refactor-review` if the change is a refactor
