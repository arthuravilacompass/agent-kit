---
name: chat-draft
description: Invoke to draft informal pt-BR chat messages for Teams/Slack — recap of a tech-sync, squad update, or any request labeled "message for the team / chat / Teams / Slack".
---

Drafts informal pt-BR chat messages. The recurring problem this skill solves: first drafts come back too formal, emoji-heavy, and over-structured for the channel.

## Heuristics (not a template)

- **Conversational tone.** Like talking to a colleague in the hallway, not drafting a memo. No "Prezados" / "Atenciosamente" / "Conforme alinhado".
- **Match the thread.** If the message replies to another, mirror the other party's register (formal → middle ground; informal → informal, direct).
- **Emojis: zero by default.** Use only if the original thread already did, and at the same volume. Never generic decoration (✅ 🚀 ⚡ 📌 opening sections).
- **Short by default.** If it fits in 2-3 lines, keep it at 2-3 lines. Break into paragraphs only when there's more than one distinct topic.
- **Tech-sync / meeting recap:** preserve ALL items from the original agenda (including carry-over items from the previous meeting). Don't consolidate or omit "minor" items.
- **Don't invent sections.** Don't force "Context / Next steps / Blockers" if it wasn't asked for. Structure emerges from the content, not from the form.
- **Ask if input is missing.** If you don't know the audience, the channel (Teams DM vs. public channel vs. Slack), or what needs to be communicated — ask before generating.

## Reference sample (target style, tech-sync recap)

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

(Note there's ONE optional emoji at the end, conversational — not decorating sections.)

## When NOT to use

- Formal message (external client, HR, legal) — ask for register confirmation first.
- PR description / commit message — use `core:commit` (if available) / `gh`/native for the PR.
- Technical document / ADR — use the appropriate doc skill (`grill-me` for a prior stress-test).
