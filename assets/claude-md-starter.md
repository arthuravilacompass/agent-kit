# claude-md-starter.md — esqueleto de CLAUDE.md

Este arquivo não é lido pelo Claude Code — é um template. Copie o corpo abaixo (a partir de `# CLAUDE.md`) para o `CLAUDE.md` do projeto consumidor e preencha os placeholders (`<...>`). A estrutura vem de um `CLAUDE.md` real, mas todo conteúdo específico de domínio/empresa foi removido — o que sobra é a *forma*: que seções existem, o que cada uma deve conter, e o princípio-guia de "ponteiro, não conteúdo inline".

## Princípio-guia: ponteiro, não conteúdo inline

O `CLAUDE.md` raiz é a coisa mais cara em custo de contexto do projeto — ele carrega toda sessão. Regra de ouro: se o conteúdo é longo o bastante pra merecer sua própria seção com exemplos, ele vive num doc/skill/rule separado e o `CLAUDE.md` só aponta pra lá (`ver arquivo.md §Seção`). O que fica inline é o que precisa estar sempre disponível em uma frase — identidade do projeto, convenções de uma linha, e os ponteiros em si.

---

## Corpo do template

```markdown
# CLAUDE.md

## Project Identity

**<Nome do Projeto>** é <uma frase: o que o produto é e pra quem>.

- **<Eixo de variação 1, ex. plataformas/marcas suportadas>**: <lista>
- **<Eixo de variação 2, ex. idiomas>**: <lista>
- **Integrações principais**: <lista curta — analytics, crash reporting, pagamento, etc.>

---

## Architecture

<1-2 frases: camadas/padrão arquitetural de alto nível>. Diagrama completo e catálogo de módulos: `<path>/CLAUDE.md` §Architecture.

<Ponteiros para onde vivem as decisões estruturais — setup de ambiente, convenção de módulo, etc. — não o conteúdo em si.>

---

## Key Patterns

<3-6 padrões-chave do projeto, uma linha cada, formato "Nome: descrição curta + onde ver mais se precisar de detalhe.">

**<Padrão 1, ex. Optimistic updates>:** <descrição de uma linha>. Ver `<referência>`.

**<Padrão 2, ex. Navegação>:** <descrição de uma linha>.

**<Padrão 3, ex. Error handling>:** <descrição de uma linha>.

**<Padrão 4, ex. L10n>:** <descrição de uma linha>.

**<Padrão 5, ex. Design system>:** <regra objetiva e verificável — ex. "todo valor visual vem de `<TokenSystem>.*`, nunca hardcode">.

**Code review:** <convenção do time para comentários de review — prefixos, idioma, onde documentar o checklist>.

**Advisor checkpoints:** <se o projeto usa checkpoints de escalada a um reviewer mais forte (pre-plan/post-plan/pre-done ou equivalente), documente aqui em uma linha + ponteiro pro mecanismo>.

---

## Language

- Code, identificadores, mensagens de commit → **<idioma>** (modo imperativo).
- Descrições de PR, comentários de review, docs de projeto → **<idioma>**.

---

## Model Strategy

- **<Modelo A>** — <quando usar: ex. síntese, crítica estrutural, brainstorm, decisões de arquitetura>.
- **<Modelo B>** — <quando usar: ex. execução — código, fixes, reviews, investigação>.
- **<Modelo C>** — <quando usar: ex. fallback e planning longo de custo menor>.
- Use `/clear` entre tarefas independentes.

---

> **Guia prático**: `<path para o manual do operador>` · Commands: `<path>` · Rules: `<path>` · Skills: `<path>` · **Mapa do toolkit**: `<path>`
```

---

## Como preencher

1. **Project Identity** — não pule mesmo em projeto pequeno; é o que ancora todo o resto. Uma frase de propósito + os eixos de variação reais (não invente categoria que o projeto não tem).
2. **Architecture** — se o projeto já tem um doc de arquitetura, este bloco é só o ponteiro + 1-2 frases de orientação. Não duplique o diagrama aqui.
3. **Key Patterns** — cada linha deve ser verificável (alguém consegue checar se foi seguida olhando o diff), não um conselho vago. Se o padrão precisar de exemplo de código, ele vive numa skill/rule, não aqui.
4. **Language** — só vale a pena declarar se o projeto realmente mistura idiomas (código em inglês, comunicação em outro idioma, etc.); se for tudo no mesmo idioma, remova a seção.
5. **Model Strategy** — nomeie os modelos reais que o time usa e o critério de quando trocar; não copie uma estratégia de três modelos se o projeto só usa um.
6. **Advisor checkpoints** — só inclua se o projeto tiver de fato um mecanismo de escalada (subagent cego, reviewer externo, etc.); não descreva um mecanismo aspiracional que ainda não existe.
7. **Rodapé de ponteiros** — a última linha do arquivo deve linkar pra tudo que tem profundidade própria (guia operacional, commands, rules, skills). Se o projeto ainda não tem esses artefatos, não coloque o link — crie a seção quando o artefato existir.
