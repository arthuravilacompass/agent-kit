---
name: mobx
description: Invoque para revisar ou escrever qualquer store/controller MobX (Flutter) — smells que o linter não pega, do correctness blocker à direção arquitetural aspiracional. Gatilhos em pt-BR — "esse observable está certo?", "esse estado deveria ser enum?", "por que esse getter não atualiza a UI?", "revisão de MobX/DI".
---

# MobX Skill

Casa única do conhecimento MobX/DI/Architecture para Flutter. Cobre smells que o linter não detecta — desde correctness blockers até direção arquitetural aspiracional.

Parte deste catálogo (DI001, ARCH001, LOG001) é enforced mecanicamente pelo hook `hooks/smell-checker.sh` deste mesmo plugin (exit 2, add-only) — ver `## Enforcement` em `REFERENCE.md`. O resto é conhecimento on-demand: consultado por review agents, pelo advisor, e por receitas de fix. Diferente do setup original de onde este skill foi portado, este plugin não tem um mecanismo de auto-load-por-glob de arquivo — todo o conteúdo aqui é lido sob demanda (pela skill description, por um agente de review, ou por citação explícita).

## Três documentos nesta skill

**`REFERENCE.md`** — Blockers on-demand + STANDARD codes on-demand + política de codes + `## Enforcement` (o que o hook cobre vs. o que fica só em prosa).
Leia quando: review agent precisa de sinal completo para um code; você quer entender o tier e o *por quê* de cada regra; ou vai revisar um store/controller do zero.

**`PATTERNS.md`** — Padrões aspiracionais (FSM001, SSOT001, CMD001, MOBX006, e as formas narrativas de "ação falível retorna sealed result" / "store gerenciada por Coordinator é pura").
Leia quando: código novo introduz flow state, async results, ou multi-observable composition. Nunca bloqueia PRs de bugfix — são `non-blocker` e orientação de direção.

**`RECIPES.md`** — Receitas canônicas de migração por smell, com steps ordenados e exemplos.
Leia quando: um smell-hunter (ver `mobile:mobx-smell-hunter` para os 4 codes aspiracionais) reportou um code específico e você precisa do passo-a-passo para aplicar o fix correto na ordem certa.

## Correção registrada — MOBX004

O code MOBX004 ("`@observable` deve ser privado + getter") foi reconciliado com a prática medida em um projeto real: a formulação original tratava *todo* `@observable` público como violação 🔴, mas 61% dos observables medidos em stores reais eram públicos e reativamente corretos (mobx_codegen gera o accessor via mixin — público não quebra tracking). O alvo real do code é um **getter manual que bypassa o mixin** (`Type get x => _x;` sobre um `_x` que deveria estar exposto apenas pelo `with _$Store`), não a visibilidade do campo em si. Ver a formulação corrigida em `REFERENCE.md` §MOBX004.

## Referência técnica — Observer e builders deferidos

`Observer` (flutter_mobx) só rastreia observables lidos **sincronamente dentro do seu próprio `builder`**. Reads dentro de um builder deferido aninhado — `ListenableBuilder`, `Builder`, `LayoutBuilder`, `AnimatedBuilder`, `FutureBuilder`, `ValueListenableBuilder`, `StreamBuilder` — não são rastreados: essa closure roda fora do `reaction.track()` do Observer.

**Sintoma**: o widget só reage ao que é lido direto no builder do Observer; estado que muda depois (ex.: assíncrono) não dispara rebuild.

**Fix**: inverta o aninhamento — o builder deferido por fora, o `Observer` por dentro envolvendo a subtree. É mais robusto que hoistar cada read manualmente pro builder do Observer, porque não depende de lembrar disso a cada novo read introduzido depois.
