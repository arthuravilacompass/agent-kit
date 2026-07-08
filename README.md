# agent-kit

Plugins de Claude Code que padronizam a disciplina de engenharia — do ticket ao PR, com enforcement determinístico e portáveis entre projetos e clientes.

## Por que este kit?

Agentes de código sem guardrails produzem resultado inconsistente — e quem troca de cliente com frequência recomeça a disciplina do zero a cada projeto. O agent-kit é a memória executável dessa disciplina: toda regra nasceu de um erro real, virou mecanismo quando texto sozinho falhou, e só continua carregada enquanto provar uso. Ele ataca os dois problemas:

- **Regras epistêmicas sempre-ativas** — evidência antes de claim, grep antes de responder convenção, disciplina de escopo e de bugfix; injetadas em toda sessão via SessionStart.
- **Workflows de entrega** — um condutor (`core:pipeline`) que detecta o estágio real da tarefa e roteia: clarificar → especificar → quebrar → implementar → revisar → entregar → capturar.
- **Enforcement determinístico** — hooks e gates que não dependem de o modelo obedecer. O mais forte é o gate de citação: recusa relatório de bug cuja afirmação `arquivo:linha` não tenha leitura registrada no ledger da sessão. Também auto-aprova leitura segura, bloqueia smells de correctness em Dart e protege diretórios críticos.
- **Portabilidade por construção** — zero conteúdo do projeto de origem, garantido por gate mecânico (`scripts/check-provenance.sh`) sobre o repo inteiro. Correção aprendida num cliente vira enforcement portável no próximo.

O foco é qualidade e disciplina, não velocidade bruta.

## O que está incluído

Quatro plugins instaláveis por um marketplace local:

| Plugin | O que é | Conteúdo | Instale quando |
|---|---|---|---|
| `core` | Metodologia de entrega com enforcement determinístico, do ticket ao PR, qualquer stack | 14 skills, 1 agent, 7 hooks, 5 scripts | Sempre — é a base dos demais |
| `council` | Lentes epistêmicas para decisões de alto custo de reversão | 7 skills, 3 agents, 1 hook | Junto do `core`, sempre |
| `team` | Copiloto de cerimônias ágeis — refinamento com PO, comunicação de squad | 3 skills, 1 hook | Se você conduz refinamento ou comunica squad |
| `mobile` | Toolkit Flutter/Dart | 10 skills, 1 agent, 5 hooks, 5 scripts, 2 MCP servers | Só em projeto Flutter/Dart |

Inventário completo de skills, agents, hooks e scripts, gerado por script e verificado no gate: **[INVENTORY.md](INVENTORY.md)**.

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
claude plugin install council@agent-kit  # acompanha o core
claude plugin install team@agent-kit     # opcional: cerimônias ágeis com PO/squad
claude plugin install mobile@agent-kit   # só em projeto Flutter/Dart
```

Rode de dentro do projeto onde o kit deve ficar ativo.

### 3. Verificar

Abra uma sessão de Claude Code e confirme:

```bash
claude plugin list   # deve listar os plugins que você instalou (core@agent-kit, ...)
```

Numa sessão nova, as regras do `core` já entram via SessionStart. Jogue uma tarefa crua, sem estruturar — o `core:pipeline` detecta o estágio e conduz:

> preciso investigar por que o deeplink X quebra no Android

### 4. Atualizar

Depois de um novo commit no kit:

```bash
claude plugin update core@agent-kit council@agent-kit team@agent-kit mobile@agent-kit
```

Reinício de sessão necessário. Plugin instalado em escopo de projeto exige `--scope project`.

### Desinstalar

```bash
claude plugin uninstall mobile@agent-kit   # se instalado
claude plugin uninstall team@agent-kit
claude plugin uninstall council@agent-kit
claude plugin uninstall core@agent-kit
claude plugin marketplace remove agent-kit
```

## Workflow

O kit segue um fluxo estruturado em torno do `core:pipeline`: você entrega a intenção crua, ele detecta o estágio e propõe a rota — um estágio por vez, nunca a cadeia inteira sozinho.

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

Cada estágio produz um artefato que informa o próximo, reduzindo ambiguidade e retrabalho. Rota mínima é legítima em tarefa pequena — o pipeline propõe pular estágios e espera sua confirmação.

<!-- demo: asciinema/GIF 30s do pipeline — gravação manual do operador; incorporar aqui -->

## Requisitos

- [Claude Code](https://claude.com/claude-code) com suporte a plugins
- **Opcional:** marketplace [superpowers](https://github.com/obra/superpowers) — alguns fluxos do `core` o referenciam (brainstorming, writing-plans, systematic-debugging); sem ele nada quebra, o pipeline indica o fallback interno de cada estágio
- Para o `mobile`: projeto Flutter/Dart. Os MCP servers registrados são só os genéricos de toolchain — nenhum server de backend/projeto

## Avançado

### Conselho de Posturas (`council`)

Seis modos de raciocínio pra vestir deliberadamente diante de uma decisão de alto custo de reversão — Schrödinger (diagnóstico ambíguo), Bohr (falsa dicotomia), Epicurus (escopo), Sagan (calibragem de esforço), Maxwell (propagação de mudança), Zeno (stress de invariantes). Índice, formato de saída e escalonamento pro modo cego: skill `council:council`.

### Governança

Ciclo de vida dos artefatos (o que entra, sobe e sai), regra de promoção, contrato de autoria de skills e ledger de decisões: **[docs/GOVERNANCE.md](docs/GOVERNANCE.md)**. Operação de quem mantém o kit — publicação, gate de qualidade quíntuplo, material genericizado ainda sem uso comprovado (`unwired/`): **[docs/OPERATIONS.md](docs/OPERATIONS.md)**.

### Estrutura do repositório

| Diretório | O que é |
|---|---|
| `plugins/` | Os quatro plugins instaláveis (`core`, `council`, `team`, `mobile`) |
| `unwired/` | Matéria-prima genericizada aguardando prova de uso — nada é carregado, custo de contexto zero ([detalhe](docs/OPERATIONS.md)) |
| `assets/` | Templates de cópia manual: status line, esqueleto de `CLAUDE.md`, snippets de `settings.json` |
| `docs/` | [GOVERNANCE.md](docs/GOVERNANCE.md) (ciclo de vida, contrato de skills, ledger) e [OPERATIONS.md](docs/OPERATIONS.md) (operação do dono) |
| `scripts/` | Gate de proveniência, gerador de inventário e tooling de manutenção |

---

[INVENTORY.md](INVENTORY.md) · [docs/GOVERNANCE.md](docs/GOVERNANCE.md) · [docs/OPERATIONS.md](docs/OPERATIONS.md) · [CHANGELOG.md](CHANGELOG.md)
