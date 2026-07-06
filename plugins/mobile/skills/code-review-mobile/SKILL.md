---
name: code-review-mobile
description: Invoque para revisar um PR/diff Flutter — checklist universal Camada 1 (17 itens, sempre) + Camada 2 contextual (UI, Observer, listas, l10n, navegação, testes) + referência de estrutura de módulo/componente. Gatilhos em pt-BR — "revisa esse PR Flutter", "checklist de review mobile", "onde devia ficar esse widget/store".
---

# Code Review Mobile — Casa Única de Review Flutter

Este skill é a casa única do conhecimento de review Flutter/MobX genérico (stack: Flutter + MobX + get_it/injectable + go_router + dartz `Either`). Companions na mesma pasta:

| Companion | Conteúdo |
|---|---|
| `CHECKLIST.md` | Verification discipline + workflow + Camada 1 (17 itens) + prefixos de comentário + Camada 2 (itens 18–50) |
| `STRUCTURE.md` | Estrutura de módulo/componente: folder layout, naming, barrel files, widget extraction, modal sheets, import org, formatting |
| `STANDARDS.md` | STANDARD codes em prosa (acordos de time — genéricos, adapte à convenção do seu projeto) |
| `COOKBOOK.md` | Exemplos canônicos (DI, navegação, testing, Either pattern, security checklist, page template) |

## Config do projeto

Este skill assume o stack Flutter + MobX + `get_it`/`injectable` + `go_router` + `dartz` (`Either`) — troque os exemplos se seu projeto usar outro state-management/DI/navigation stack. Assume também que o projeto define:
- **Sistema de design tokens** próprio (se houver) — os itens de Camada 2 que mencionam "tokens visuais" apontam para a config do seu design system, não para um específico.
- **Locales suportadas** (se o app for multi-idioma) — os itens de l10n assumem que você preenche a lista real.
- **Branch base** para `git diff` (default sugerido: `main`).

## Camada 1 + Workflow

Read `CHECKLIST.md` §Camada 1 for the universal 17-item checklist, PR workflow, and comment prefixes (`blocker:` / `non-blocker:`). Apply before Camada 2.

## Camada 2 — Contextual Checks

Read `CHECKLIST.md` §Camada 2 (items 18–50). Apply only when the trigger condition in the "Quando" column is present in the diff.

## Standards Reference

Read `STANDARDS.md` when the check involves any STANDARD-tier code — acordos de time que geralmente valem a pena adotar, mas não são universais como Camada 1.

Read `CHECKLIST.md` §Standards when the check involves: Dart language patterns (late, final, switch expressions, records, sealed classes), widget keys, race condition patterns, or navigation guards.

## Component Structure Reference

Read `STRUCTURE.md` when the check involves: module folder layout, naming conventions, barrel files, widget extraction rules, modal bottom sheets, import organization, or formatting.

## Exemplos Canônicos

Read `COOKBOOK.md` for DI, navigation, testing patterns, Either pattern, security checklist, and page template.

## After This Skill

1. `/superpowers:verification-before-completion` (ou o equivalente do seu setup)
2. `mobile:refactor-review` se a mudança for um refactor
