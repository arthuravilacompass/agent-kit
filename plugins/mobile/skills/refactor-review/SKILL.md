---
name: refactor-review
description: Invoque antes de commitar um refactor que toca stores/repositories/coordinators compartilhados ou navegação — protocolo de 2 fases (regressão + qualidade). Gatilhos em pt-BR — "revisa esse refactor antes de eu commitar", "confirma que esse refactor não quebrou nada", "checklist pós-refactor".
---

# Refactor Review

Duas fases. Checklists detalhados em `CHECKLIST.md` (mesma pasta) — leia antes de executar cada fase.

## Fase 1 — Regression Analysis

Leia `CHECKLIST.md` §§1.1–1.7. Aplique cada dimensão em `git diff --cached` (ou `git diff`). Reporte findings por dimensão. Declare "No issues found" explicitamente pra dimensões limpas — não pule nenhuma.

## Fase 2 — Code Quality

Leia `CHECKLIST.md` §§2.1–2.8. Rode `/simplify`, `mobile:code-review-mobile`, e onde fragilidade for sinalizada, trace os touchpoints manualmente.

## Output

Use o template no fim de `CHECKLIST.md`.

## After This Skill

1. `/superpowers:verification-before-completion` (ou o equivalente do seu setup)
2. `mobile:code-review-mobile` (pule se já foi feito na Fase 2 sem mudanças novas)
3. Se seu projeto tem um sistema de design tokens com regras de uso próprias, confira conformidade agora
4. Fluxo de commit/PR do seu setup (ex.: `core:commit` → `core:pr`)
