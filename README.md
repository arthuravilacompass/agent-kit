# agent-kit

Configuração padronizada de Claude Code para todos os meus repositórios. Fornece regras sempre-ativas, workflows de entrega, skills, agents e hooks — distribuídos como quatro plugins instaláveis via marketplace local: **`core`** (metodologia, qualquer stack), **`council`** (lentes de decisão), **`team`** (cerimônias ágeis) e **`mobile`** (Flutter/Dart).

## Por que este kit?

Agentes de código sem guardrails produzem resultado inconsistente — e quem troca de projeto com frequência recomeça a disciplina do zero a cada cliente. O agent-kit resolve os dois problemas:

- **Regras epistêmicas sempre-ativas** — evidência antes de claim, grep antes de responder convenção, disciplina de escopo e de bugfix, injetadas em toda sessão via SessionStart.
- **Workflows de entrega** — um condutor de fluxo (`core:pipeline`) que detecta o estágio real da tarefa e roteia pelos estágios: clarificar, especificar, quebrar, implementar, revisar, entregar, capturar.
- **Enforcement determinístico** — hooks que auto-aprovam leitura segura, bloqueiam smells de correctness em Dart, protegem diretórios críticos e mantêm ledger de citação. Não dependem de o modelo obedecer.
- **Portabilidade por construção** — zero conteúdo de projeto de origem, garantido por gate mecânico (`scripts/check-provenance.sh`) sobre o repo inteiro. Correções de um projeto viram enforcement portável pro próximo.

## O que está incluído

### `core` — metodologia de engenharia, qualquer stack

14 skills, 1 agent, 7 hooks e 5 scripts. Destaques:

- `core:pipeline` — condutor de fluxo: classifica a intenção crua e conduz pelas skills do kit, um estágio por vez
- `/core:commit`, `/core:pr`, `/core:review-local` — fluxo de entrega com validação pré-commit e reviewers em paralelo
- `/core:tech-breakdown`, `/core:spec-refine`, `/core:archaeology` — de ticket a plano de implementação grillado contra o codebase real
- `core:learn` + `/core:compound` — captura de aprendizado e handoff no fim da sessão

### `council` — lentes epistêmicas (instalar junto do `core`)

7 skills, 3 agents. Conselho de Posturas: 6 lentes (Schrödinger, Bohr, Epicurus, Sagan, Maxwell, Zeno) para decisões de alto custo de reversão — índice em `council:council`.

### `team` — cerimônias ágeis

3 skills. `/team:refine-live` (copiloto da agenda de refinamento com o PO), `/team:refine-async` (triage pós-agenda) e `team:chat-draft` (mensagens de squad).

### `mobile` — toolkit Flutter/Dart (pressupõe `core`)

10 skills, 1 agent, 4 hooks, 5 scripts e 2 MCP servers (`dart`, `marionette`). Destaques:

- `mobile:code-review-mobile`, `mobile:refactor-review` — review Flutter com checklist em camadas e protocolo pós-refactor
- `mobile:mobx`, `mobile:performance-patterns` — smells de MobX/DI e padrões de performance que o linter não pega, com bloqueio determinístico dos casos de correctness
- `mobile:deeplink-debug`, `mobile:ga4-validate`, `mobile:marionette` — debug de deeplink, validação de tracking GA4 e condução visual do app no simulador
- `mobile:feature-scaffold`, `/mobile:figma-to-component` — scaffold em camadas e conversão Figma → widget tree

Inventário completo, gerado por script e verificado no gate: **[INVENTORY.md](INVENTORY.md)**.

## Instalação

### 1. Clonar (uma vez)

Clone este repositório para um path estável (a URL está no botão **Code** acima):

```bash
git clone <url-deste-repositorio> ~/dev/agent-kit
```

### 2. Adicionar o marketplace e instalar

