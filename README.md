# agent-kit

Marketplace pessoal de plugins do Claude Code: metodologia de engenharia, disciplina epistêmica e toolkit mobile — extraídos de uso real, genericizados, e organizados para reaplicar em qualquer projeto novo sem carregar nada específico do domínio/empresa de origem.

Dois plugins:

- **`core`** — metodologia de engenharia com agentes: epistemologia (research-depth, evidência antes de claim, scope discipline, bugfix principles), fluxo de trabalho (commit, PR, review, breakdown técnico, refinamento de spec), hooks determinísticos (auto-aprovação de leitura, guarda de diretório, injeção de escopo, ledger de citação).
- **`mobile`** — toolkit pessoal para desenvolvimento Flutter/MobX: review de código, condução de app via MCP, scaffold de feature, debug de deeplink, validação de tracking GA4, padrões de performance, smells de MobX/DI/arquitetura.

`core` não depende de `mobile` e serve qualquer stack. `mobile` pressupõe `core` instalado (usa as mesmas convenções de skill/hook) e só é útil em projetos Flutter/Dart.

Alguns fluxos do `core` referenciam skills do marketplace `superpowers` (brainstorming, writing-plans, systematic-debugging, executing-plans). Sem ele instalado nada quebra: `core:pipeline` indica o fallback interno equivalente de cada estágio (grill-me, tech-breakdown, schrodinger, execução direta com gate).

---

## Instalação

### Agora — marketplace local (sem depender do GitHub)

Funciona hoje, direto do clone local, sem publicar nada:

```bash
claude plugin marketplace add "$HOME/dev/agent-kit"
claude plugin install core@agent-kit
claude plugin install mobile@agent-kit   # só em projeto Flutter/Dart
```

Rode os comandos acima de dentro do projeto onde você quer o kit ativo (ou adicione `enabledPlugins` no `settings.json` do projeto/usuário). Para atualizar depois de um novo commit no kit: `claude plugin update core@agent-kit` (e/ou `mobile@agent-kit`) — reinício da sessão necessário para aplicar.

### GitHub

Para publicar (privado ou não), o dono roda a partir de `$HOME/dev/agent-kit`:

```bash
git remote add origin git@github.com:<usuario>/agent-kit.git
git push -u origin main --tags
```

E os consumidores trocam a marketplace local por uma `extraKnownMarketplaces` apontando pro GitHub, no `settings.json` (projeto ou usuário):

```json
{
  "extraKnownMarketplaces": {
    "agent-kit": {
      "source": { "source": "github", "repo": "<usuario>/agent-kit" }
    }
  }
}
```

```bash
claude plugin marketplace add <usuario>/agent-kit
claude plugin install core@agent-kit
claude plugin install mobile@agent-kit
```

A marketplace local continua funcionando como caminho de desenvolvimento mesmo com o remote publicado — o fonte em `$HOME/dev/agent-kit` é onde se edita; o GitHub é distribuição.

---

## Mapa wired — `plugins/core`

Tudo abaixo é carregado pelo Claude Code assim que o plugin está habilitado (skills sob demanda pela `description`; hooks e o agent sempre presentes).

**Skills (21)** — `plugins/core/skills/<nome>/SKILL.md`. 8 são invocáveis pelo modelo via tool Skill (`chat-draft`, `epicurus`, `grill-me`, `learn`, `methodology`, `pipeline`, `schrodinger`, `using-agent-kit`); as outras 13 têm `disable-model-invocation: true` no frontmatter — só rodam via slash command explícito (`/core:commit`, `/core:archaeology`, etc.), nunca por iniciativa do modelo:

| Skill | Para quê |
|---|---|
| `using-agent-kit` | sempre-ativo via SessionStart — regras epistêmicas e de disciplina (research-depth, evidência antes de claim, scope discipline, bugfix principles, permissions, vocabulário de posturas, governança do kit) |
| `methodology` | metodologia de engenharia consolidada do kit — ponto de entrada pros princípios de mais alto nível |
| `pipeline` | condutor de fluxo: detecta o estágio real, classifica a intenção (feature/bug/investigação/spec-de-fora/refactor) e roteia pelas skills um estágio por vez — camada de routing do kit |
| `advisor-check` | escalação a um reviewer mais forte em pontos de decisão (pre-plan / post-plan / pre-done) |
| `archaeology` | mapa de codebase pré-tarefa (arqueologia antes de tocar código desconhecido) |
| `commit` | commit padronizado |
| `pr` | abertura/gestão de pull request |
| `review-local` | review de diff local antes de commit/PR |
| `review-remote` | review de PR remoto |
| `spec-refine` | refinamento adversarial de spec |
| `tech-breakdown` | breakdown técnico pra tech lead a partir de uma US/ticket |
| `figma-to-component` | extrai design do Figma via MCP e produz spec de widget tree mapeada aos componentes do design system do projeto consumidor |
| `bug-report` | investiga bug e só fecha relatório com citação `file:line` verificada por gate determinístico + verifier semântico em contexto fresco |
| `refine-live` | copiloto ao vivo pra agenda de refinamento com o PO — perguntas de esclarecimento em tempo real |
| `refine-async` | triage pós-refinamento — consolida contexto do refine-live, grep leve, gera subtarefas [INTERIM] pra aprovação |
| `compound` | composição de skills/tarefas em fluxo maior |
| `chat-draft` | rascunho de mensagem informal (Teams/Slack) |
| `grill-me` | entrevista estruturada e implacável pra pressionar plano/decisão |
| `learn` | escaneia a conversa e propõe entries de memória pra aprovação |
| `epicurus` | postura: separa necessário de desejável-descartável de vão antes de dar design/escopo por pronto |
| `schrodinger` | postura: mantém hipóteses de diagnóstico vivas até existir observação que discrimine |

