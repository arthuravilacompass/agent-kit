# agent-kit

> Consultor em rotação não pode recomeçar a disciplina do zero a cada cliente. O agent-kit é a memória executável dessa disciplina: toda regra aqui nasceu de um erro real, virou mecanismo quando texto falhou, e só continua carregada enquanto provar uso. Correções de um projeto viram enforcement portável pro próximo.

Dois plugins de Claude Code, instaláveis como marketplace local: **`core`** (metodologia de engenharia e disciplina epistêmica, qualquer stack) e **`mobile`** (toolkit Flutter/Dart, pressupõe `core`). Zero conteúdo do projeto de origem — um gate mecânico garante isso.

## Quickstart — 60 segundos

```bash
claude plugin marketplace add "$HOME/dev/agent-kit"
claude plugin install core@agent-kit
claude plugin install mobile@agent-kit   # só em projeto Flutter/Dart
```

Rode de dentro do projeto onde o kit deve ficar ativo. Abra uma sessão e jogue uma tarefa crua, sem estruturar:

> preciso investigar por que o deeplink X quebra no Android

O `core:pipeline` detecta o estágio real da tarefa, classifica a intenção e conduz pelas skills do kit — um estágio por vez. Esse é o primeiro valor; o resto do kit (hooks determinísticos, posturas epistêmicas, fluxos de entrega) entra em cena conforme o trabalho pede.

Para atualizar depois de um novo commit no kit: `claude plugin update core@agent-kit` (e/ou `mobile@agent-kit`) — reinício de sessão necessário.

*Inventário completo do que cada plugin carrega (skills, agents, hooks, scripts, MCP): [INVENTORY.md](INVENTORY.md) — gerado por script, verificado no gate. Operação do dono (publicação, permissões, gate): [docs/OPERATIONS.md](docs/OPERATIONS.md).*

## O que cada plugin carrega

- **`core`** — metodologia de engenharia com agentes: regras epistêmicas sempre-ativas (research-depth, evidência antes de claim, scope discipline), condutor de fluxo (`core:pipeline`), fluxos de entrega (commit, PR, review, breakdown técnico, refinamento de spec), Conselho de Posturas (lentes epistêmicas in-thread e em subagente isolado) e hooks determinísticos (auto-aprovação de leitura, guarda de diretório, injeção de escopo, ledger de citação).
- **`mobile`** — toolkit Flutter/MobX: review de código mobile, condução de app via MCP, scaffold de feature, debug de deeplink, validação de tracking, padrões de performance, smells de MobX/DI/arquitetura com bloqueio determinístico dos casos de correctness. Os MCP servers registrados são só os genéricos de toolchain (`dart`, `marionette`) — nenhum server de backend/projeto: portabilidade entre projetos consumidores é o critério.

`core` não depende de `mobile` e serve qualquer stack. `mobile` pressupõe `core` instalado e só é útil em projetos Flutter/Dart.

Alguns fluxos do `core` referenciam skills do marketplace `superpowers` (brainstorming, writing-plans, systematic-debugging, executing-plans). Sem ele instalado nada quebra: `core:pipeline` indica o fallback interno equivalente de cada estágio.

## `unwired/`

`unwired/` não é um plugin — nada dele é carregado, custo de contexto zero. É matéria-prima genericizada aguardando prova de uso real. Todo artefato do kit está em exatamente um de três estados: **wired** (`plugins/`, custa contexto), **unwired** (custo zero) ou **deletado** — nunca "testado mas não ligado". A regra de promoção e o detalhe por item: [unwired/README.md](unwired/README.md).

## Assets manuais (`assets/`)

Templates que você copia e adapta à mão — nada aqui é carregado automaticamente:

- **`statusline-command.sh`** — status line (modelo, contexto, rate limits, branch). Copiar pra um path estável, `chmod +x`, apontar em `settings.json` (`statusLine.command`). Requer `jq`.
- **`claude-md-starter.md`** — esqueleto de `CLAUDE.md` pro projeto consumidor; princípio-guia "ponteiro, não conteúdo inline".
- **`settings-snippets.md`** — trechos de `settings.json`: sandbox Flutter e deny-list de edição em arquivo gerado por codegen.

## Princípios

- **Estado único por artefato** — wired, unwired ou deletado; nunca uma quarta categoria fantasma.
- **Advisory-nudge não entra em `plugins/` sem medição** — mecanismo só-lembrete precisa provar conversão real antes de ser wired; caso concreto em [unwired/README.md](unwired/README.md).
- **Documentação nasce do que morde** — toda regra carrega um `Sinal` (como detectar a violação) e um `Failure mode` (o que quebra rio abaixo). Regra textual que falha repetido vira mecanismo (hook, gate, schema), não mais texto.
- **Zero conteúdo do projeto de origem, inclusive em `unwired/`** — gate mecânico (`scripts/check-provenance.sh`) roda sobre o repo inteiro, sem exceção.

---

Referência gerada: [INVENTORY.md](INVENTORY.md) · Operação do dono: [docs/OPERATIONS.md](docs/OPERATIONS.md) · Histórico: [CHANGELOG.md](CHANGELOG.md)
