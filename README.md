# agent-kit

Memória executável de disciplina de engenharia para Claude Code: toda regra aqui nasceu de um erro real, virou mecanismo quando texto falhou, e só continua carregada enquanto provar uso. Quatro plugins instaláveis levam essa disciplina de um projeto ao próximo — a correção aprendida num cliente vira enforcement portável no seguinte.

## A bandeira: citação verificada

Neste kit, "evidência antes de claim" não é lembrete — é mecanismo. O hook `read-ledger.sh` registra cada `Read`/`Grep` da sessão num ledger; `validate_citations.py --gate` recusa relatório cuja citação `arquivo:linha` não tenha leitura registrada correspondente. A skill `core:bug-report` executa esse gate por padrão: investigação que afirma comportamento de código sem ter lido a fonte não passa.

## O fluxo de entrega

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

<!-- demo: asciinema/GIF 30s do pipeline — gravação manual do operador; incorporar aqui -->

## Os quatro plugins

| Plugin | Identidade | Conteúdo | Instale quando |
|---|---|---|---|
| `core` | Metodologia de entrega com enforcement determinístico, do ticket ao PR, qualquer stack | 14 skills, 1 agent, 7 hooks, 5 scripts | Sempre — é a base dos demais |
| `council` | Lentes epistêmicas para decisões de alto custo de reversão | 7 skills, 3 agents, 1 hook | Junto do `core`, sempre — condição do censo das posturas |
| `team` | Copiloto de cerimônias ágeis — refinamento com PO, comunicação de squad | 3 skills, 1 hook | Se você conduz refinamento ou comunica squad |
| `mobile` | Toolkit Flutter/Dart | 10 skills, 1 agent, 5 hooks, 5 scripts, 2 MCP servers | Só em projeto Flutter/Dart |

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
claude plugin update core@agent-kit council@agent-kit team@agent-kit mobile@agent-kit
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

## Seções avançadas

### Conselho de Posturas (`council`)

Seis modos de raciocínio pra vestir deliberadamente diante de uma decisão — Schrödinger (diagnóstico ambíguo), Bohr (falsa dicotomia), Epicurus (escopo), Sagan (calibragem de esforço), Maxwell (propagação de mudança), Zeno (stress de invariantes). Índice, formato de saída e escalonamento pro modo cego: skill `council:council`.

### Governança

Modelo de 3 estados (wired/unwired/deletado), regra de promoção, teto do tier sempre-ativo, contrato de SKILL.md (esqueletos, idioma, tetos de linhas e de descriptions) e ledger de decisões `D*`/`R*`: **[docs/GOVERNANCE.md](docs/GOVERNANCE.md)**. Operação do dono — publicação, gate de qualidade quíntuplo, `unwired/`: **[docs/OPERATIONS.md](docs/OPERATIONS.md)**.

### Estrutura do repositório

| Diretório | O que é |
|---|---|
| `plugins/` | Os quatro plugins instaláveis (`core`, `council`, `team`, `mobile`) |
| `unwired/` | Matéria-prima genericizada aguardando prova de uso — nada é carregado, custo de contexto zero ([detalhe](docs/OPERATIONS.md)) |
| `assets/` | Templates de cópia manual: status line, esqueleto de `CLAUDE.md`, snippets de `settings.json` |
| `docs/` | [GOVERNANCE.md](docs/GOVERNANCE.md) (ciclo de vida, contrato de SKILL.md, ledger) e [OPERATIONS.md](docs/OPERATIONS.md) (operação do dono) |
| `scripts/` | Gate de proveniência, gerador de inventário e tooling de manutenção |

### Requisitos

- [Claude Code](https://claude.com/claude-code) com suporte a plugins
- **Opcional:** marketplace [superpowers](https://github.com/obra/superpowers) — alguns fluxos do `core` o referenciam (brainstorming, writing-plans, systematic-debugging); sem ele nada quebra, o pipeline indica o fallback interno de cada estágio
- Para o `mobile`: projeto Flutter/Dart. Os MCP servers registrados são só os genéricos de toolchain — nenhum server de backend/projeto

## Glossário

- **wired** — artefato que vive em `plugins/` e é carregado pelo Claude Code; custa contexto toda sessão, e por isso exige uso real comprovado pra entrar e pra permanecer.
- **unwired** — matéria-prima genericizada em `unwired/`; custo de contexto zero, aguardando prova de uso pra ser promovida.
- **grillado** — que passou pelo `grill-me`: interrogatório adversarial (entrevista ou escalação a um reviewer mais forte) que pressiona as decisões antes de dar um plano ou entrega por pronto.
- **gate** — verificação mecânica que precisa sair verde antes de qualquer commit: proveniência, manifests, evals, inventário e governança. Não depende de o modelo obedecer.
- **censo** — medição de uso real ao fim de um ciclo de cliente (`census_usage.py`) que decide o que continua wired, o que é demovido e o que sai; também resolve os prazos dos itens provisórios.

## Princípios

- **Toda regra nasce de um erro real** — e carrega um `Sinal` (como detectar a violação) e um `Failure mode` (o que quebra na prática).
- **Zero conteúdo do projeto de origem** — inclusive em `unwired/`; o gate mecânico roda sobre o repo inteiro, sem exceção.
- **Só continua carregado o que prova uso** — modelo de estados, regra de promoção e teto do sempre-ativo em [docs/GOVERNANCE.md](docs/GOVERNANCE.md).

---

[INVENTORY.md](INVENTORY.md) · [docs/GOVERNANCE.md](docs/GOVERNANCE.md) · [docs/OPERATIONS.md](docs/OPERATIONS.md) · [CHANGELOG.md](CHANGELOG.md)