**Agent (1)** — `plugins/core/agents/consumer-simulation.md`: recebe só o texto do ticket + critérios de aceite (nunca a implementação) e produz comportamentos esperados, pra detectar gap entre pedido e entregue.

**Hooks (7)** — `plugins/core/hooks/`, wireados em `hooks.json`:

| Hook | Evento | Faz o quê |
|---|---|---|
| `session-start.sh` | SessionStart (startup\|clear\|compact) | injeta o corpo de `using-agent-kit` como contexto sempre-ativo |
| `plan-autoload.sh` | SessionStart | se existe plano recente (<72h) em `docs/.../plans/`, injeta ponteiro de retomada |
| `bash-autoapprove-readonly.sh` | PreToolUse (Bash) | auto-aprova comandos de leitura reconhecidos como seguros (ex. `git status`), nunca comandos de escrita/push |
| `claude-dir-guard.sh` | PreToolUse (Bash) | bloqueia `rm` que atinge `.claude/` |
| `scope-inject.sh` | PreToolUse (Edit\|Write\|MultiEdit) | injeta ponteiro de escopo quando o arquivo editado casa um mapa de conhecimento do projeto |
| `context-monitor.sh` | PostToolUse (Bash) | avisa quando o transcript da sessão cresce além de um limiar |
| `read-ledger.sh` | PostToolUse (Read\|Grep) | registra o range lido no ledger da sessão (base do mecanismo de citação) |

**Scripts (5)** — `plugins/core/scripts/`: `analyze_tokens.py` (custo de contexto por componente — usado no teste R2 abaixo), `census_usage.py`, `conflict_triage.py`, `prune_branches.sh`, `validate_citations.py` (camada 1 do mecanismo de citação que `read-ledger.sh` alimenta).

---

## Mapa wired — `plugins/mobile`

**Skills (9)** — `plugins/mobile/skills/<nome>/SKILL.md`: `code-review-mobile` (checklist + cookbook + standards + estrutura de módulo Flutter), `mobx` (smells MobX/DI/arquitetura que o linter não pega — blockers on-demand, padrões aspiracionais, receitas), `refactor-review` (protocolo pós-refactor), `deeplink-debug`, `export-logs`, `feature-scaffold`, `ga4-validate`, `marionette` (condução de app Flutter rodando via MCP), `performance-patterns`.

**Agent (1)** — `plugins/mobile/agents/mobx-smell-hunter.md`: caça os 4 smells MobX que o linter e o hook determinístico não cobrem (composição de flow state, estado multi-writer, discriminador primitivo, estado de concorrência sintético).

**Hooks (4)** — `plugins/mobile/hooks/`, wireados em `hooks.json`:

| Hook | Evento | Faz o quê |
|---|---|---|
| `smell-checker.sh` | PreToolUse (Edit\|Write\|MultiEdit) | bloqueia (exit 2, add-only) smells de correctness em Dart: DI direto no lugar errado, `BuildContext` vazando pra controller, `print` em código de produção |
| `dart-auto-format.sh` | PostToolUse (Edit\|Write\|MultiEdit) | roda `dart format` no arquivo editado |
| `dart-analyze-file.sh` | PostToolUse (Edit\|Write\|MultiEdit) | roda `dart analyze` escopado ao arquivo, feedback sempre advisory |
| `package-feedback.sh` | PostToolUse (Edit\|Write) | lembrete de rodar teste de package ao editar `_test.dart`, uma vez por sessão |

**Scripts (5)** — `plugins/mobile/scripts/`: `arch_graph.sh`, `arch_violations.py`, `check_merged_imports.py`, `export_network_logs.py`, `swap_pubspec.py`.

**MCP (`.mcp.json`)** — registra dois servers: `dart` (`dart mcp-server`) e `marionette` (`marionette_mcp`) — condução/inspeção de app Flutter rodando. Nenhum server específico de backend/projeto (ex. Firebase com project-id real) foi incluído — portabilidade entre projetos consumidores é o critério.

---

## `unwired/` e regra de promoção

