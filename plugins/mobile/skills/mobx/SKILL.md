---
name: mobx
description: Invoque para revisar ou escrever qualquer store/controller MobX (Flutter) — smells que o linter não pega, do correctness blocker à direção arquitetural aspiracional. Gatilhos em pt-BR — "esse observable está certo?", "esse estado deveria ser enum?", "por que esse getter não atualiza a UI?", "revisão de MobX/DI".
---

# MobX Skill

Casa única do conhecimento MobX/DI/Architecture para Flutter. Cobre smells que o linter não detecta — desde correctness blockers até direção arquitetural aspiracional.

Parte deste catálogo (DI001, ARCH001, LOG001) é enforced mecanicamente pelo hook `hooks/smell-checker.sh` deste mesmo plugin (exit 2, add-only) — ver `## Enforcement` em `REFERENCE.md`. O resto é conhecimento on-demand: consultado por review agents, pelo advisor, e por receitas de fix. Não há auto-load por glob de arquivo: todo o conteúdo aqui é lido sob demanda (pela skill description, por um agente de review, ou por citação explícita).

## Três documentos nesta skill

**`REFERENCE.md`** — Blockers on-demand + STANDARD codes on-demand + política de codes + `## Enforcement` (o que o hook cobre vs. o que fica só em prosa).
Leia quando: review agent precisa de sinal completo para um code; você quer entender o tier e o *por quê* de cada regra; ou vai revisar um store/controller do zero.

**`PATTERNS.md`** — Padrões aspiracionais (FSM001, SSOT001, CMD001, MOBX006, e as formas narrativas de "ação falível retorna sealed result" / "store gerenciada por Coordinator é pura").
Leia quando: código novo introduz flow state, async results, ou multi-observable composition. Nunca bloqueia PRs de bugfix — são `non-blocker` e orientação de direção.

**`RECIPES.md`** — Receitas canônicas de migração por smell, com steps ordenados e exemplos.
Leia quando: um smell-hunter (ver `mobile:mobx-smell-hunter` para os 4 codes aspiracionais) reportou um code específico e você precisa do passo-a-passo para aplicar o fix correto na ordem certa.

MOBX004 (observable e getter) → `REFERENCE.md` §MOBX004.
Observer que não rebuilda com builder deferido aninhado → `REFERENCE.md` §Observer e builders deferidos.
