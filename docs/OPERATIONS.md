# Operações do kit

Escopo: operação de quem mantém e publica este kit (o dono). Instalação e uso do dia-a-dia (marketplace local) estão no `README.md` — este documento cobre publicação e distribuição (incluindo o lado consumidor da rota GitHub, que só existe depois que o dono publica), permissões e gate.

---

## 1. Publicação no GitHub

Lado do dono, executado a partir de `$HOME/dev/agent-kit`:

```bash
git remote add origin git@github.com:<usuario>/agent-kit.git
git push -u origin main --tags
```

**Placeholder obrigatório.** `<usuario>` é literal — nunca substituir por um nome de conta real neste arquivo nem em qualquer outro do repo. `scripts/check-provenance.sh` mantém uma denylist que casa nomes de conta por substring; um nome real aqui deixa o gate de proveniência vermelho.

Lado do consumidor: troca a marketplace local por uma `extraKnownMarketplaces` apontando pro GitHub, no `settings.json` (projeto ou usuário):

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
claude plugin install council@agent-kit   # acompanha o core SEMPRE — condição do censo de validação das posturas
claude plugin install team@agent-kit      # opcional: cerimônias de refinamento/squad
claude plugin install mobile@agent-kit    # só em projeto Flutter/Dart
```

A dependência inter-plugin tem aviso mecânico numa direção só: `team`/`council`/`mobile` avisam no SessionStart se o `core` não consta como instalado (hook `require-core.sh`). A direção reversa (`core` referenciando o Conselho) é coberta por esta instrução de instalação acoplada, não por hook — o `core` funciona sem o `council`, mas o censo de conversão das posturas exige os dois instalados juntos para não confundir conversão com disponibilidade.

A marketplace local (`claude plugin marketplace add "$HOME/dev/agent-kit"`) continua funcionando como caminho de desenvolvimento mesmo depois do remote publicado — o fonte se edita em `$HOME/dev/agent-kit`; o GitHub é canal de distribuição, não o lugar de edição.

Fluxo de update do consumidor após um novo commit no kit: `claude plugin update core@agent-kit` (e/ou `council@agent-kit`, `team@agent-kit`, `mobile@agent-kit`), seguido de reinício da sessão — sem o reinício a atualização não é aplicada.

---

## 2. Composição com o modo de permissão do harness

Duas camadas removem prompts de permissão, com papéis distintos:

- O modo de permissão do `settings.json` do usuário (`defaultMode`, sandbox) é o dono da decisão ampla de aprovação.
- `plugins/core/hooks/bash-autoapprove-readonly.sh` é um refinador estreito, só para Bash: emite `allow` para comandos de leitura reconhecidos como seguros, ou defere — nunca bloqueia.

Sinal para desabilitar o hook: se o `defaultMode` do usuário já aprova a maioria dos comandos Bash, o hook passa a ser latência morta (spawn de `python3` por chamada, estimativa de dezenas de ms). Ele paga a própria passagem quando o modo de permissão é mais restritivo ou o sandbox está inativo — nesses casos, manter ligado.

---

## 3. Nota de double-loading

Se este marketplace é instalado dentro de um workspace que já tem cópia própria commitada de skills/rules equivalentes (ex.: monorepo com `.claude/skills/` próprio), as duas fontes coexistem — o Claude Code carrega ambas. Coexistência benigna: não há conflito de nome garantido porque o plugin usa namespace (`core:`/`council:`/`team:`/`mobile:`); o custo é contexto duplicado, não comportamento incorreto. Não é motivo para deixar de instalar — é um custo a pesar na decisão de manter as duas fontes ou migrar o workspace para consumir só o plugin.

---

## 4. Gate de qualidade

Cinco comandos, todos precisam sair verdes antes de qualquer commit:

```bash
./scripts/check-provenance.sh
claude plugin validate .
./evals/run-evals.sh
python3 scripts/generate_inventory.py --check
./scripts/check-governance.sh
```

- `check-provenance.sh` — denylist de nomes de empresa/produto/board/paths internos, rodada sobre o repo inteiro (inclusive `unwired/`, sem exceção).
- `claude plugin validate .` — valida o manifest da marketplace e o de cada plugin.
- `run-evals.sh` — Tier 1 determinístico: roda os hooks reais contra payload sintético. Executa via heredoc; em ambientes que sandboxam criação de arquivo temporário (alguns harnesses de agente), rode com o sandbox desabilitado para esse comando específico.
- `generate_inventory.py --check` — `INVENTORY.md` é gerado, nunca editado à mão; este comando falha (gate vermelho) se a árvore do repo divergir do inventário registrado. Regenerar com `python3 scripts/generate_inventory.py` e commitar o resultado.
- `check-governance.sh` — mede a saída real de `session-start.sh` contra o teto do tier sempre-ativo e verifica que todo ID `D*`/`R*` citado no repo resolve no ledger. Teto, ledger e racional: `docs/GOVERNANCE.md`.

Convenção normativa por trás do inventário: a linha `# desc:` (linha 2 de cada hook/script sob `plugins/*/hooks` e `plugins/*/scripts`) é a fonte da descrição que aparece em `INVENTORY.md`. Qualquer header de prosa que já exista no arquivo é comentário livre, sem efeito no inventário. Em caso de divergência entre os dois, corrige-se a linha `# desc:` — não o header de prosa.