`unwired/` não é um plugin — nada nele é carregado pelo Claude Code, custo de contexto zero. É matéria-prima genericizável (council/posturas restantes, par de skills Figma→componente, bug-report com citação, refino live/async, metade-nudge de um hook, Stop-hook de handoff resgatado na revisão pós-construção, manual de operador de origem) com scrub mecânico de proveniência aplicado, mas sem uso real comprovado *neste* kit.

Modelo de três estados (D10): todo artefato que já existiu aqui está em exatamente um — **wired** (`plugins/`, custa contexto), **unwired** (aqui, custo zero, só lido se alguém abrir), ou **deletado** (avaliado e descartado). Nunca "testado mas não ligado".

Regra de promoção unwired → wired: uso real comprovado no projeto novo (você invocou, funcionou, quer que sobreviva ao próximo `/clear`) — não "parece útil" nem "era usado na origem". Ao promover: reescreva a `description` com o gatilho do novo contexto, preencha os placeholders de proveniência com nomes reais do projeto novo, mova o arquivo pra estrutura padrão do plugin, rode `claude plugin validate .`, delete a cópia em `unwired/`. Detalhe completo por item: `unwired/README.md`.

---

## Assets manuais (`assets/`)

Nenhum destes é carregado automaticamente pelo Claude Code — são templates/scripts que você copia e adapta manualmente:

- **`assets/statusline-command.sh`** — status line (modelo, contexto usado, rate limits, branch git). Instalar: copiar pra um path estável (ex. `~/.claude/statusline-command.sh`), `chmod +x`, e apontar em `settings.json`: `"statusLine": { "type": "command", "command": "bash ~/.claude/statusline-command.sh" }`. Requer `jq`.
- **`assets/claude-md-starter.md`** — esqueleto de `CLAUDE.md` pro projeto consumidor: seções (Project Identity, Architecture, Key Patterns, Language, Model Strategy, rodapé de ponteiros) + princípio-guia "ponteiro, não conteúdo inline". Copiar o corpo a partir de `# CLAUDE.md` e preencher os placeholders.
- **`assets/settings-snippets.md`** — trechos prontos de `settings.json`: sandbox Flutter (`allowWrite`/`allowRead` de cache de toolchain) e deny-list de edição em arquivo gerado por codegen (`.g.dart`, `.freezed.dart`, `.config.dart`). Copiar o trecho relevante e ajustar paths/domínios reais.

---

## Princípios do kit

- **Estado único por artefato (wired / unwired / deletado).** Ver seção acima — nunca uma quarta categoria fantasma de "meio-ligado".
- **Advisory-nudge não entra em `plugins/` sem medição.** Um mecanismo puramente de lembrete (sem enforcement, só reminder) precisa provar conversão real de uso antes de ser wired — não basta a ideia parecer boa. Caso concreto em `unwired/README.md` (`learning-pulse`): a metade "nudge" mediu ~0 conversão no projeto de origem e foi descartada por isso, não promovida por precaução.
- **Documentação nasce do que morde, não do que parece prudente.** Toda regra/skill do kit carrega um `Sinal` (como detectar a violação) e um `Failure mode` (o que quebra rio abaixo) — nasceu de um caso real observado, não de uma preocupação teórica antecipada. Regra textual que falha repetido vira mecanismo (hook, schema de output, gate determinístico) em vez de mais texto — texto marginal sob orçamento de atenção finito tende a ser omitido, não desobedecido.
- **Zero conteúdo do projeto de origem/específico de domínio, inclusive em `unwired/`.** Gate mecânico: `scripts/check-provenance.sh` (denylist de nomes de empresa/produto/board/paths internos) roda sobre o repo inteiro, sem exceção pra material unwired.

---

## Nota — double-loading em workspace com cópia própria

Se você instala este marketplace dentro de um workspace que já tem sua própria cópia commitada de skills/rules equivalentes (ex. um monorepo que já embarca `.claude/skills/` com conteúdo parecido), as duas fontes coexistem — o Claude Code carrega ambas. É redundante, mas benigno: não há conflito de nome garantido (plugin usa namespace `core:`/`mobile:`), e na pior hipótese você vê a mesma orientação listada duas vezes. Não é motivo pra não instalar; é só um custo de contexto duplicado a considerar ao decidir manter as duas fontes ou migrar o workspace pra consumir só o plugin.

---

## Gate de qualidade

```bash
./scripts/check-provenance.sh   # zero conteúdo do projeto de origem/domínio-específico, todo o repo
claude plugin validate .    # manifest da marketplace + dos 2 plugins
./evals/run-evals.sh        # Tier 1 determinístico: hooks reais com payload sintético
```

Os três precisam sair verdes antes de qualquer commit. `run-evals.sh` roda hooks reais via heredoc — em ambientes que sandboxam criação de arquivo temporário (ex. alguns harnesses de agente), rode com o sandbox desabilitado para esse comando específico.
