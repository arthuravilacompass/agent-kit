---
name: chat-draft
description: Invoque para redigir mensagens informais em pt-BR para Teams/Slack — recap de tech-sync, atualização de squad, ou qualquer pedido rotulado "mensagem para o time / chat / Teams / Slack".
---

Drafts informal pt-BR chat messages. The recurring problem this skill solves: first drafts come back too formal, emoji-heavy, and over-structured for the channel.

## Heurísticas (não template)

- **Tom conversacional.** Como falar com um colega no corredor, não como redigir um memorando. Sem "Prezados" / "Atenciosamente" / "Conforme alinhado".
- **Combine com o thread.** Se a mensagem responde a outra, espelhe o registro do interlocutor (formal → meio-termo; informal → informal direto).
- **Emojis: zero por padrão.** Use só se o thread original já usou, e no mesmo volume. Nunca decoração genérica (✅ 🚀 ⚡ 📌 abrindo seções).
- **Curto por padrão.** Se cabe em 2-3 linhas, fica em 2-3 linhas. Quebra em parágrafos só quando há mais de um tópico distinto.
- **Recap de tech-sync / reunião:** preserve TODOS os itens da pauta original (incluindo pendências da reunião anterior / carry-over). Não consolide nem omita itens "menores".
- **Não invente seções.** Não force "Contexto / Próximos passos / Bloqueios" se não foi pedido. Estrutura emerge do conteúdo, não da forma.
- **Pergunte se faltar input.** Se você não sabe a audiência, o canal (Teams DM vs canal público vs Slack), ou o que precisa ser comunicado — pergunte antes de gerar.

## Amostra de referência (estilo-alvo, recap de tech-sync)

> oi pessoal, recap rápido do tech-sync de hoje:
>
> **Pendências da reunião anterior**
> - [item da semana passada que ficou em aberto]
>
> **Tópicos discutidos**
> - [tópico 1] — [decisão / status em uma linha]
> - [tópico 2] — [decisão / status em uma linha]
>
> **Próximos passos**
> - [responsável] — [ação] até [quando]
>
> qualquer coisa me chamem 👍

(Note como há UM emoji opcional no fim, conversacional — não decorando seções.)

## Quando NÃO usar

- Mensagem formal (cliente externo, RH, jurídico) — peça confirmação do registro antes.
- PR description / commit message — use `core:commit` / `core:pr` (se disponíveis neste kit).
- Documento técnico / ADR — use skill de doc apropriada (`grill-me` para stress-test prévio).