Docs de superfície (README, este arquivo e `docs/GOVERNANCE.md`) não carregam datas — histórico vive no `CHANGELOG.md`. Checagem: negar `grep -q` por padrão de ano-mês (`AAAA-`) sobre o arquivo. Nota: `grep -c` sai com código 1 quando não há match — não usar `-c` como aceite encadeado em `&&`.

---

## 5. unwired/ — matéria-prima sem uso comprovado

`unwired/` não é um plugin: nada ali é carregado pelo Claude Code — custo de contexto zero. É material genericizado de projetos de origem, escrutinado o bastante pra virar referência, mas sem uso real comprovado neste kit. Ciclo de vida (estados, promoção, exceção de deadline): `docs/GOVERNANCE.md`.

| Pasta | Origem | Por que não é wired |
|---|---|---|
| `ui-comparison/` | Skill de fidelidade visual de um projeto de origem | O método (fases, rubrica de score) é genérico; sem design system real pra testar contra, não tinha como comprovar uso aqui. `figma-to-component`, que vivia neste mesmo par, foi promovido — ver `plugins/mobile/skills/figma-to-component/` e o registro no `CHANGELOG.md`. |
| `learning-pulse/` | Metade "nudge" de um hook de duplo propósito | A metade advisory mediu ~0 conversão em uso real no projeto de origem e foi removida de lá por essa razão; a outra metade (debounce de scope-injection) foi resolvida de outra forma no `scope-inject.sh` do `core`. Só vira wired com medição nova que sustente o custo do lembrete. |
| `handoff-gate/` | Stop hook que fecha o loop alerta→ação do context-monitor | Deletado na extração como órfão ("peso morto com aparência de vivo"); resgatado na revisão pós-construção — o censo cego avaliou o mérito do mecanismo de forma independente e, com o fim do clone do projeto de origem, deletado significava perda definitiva (registro no `CHANGELOG.md`). O critério não muda: só sobe com uso real; o header do script lista o checklist de religação. |
| `WORKFLOW.md` | Manual do operador de um projeto de origem | Genericizado (nomes de skill no vocabulário deste kit onde há equivalente; lacunas marcadas). Referência/inspiração pro README, não documento que o Claude Code carrega. |

Fora daqui: conteúdo específico do domínio/empresa de origem (a denylist de `scripts/check-provenance.sh` cobre `unwired/` sem exceção, além da checagem manual de paths/classes/tickets feita na entrada de cada item) e duplicação de algo já wired.