```bash
claude plugin marketplace add "$HOME/dev/agent-kit"
claude plugin install core@agent-kit
claude plugin install council@agent-kit  # acompanha o core — condição do censo de validação das posturas
claude plugin install team@agent-kit     # opcional: cerimônias ágeis com PO/squad
claude plugin install mobile@agent-kit   # só em projeto Flutter/Dart
```

Rode de dentro do projeto onde o kit deve ficar ativo.

### 3. Verificar

Abra uma sessão de Claude Code e confirme:

```bash
claude plugin list   # deve listar core@agent-kit, council@agent-kit, team@agent-kit e mobile@agent-kit (os que você instalou)
```

Numa sessão nova, as regras do `core` já entram via SessionStart. Jogue uma tarefa crua, sem estruturar — o `core:pipeline` detecta o estágio e conduz:

> preciso investigar por que o deeplink X quebra no Android

### 4. Atualizar

Depois de um novo commit no kit:

```bash
claude plugin update core@agent-kit     # e/ou mobile@agent-kit
```

Reinício de sessão necessário.

### Desinstalar

```bash
claude plugin uninstall mobile@agent-kit   # se instalado
claude plugin uninstall team@agent-kit
claude plugin uninstall council@agent-kit
claude plugin uninstall core@agent-kit
claude plugin marketplace remove agent-kit
```

## Fluxo de trabalho

```
intenção crua ("adiciona autenticação", "esse deeplink quebrou", ticket do board)
  ↓ core:pipeline — detecta o estágio real, classifica a intenção, propõe a rota
clarificar        → core:grill-me / brainstorming
especificar       → /core:spec-refine
quebrar           → /core:tech-breakdown
implementar       → execução com hooks de enforcement ativos
revisar           → /core:review-local (+ mobile:refactor-review em refactor)
entregar          → /core:commit → /core:pr
capturar          → core:learn + handoff
```

Um estágio por vez — o pipeline recomenda a próxima rota e para; nunca executa a cadeia inteira sozinho. Rota mínima é legítima em tarefa pequena.

## Requisitos

- [Claude Code](https://claude.com/claude-code) com suporte a plugins
- **Opcional:** marketplace [superpowers](https://github.com/obra/superpowers) — alguns fluxos do `core` o referenciam (brainstorming, writing-plans, systematic-debugging); sem ele nada quebra, o pipeline indica o fallback interno de cada estágio
- Para o `mobile`: projeto Flutter/Dart. Os MCP servers registrados são só os genéricos de toolchain — nenhum server de backend/projeto

## Estrutura do repositório

| Diretório | O que é |
|---|---|
| `plugins/` | Os quatro plugins instaláveis (`core`, `council`, `team`, `mobile`) |
| `unwired/` | Matéria-prima genericizada aguardando prova de uso — nada é carregado, custo de contexto zero ([detalhe](unwired/README.md)) |
| `assets/` | Templates de cópia manual: status line, esqueleto de `CLAUDE.md`, snippets de `settings.json` |
| `docs/` | [GOVERNANCE.md](docs/GOVERNANCE.md) (ciclo de vida, promoção, ledger de decisões), [SKILL-CONTRACT.md](docs/SKILL-CONTRACT.md) (formato de autoria de skills) e [OPERATIONS.md](docs/OPERATIONS.md) (operação do dono) |
| `scripts/` | Gate de proveniência, gerador de inventário e tooling de manutenção |

## Princípios

- **Toda regra nasce de um erro real** — e carrega um `Sinal` (como detectar a violação) e um `Failure mode` (o que quebra na prática).
- **Zero conteúdo do projeto de origem** — inclusive em `unwired/`; o gate mecânico roda sobre o repo inteiro, sem exceção.
- **Só continua carregado o que prova uso** — modelo de estados, regra de promoção e teto do sempre-ativo em [docs/GOVERNANCE.md](docs/GOVERNANCE.md).

---

[INVENTORY.md](INVENTORY.md) · [docs/GOVERNANCE.md](docs/GOVERNANCE.md) · [docs/OPERATIONS.md](docs/OPERATIONS.md) · [CHANGELOG.md](CHANGELOG.md)
