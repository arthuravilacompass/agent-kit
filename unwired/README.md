# unwired/ — material genericizável sem uso comprovado

Este diretório não é um plugin. Nada aqui é carregado pelo Claude Code — custo de contexto zero. É matéria-prima: coisas que existiram e funcionaram em algum grau num projeto de origem, escrutinadas o bastante pra virar referência, mas sem uso real comprovado *neste* kit para justificar viver em `plugins/`.

## O modelo (D10): wired / unwired / deletado

Todo artefato que já existiu neste kit está num destes três estados, nunca em limbo:

- **wired** — vive em `plugins/core/` ou `plugins/mobile/`. Foi admitido porque tem uso real comprovado (não só "parecia bom"). Custa contexto toda sessão que carrega o plugin.
- **unwired** — vive aqui. Genericizável, scrub mecânico aplicado, mas sem prova de uso no novo projeto. Custo de contexto **zero** — só é lido se alguém abrir o arquivo.
- **deletado** — não existe no repo. Foi avaliado e descartado (vestigial, TF-específico demais pra genericizar, ou substituído por outra coisa melhor).

Nunca "testado mas não ligado" — essa terceira categoria fantasma é o que este modelo existe para eliminar.

## Regra de promoção

**Um item sobe de `unwired/` para `plugins/` (wired) quando tiver uso real comprovado no projeto novo — o mesmo critério de admissão que qualquer skill/agent/hook novo teria.** Não é "parece útil" nem "era usado no projeto de origem" — é: você invocou isso pelo menos uma vez no projeto novo, funcionou, e quer que sobreviva ao próximo `/clear`.

Ao promover:
1. **Reescreva a `description`** com o gatilho específico do novo contexto — a description arquivada carrega vocabulário/gatilho do projeto de origem (às vezes já genérico, às vezes não).
2. **Preencha os placeholders de proveniência** (`<TICKET>`, `<DesignTokens>`, `<BOARD_NAME>`, nomes de componente entre `<>`) com os nomes reais do projeto novo. O scrub que colocou o item aqui foi mecânico, não uma reescrita — o trabalho de reancorar no domínio novo é seu, não deste kit.
3. **Mova o arquivo** para `plugins/<core|mobile|novo-plugin>/` na estrutura padrão (skills em `skills/<nome>/SKILL.md`, agents em `agents/<nome>.md`, etc.) e rode `claude plugin validate .`.
4. **Delete a cópia em `unwired/`** — um item promovido não fica duplicado nos dois estados.

## O que tem aqui e por quê

| Pasta | Origem | Por que não é wired |
|---|---|---|
| `council/`, `posturas/` (bohr, sagan), `agents/` (maxwell, zeno, epistemic-council) | Conselho de Posturas de um projeto de origem | Duas posturas (Schrödinger, Epicurus) já provaram uso real e estão em `plugins/core/skills/`; o resto do aparato (índice, memória episódica, posturas restantes, subagents isolados) não tinha essa prova neste kit. |
| `ui-comparison/` | Skill de fidelidade visual de um projeto de origem | O método (fases, rubrica de score) é genérico; sem design system real pra testar contra, não tinha como comprovar uso aqui. `figma-to-component` (que vivia neste mesmo par) foi promovido em 2026-07-07 — ver `plugins/mobile/skills/figma-to-component/` (foi pra `mobile`, não `core`, por ser Flutter-only). |
| `learning-pulse/` | Metade "nudge" de um hook de duplo propósito | A outra metade (debounce de scope-injection) foi resolvida de outra forma no `scope-inject.sh` de `plugins/core` — não sobrevive. A metade advisory (lembrete a cada N mensagens) **mediu ~0 conversão em uso real** no projeto de origem e foi removida de lá por essa razão. Só volta a ser wired com medição nova que sustente o custo do lembrete — não por achar a ideia boa de novo. |
| `handoff-gate/` | Stop hook que fecha o loop alerta→ação do context-monitor | Originalmente DELETADO na extração ("órfão nunca registrado — peso morto com aparência de vivo": tinha evals passando sem nunca ter sido wired em settings algum). Resgatado pra unwired na rodada de revisão pós-construção (2026-07-06): o censo cego avaliou o mérito do mecanismo de forma independente (4/5) e, com o fim do clone do projeto de origem, deletado significava perda definitiva. O critério de promoção não muda: só sobe com uso real; o header do script lista o checklist (registrar no Stop, migrar state pra `${CLAUDE_PLUGIN_DATA}`, recriar evals). |
| `WORKFLOW.md` | Manual do operador de um projeto de origem | Genericizado (nomes de skill atualizados pro vocabulário deste kit onde há equivalente; lacunas marcadas onde não há). Fica em unwired porque é referência/inspiração pro README real de `plugins/`, não um documento que o Claude Code carrega. |

## O que NÃO está aqui

- Conteúdo específico do domínio/empresa de origem — a mesma denylist de `scripts/check-provenance.sh` que gate o resto do repo cobre `unwired/`. Além da denylist mecânica, cada arquivo aqui passou por uma checagem de proveniência (paths internos reais, nomes de classe/módulo verbatim, IDs de ticket/investigação reais) — não só grep por string de marca.
- Duplicação de algo já wired (Schrödinger e Epicurus, por exemplo, não estão aqui — estão só em `plugins/core/skills/`).
