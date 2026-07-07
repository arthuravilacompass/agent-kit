# Refino Fase 1 — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fechar os itens mecânicos confirmados da onda de refino (spec `docs/superpowers/specs/2026-07-07-refino-pos-auditoria-design.md` §5 Fase 1): CI, fix do furo Bash-read, marcador wired-provisório, critério slash-only, coluna de conformidade.

**Architecture:** Tudo é extensão de mecanismos existentes — os gates `check-governance.sh`/`generate_inventory.py` ganham fontes de dados novas (duas seções parseáveis em docs), o `review-local` ganha 2 edits cirúrgicos, e o CI só orquestra o que já roda localmente. Nenhum hook de enforcement é tocado.

**Tech Stack:** Bash (gates), Python 3 stdlib puro (generator — sem PyYAML, determinístico), GitHub Actions, Markdown parseável por regex de linha.

## Global Constraints

- **NO-COMMIT**: nenhum `git commit`/`push` sem autorização explícita do operador. Se a autorização não foi dada no kickoff da execução, o executor faz `git add` (stage), reporta e **para** no lugar de cada step de commit.
- **Gates verdes após cada task**: `bash scripts/check-provenance.sh && bash scripts/check-governance.sh && python3 scripts/generate_inventory.py --check && ./evals/run-evals.sh`. Baseline 2026-07-07: tudo verde, 35 evals, sempre-ativo 10.876/16.384 bytes.
- **`INVENTORY.md` é gerado** — nunca editar à mão; toda mudança no generator termina com regen + `--check`.
- **Não tocar** em `bash-autoapprove-readonly.sh`, `read-ledger.sh`, `claude-dir-guard.sh` e demais hooks.
- Idioma: docs e strings de saída pt-BR; código, identificadores e mensagens de commit em inglês.
- Datas “valida até 2026-08-06” = fim do ciclo assumido (30 dias da promoção do Conselho). Se o operador definir outra data de censo, trocar nas linhas da tabela do Task 3 antes de executar.
- Item 1.1 do spec (dogfood em projeto externo) é **ação do operador, paralela** — não é task deste plano.

---

### Task 1: Emenda D14 §Escopo — cláusula de correção cirúrgica

**Files:**
- Modify: `docs/SKILL-CONTRACT.md:5`

**Interfaces:**
- Produces: regra que permite o Task 2 editar `review-local/SKILL.md` sem arrastá-lo pra §Conformidade. Decisão do operador (2026-07-07, AskUserQuestion).

- [ ] **Step 1: Editar a linha de escopo**

Substituir a linha 5 inteira:

```markdown
**Escopo**: skill nova nasce conforme. Skill existente conforma quando for reformada — mudança de esqueleto, propósito ou estrutura; ao ser reformada, entra na §Conformidade. Correção cirúrgica (linhas pontuais que não mudam esqueleto, propósito nem estrutura) não constitui reforma e não obriga conformidade. Sem big-bang no estoque.
```

- [ ] **Step 2: Verificar gate**

Run: `bash scripts/check-governance.sh`
Expected: 4 linhas `OK:` (o parse da §Conformidade não é afetado), exit 0.

- [ ] **Step 3: Commit (gated por NO-COMMIT)**

```bash
git add docs/SKILL-CONTRACT.md
git commit -m "docs(governance): D14 scope — surgical fixes don't trigger conformity"
```

---

### Task 2: Fix do furo Bash-read no review-local

**Files:**
- Modify: `plugins/core/skills/review-local/SKILL.md:68` e `:77`

**Interfaces:**
- Consumes: cláusula cirúrgica do Task 1 (o arquivo NÃO entra na §Conformidade).
- Produces: mandato de leitura citável via tool Read; claim da linha 77 anotada com o veredito do teste de runtime de 2026-07-07 (reads de subagent via tool Read entram no ledger da sessão-mãe; via Bash não entram).

- [ ] **Step 1: Adicionar o mandato ao bloco Dispatch (linha 68)**

Ao final do parágrafo **Dispatch:** (que termina em “— nunca o diff.”), acrescentar na mesma linha:

```markdown
 Cada prompt de agente DEVE mandar: use o tool **Read** (nunca `cat`/`sed`/`grep` via Bash) para qualquer arquivo que vá ser citado como evidência — leitura via Bash não entra no read-ledger e derruba a citação no gate.
```

- [ ] **Step 2: Anotar a claim da linha 77**

Substituir a frase `O read-ledger registra os reads de TODOS os subagentes sob a session_id-pai.` por:

```markdown
O read-ledger registra os reads via tool Read/Grep de TODOS os subagentes sob a session_id-pai (verificado em runtime, 2026-07-07); leitura via Bash NÃO entra — daí o mandato do Dispatch.
```

- [ ] **Step 3: Verificar**

Run: `grep -c "read-ledger" plugins/core/skills/review-local/SKILL.md && wc -l plugins/core/skills/review-local/SKILL.md && bash scripts/check-governance.sh`
Expected: 3 ocorrências; ~116-117 linhas (informativo — arquivo fora da §Conformidade); gate verde.

- [ ] **Step 4: Commit (gated por NO-COMMIT)**

```bash
git add plugins/core/skills/review-local/SKILL.md
git commit -m "fix(review-local): mandate Read tool for citable evidence (Bash reads bypass ledger)"
```

---

### Task 3: Tabela de provisórios no GOVERNANCE + check 5 no gate + ledger D17

**Files:**
- Modify: `docs/GOVERNANCE.md` (nova subseção após a §Exceção, linha 28; nova entrada no ledger)
- Modify: `scripts/check-governance.sh` (check 5, antes do `exit $fail`)

**Interfaces:**
- Produces: formato de linha parseável `` - `<path-relativo>` — valida até AAAA-MM-DD `` na subseção `### Provisórios ativos`, consumido pelo check 5 (este task) e pelo `collect_provisional()` do Task 4. Enumeração vem do `CHANGELOG.md` (leva 2026-07-06: bug-report, refine-live, refine-async, figma-to-component; leva 2026-07-07: os 8 arquivos do Conselho).

- [ ] **Step 1: Inserir a subseção no GOVERNANCE (imediatamente após o parágrafo da §Exceção, antes de `## Meta-princípios`)**

```markdown
### Provisórios ativos (lidos por máquina)

Itens atualmente wired sob a exceção acima. Formato de linha (contrato lido por `scripts/generate_inventory.py` e `scripts/check-governance.sh`): `` - `<path relativo do artefato>` — valida até AAAA-MM-DD ``. Item validado por uso sai da lista (vira wired pleno); prazo vencido deixa o gate vermelho até a decisão — validar ou demover (D17).

- `plugins/core/skills/bug-report` — valida até 2026-08-06
- `plugins/core/skills/refine-live` — valida até 2026-08-06
- `plugins/core/skills/refine-async` — valida até 2026-08-06
- `plugins/mobile/skills/figma-to-component` — valida até 2026-08-06
- `plugins/core/skills/council` — valida até 2026-08-06
- `plugins/core/skills/bohr` — valida até 2026-08-06
- `plugins/core/skills/sagan` — valida até 2026-08-06
- `plugins/core/skills/council-log` — valida até 2026-08-06
- `plugins/core/skills/council-recall` — valida até 2026-08-06
- `plugins/core/agents/maxwell.md` — valida até 2026-08-06
- `plugins/core/agents/zeno.md` — valida até 2026-08-06
- `plugins/core/agents/epistemic-council.md` — valida até 2026-08-06
```

Nota: `schrodinger` e `epicurus` NÃO entram — foram wired na extração original com linhagem de uso, não sob a exceção (CHANGELOG, leva 2026-07-07 lista 8 arquivos).

- [ ] **Step 2: Adicionar D17 ao ledger (fim da lista do `## Ledger de decisões`)**

```markdown
- **D17** — Marcador wired-provisório machine-readable com prazo (§Provisórios ativos deste doc): INVENTORY marca o item, prazo vencido deixa o gate vermelho até validar ou demover. Enforcement: `scripts/check-governance.sh` (check 5) + `scripts/generate_inventory.py` (marcador ⏳).

> NB (defeito de plano corrigido em execução): a versão original desta entrada citava os IDs de fases futuras como tokens literais, o que fazia o census de `check-governance.sh` (`\b[DR][0-9]+\b`) exigir entrada de ledger pra eles antes de existirem. Removido — o preâmbulo do ledger já declara numeração esparsa por origem; não citar ID de fase futura em arquivo escaneado pelo gate.
```

- [ ] **Step 3: Adicionar o check 5 ao `scripts/check-governance.sh` (antes do `exit $fail`)**

```bash
# 5) Provisórios (D17): prazo vencido = gate vermelho até validar ou demover
prov=$(sed -n '/^### Provisórios ativos/,/^## /p' "$LEDGER" \
  | grep -E '^- `[^`]+` — valida até [0-9]{4}-[0-9]{2}-[0-9]{2}$' || true)
if [ -z "$prov" ]; then
  echo "OK: nenhum item provisório ativo"
else
  today=$(date +%F)
  expired=0
  while IFS= read -r line; do
    path=$(echo "$line" | grep -oE '`[^`]+`' | tr -d '`')
    deadline=$(echo "$line" | grep -oE '[0-9]{4}-[0-9]{2}-[0-9]{2}')
    if [ ! -e "$path" ]; then
      echo "ERRO: provisório ${path} listado em ${LEDGER} não existe no disco (D17)"
      fail=1
    fi
    if [[ "$today" > "$deadline" ]]; then
      echo "ERRO: provisório ${path} venceu em ${deadline} — validar por uso ou demover (D17)"
      fail=1; expired=1
    fi
  done <<< "$prov"
  if [ "$expired" -eq 0 ]; then
    echo "OK: provisórios dentro do prazo ($(echo "$prov" | wc -l | tr -d ' ') itens, D17)"
  fi
fi
```

(Comparação `[[ "$today" > "$deadline" ]]` é lexicográfica — correta para datas ISO. `|| true` porque o script roda `set -uo pipefail` e grep sem match retorna 1.)

- [ ] **Step 4: Verificar caminho feliz**

Run: `bash scripts/check-governance.sh`
Expected: 5 linhas `OK:` — a nova é `OK: provisórios dentro do prazo (12 itens, D17)`; `OK: todo ID citado resolve no ledger (... D17 ...)`; exit 0.

- [ ] **Step 5: Verificar caminho vermelho (temporário)**

1. Adicionar linha de teste na subseção: `` - `plugins/core/skills/commit` — valida até 2020-01-01 ``
2. Run: `bash scripts/check-governance.sh; echo rc=$?`
   Expected: `ERRO: provisório plugins/core/skills/commit venceu em 2020-01-01 ...` e `rc=1`.
3. Remover a linha de teste. Run de novo: exit 0.

- [ ] **Step 6: Commit (gated por NO-COMMIT)**

```bash
git add docs/GOVERNANCE.md scripts/check-governance.sh
git commit -m "feat(governance): D17 machine-readable provisional register + expiry gate check"
```

---

### Task 4: Marcador ⏳ no INVENTORY (generate_inventory.py)

**Files:**
- Modify: `scripts/generate_inventory.py`

**Interfaces:**
- Consumes: subseção `### Provisórios ativos` e regex de linha do Task 3.
- Produces: células de nome com sufixo `⏳ provisório até AAAA-MM-DD` nas tabelas Skills e Agents; função `collect_provisional() -> dict[path,str]`; falha alta (`InventoryError`) para path provisório que não casa com nenhum artefato renderizado.

- [ ] **Step 1: Adicionar constantes e `collect_provisional()` (após `DESC_LINE_RE`, linha 42)**

```python
GOVERNANCE_PATH = os.path.join(REPO_ROOT, "docs", "GOVERNANCE.md")
PROVISIONAL_LINE_RE = re.compile(r"^- `([^`]+)` — valida até (\d{4}-\d{2}-\d{2})$")


def collect_provisional():
    """path relativo -> deadline, da seção '### Provisórios ativos' de docs/GOVERNANCE.md."""
    if not os.path.isfile(GOVERNANCE_PATH):
        return {}
    result = {}
    in_section = False
    with open(GOVERNANCE_PATH, encoding="utf-8") as f:
        for raw in f:
            line = raw.rstrip("\n")
            if line.startswith("### Provisórios ativos"):
                in_section = True
                continue
            if in_section and (line.startswith("## ") or line.startswith("### ")):
                break
            if in_section:
                m = PROVISIONAL_LINE_RE.match(line)
                if m:
                    if m.group(1) in result:
                        raise InventoryError(
                            f"docs/GOVERNANCE.md: provisório duplicado '{m.group(1)}'"
                        )
                    result[m.group(1)] = m.group(2)
    return result
```

- [ ] **Step 2: Marcar skills e agents**

Em `collect_skills(plugin)` → assinatura vira `collect_skills(plugin, provisional)`; após montar o dict do skill, antes do `append`:

```python
        key = f"plugins/{plugin}/skills/{name}"
        deadline = provisional.pop(key, None)
```

e o append ganha `"provisional_until": deadline`. Em `collect_agents(plugin)` → `collect_agents(plugin, provisional)`, análogo com `key = f"plugins/{plugin}/agents/{fname}"`.

Em `render_plugin_section(plugin)` → `render_plugin_section(plugin, provisional)`; célula de nome (skills e agents):

```python
        if s.get("provisional_until"):
            name_cell += f" ⏳ provisório até {s['provisional_until']}"
```

(no caso de skill slash-only, o sufixo entra depois do `(slash-only: ...)`).

- [ ] **Step 3: Consumo total falha alto + legenda**

Em `generate()`: coletar `provisional = collect_provisional()` antes do loop, passar para `render_plugin_section(plugin, provisional)`; após o loop:

```python
    if provisional:
        raise InventoryError(
            "provisórios em docs/GOVERNANCE.md sem artefato correspondente: "
            + ", ".join(sorted(provisional))
        )
```

E adicionar ao cabeçalho fixo de `generate()` (depois do parágrafo do slash-only):

```python
        "Itens com “provisório até <data>” estão wired sob a exceção de deadline "
        "(`docs/GOVERNANCE.md` §Provisórios ativos) — prazo vencido deixa o gate vermelho.",
        "",
```

- [ ] **Step 4: Regenerar e verificar**

Run: `python3 scripts/generate_inventory.py && grep -c "provisório até" INVENTORY.md && python3 scripts/generate_inventory.py --check`
Expected: `13` (12 itens + 1 linha de legenda); `OK: INVENTORY.md está atualizado.`; exit 0.

- [ ] **Step 5: Verificar falha alta (temporário)**

1. Em `docs/GOVERNANCE.md`, trocar `bug-report` por `bug-reportx` na tabela; rodar `python3 scripts/generate_inventory.py`.
   Expected: `ERRO: provisórios em docs/GOVERNANCE.md sem artefato correspondente: plugins/core/skills/bug-reportx`, exit 1.
2. Reverter. Rodar `--check`: exit 0.

- [ ] **Step 6: Commit (gated por NO-COMMIT)**

```bash
git add scripts/generate_inventory.py INVENTORY.md
git commit -m "feat(inventory): provisional marker from governance register (D17)"
```

---

### Task 5: Coluna de conformidade D14 no INVENTORY

**Files:**
- Modify: `scripts/generate_inventory.py`

**Interfaces:**
- Consumes: formato da §Conformidade de `docs/SKILL-CONTRACT.md` — `` - `<path>` — <esqueleto> `` (já existente, lido também pelo gate check 3).
- Produces: coluna `Contrato (D14)` na tabela de Skills: nome do esqueleto ou `pendente`; função `collect_conformity() -> dict[path,str]`.

- [ ] **Step 1: Adicionar `collect_conformity()` (após `collect_provisional()`)**

```python
CONTRACT_PATH = os.path.join(REPO_ROOT, "docs", "SKILL-CONTRACT.md")
CONFORMITY_LINE_RE = re.compile(r"^- `(plugins/[^`]+)` — ([a-zA-Zà-ú-]+)$")


def collect_conformity():
    """path do SKILL.md -> esqueleto, da seção '## Conformidade' de docs/SKILL-CONTRACT.md."""
    if not os.path.isfile(CONTRACT_PATH):
        return {}
    result = {}
    in_section = False
    with open(CONTRACT_PATH, encoding="utf-8") as f:
        for raw in f:
            line = raw.rstrip("\n")
            if line.startswith("## Conformidade"):
                in_section = True
                continue
            if in_section and line.startswith("## "):
                break
            if in_section:
                m = CONFORMITY_LINE_RE.match(line)
                if m:
                    result[m.group(1)] = m.group(2)
    return result
```

- [ ] **Step 2: Coluna na tabela de Skills**

`generate()` coleta `conformity = collect_conformity()` e repassa; em `render_plugin_section`, a tabela de skills vira 3 colunas:

```python
    rows = []
    for s in skills:
        ...  # name_cell como está (com slash-only e ⏳)
        contract = conformity.get(f"plugins/{plugin}/skills/{s['name']}/SKILL.md", "pendente")
        rows.append([name_cell, contract, s["description"]])
    lines.extend(render_table(["Skill", "Contrato (D14)", "Descrição"], rows))
```

- [ ] **Step 3: Regenerar e verificar**

Run: `python3 scripts/generate_inventory.py && grep -c "| pendente |" INVENTORY.md && python3 scripts/generate_inventory.py --check && bash scripts/check-governance.sh`
Expected: `31` (35 skills − 4 conformes); `--check` OK; gate verde (5 OKs).

- [ ] **Step 4: Commit (gated por NO-COMMIT)**

```bash
git add scripts/generate_inventory.py INVENTORY.md
git commit -m "feat(inventory): D14 conformity column exposes contract debt"
```

---

### Task 6: Critério slash-only escrito no contrato

**Files:**
- Modify: `docs/SKILL-CONTRACT.md` (nova seção antes de `## Proibições`)
- Modify: `scripts/generate_inventory.py` (ponteiro na legenda) + regen `INVENTORY.md`

**Interfaces:**
- Produces: seção `## Critério slash-only` no contrato; legenda do INVENTORY aponta pra ela.

- [ ] **Step 1: Inserir a seção no contrato (entre `## Teto de linhas` e `## Proibições`)**

```markdown
## Critério slash-only

`disable-model-invocation: true` quando a skill: (a) dispara efeito difícil de reverter (commit, PR, escrita externa consumida por terceiros, board), (b) tem custo alto de execução por orquestração (dispatch de múltiplos agents/subagentes), ou (c) conduz cerimônia longa que não deve começar por iniciativa do modelo. Lente, postura, índice ou referência barata em contexto fica invocável pelo modelo — assim como ferramenta de propósito único disparada por intenção explícita do usuário (ex.: dirigir o app no simulador), mesmo que rode um build. Caso de borda decide pelo custo do disparo errado: skill que só propõe e para (`learn`) pode ser invocável; skill que executa cadeia inteira (`bug-report`) é slash-only.
```

- [ ] **Step 2: Ponteiro na legenda do INVENTORY**

Em `generate()`, na frase existente do slash-only, trocar o final `nunca por iniciativa do modelo.` por:

```python
        "nunca por iniciativa do modelo (critério: `docs/SKILL-CONTRACT.md` §Critério slash-only).",
```

- [ ] **Step 3: Regenerar e verificar**

Run: `python3 scripts/generate_inventory.py && python3 scripts/generate_inventory.py --check && bash scripts/check-governance.sh`
Expected: tudo verde; o parse da §Conformidade (gate check 3) não muda — a seção nova vem antes e o `sed` do gate começa em `/^## Conformidade/`.

- [ ] **Step 4: Commit (gated por NO-COMMIT)**

```bash
git add docs/SKILL-CONTRACT.md scripts/generate_inventory.py INVENTORY.md
git commit -m "docs(contract): written slash-only criterion, referenced from inventory legend"
```

---

### Task 7: CI — GitHub Actions com os gates existentes

**Files:**
- Create: `.github/workflows/ci.yml`

**Interfaces:**
- Consumes: os 4 comandos de gate + evals, todos já verdes localmente (baseline 2026-07-07).
- Produces: gate automático em push/PR. `claude plugin validate` fica FORA do v1 (exige instalar o CLI no runner — candidato pro censo).

- [ ] **Step 1: Criar o workflow**

```yaml
name: gates

on:
  push:
    branches: [main]
  pull_request:

jobs:
  gates:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Provenance gate
        run: bash scripts/check-provenance.sh
      - name: Governance gate
        run: bash scripts/check-governance.sh
      - name: Inventory up-to-date
        run: python3 scripts/generate_inventory.py --check
      - name: Hook evals (tier 1)
        run: ./evals/run-evals.sh
      - name: Shellcheck
        run: find plugins scripts evals -name '*.sh' -print0 | xargs -0 shellcheck
```

(`assets/` fica fora do shellcheck de propósito — `statusline-command.sh` é asset de usuário, não mecanismo do kit. shellcheck vem pré-instalado no runner ubuntu-latest.)

- [ ] **Step 2: Pré-verificação local do que dá**

Run: `bash scripts/check-provenance.sh && bash scripts/check-governance.sh && python3 scripts/generate_inventory.py --check && ./evals/run-evals.sh`
Expected: tudo verde. **shellcheck não está instalado nesta máquina** — opcional: `brew install shellcheck` e rodar o `find ... | xargs -0 shellcheck` local; senão, o primeiro run no branch é a verificação.

- [ ] **Step 3: Commit (gated por NO-COMMIT)**

```bash
git add .github/workflows/ci.yml
git commit -m "ci: run provenance/governance/inventory gates, hook evals and shellcheck"
```

- [ ] **Step 4: Push em branch + validação no Actions (ação do operador)**

Operador push num branch (`git push origin HEAD:ci-gates` via o alias SSH pessoal do operador — ver CLAUDE.md global) e abre o Actions. Se o shellcheck acusar findings nos hooks: triagem no PR — corrigir os triviais (quoting), **não** alterar semântica de hook de enforcement; finding que exigir mudança semântica vira follow-up anotado, com `# shellcheck disable=SCxxxx` justificado na linha.

---

### Task 8: Registro no CHANGELOG

**Files:**
- Modify: `CHANGELOG.md` (seção `[Unreleased]`)

**Interfaces:**
- Consumes: entregas dos Tasks 1–7.

- [ ] **Step 1: Adicionar em `### Adicionado`**

```markdown
- **Fase 1 da onda de refino pós-auditoria (2026-07-07, spec em `docs/superpowers/specs/2026-07-07-refino-pos-auditoria-design.md`)** — D17: registro machine-readable de provisórios em `docs/GOVERNANCE.md` §Provisórios ativos (12 itens das levas 2026-07-06/07), com check 5 no `check-governance.sh` (prazo vencido = gate vermelho) e marcador ⏳ no INVENTORY; coluna `Contrato (D14)` no INVENTORY expõe a dívida de conformidade (31 pendentes); critério slash-only escrito no `SKILL-CONTRACT.md`; CI (`.github/workflows/ci.yml`) rodando os 3 gates + evals tier-1 + shellcheck em push/PR.
```

- [ ] **Step 2: Adicionar em `### Alterado`**

```markdown
- D14 §Escopo: correção cirúrgica (linhas pontuais, sem mudar esqueleto/propósito) não constitui reforma nem obriga conformidade — decisão do dono, 2026-07-07.
- `review-local` (fix cirúrgico): mandato de tool Read para evidência citável no dispatch + claim do read-ledger anotada com o veredito do teste de runtime de 2026-07-07 (reads de subagent via Read entram no ledger da sessão-mãe; via Bash não).
```

- [ ] **Step 3: Verificar e commit (gated por NO-COMMIT)**

Run: `bash scripts/check-governance.sh`
Expected: verde (o CHANGELOG cita D14/D17 — ambos resolvem no ledger).

```bash
git add CHANGELOG.md
git commit -m "docs(changelog): record refino fase 1"
```

---

## Self-review (executado na escrita do plano)

- **Cobertura do spec §5 Fase 1**: 1.2→Task 7; 1.3→Task 2 (habilitado pelo Task 1); 1.4→Tasks 3+4; 1.5→Task 6; 1.6→Task 5. Item 1.1 (dogfood) = operador, declarado nas Global Constraints.
- **Ledger**: D17 nasce com seus dois validadores no mesmo commit (Task 3); D15/D16 não são citados em nenhum arquivo varrido pelo gate até suas fases (specs sob `docs/superpowers/` estão fora do censo de IDs — `--exclude-dir=superpowers`).
- **Consistência de tipos**: `collect_provisional()` retorna `dict[path,str]` consumido por `collect_skills/collect_agents` via `pop` (Tasks 3→4); `CONFORMITY_LINE_RE` casa o formato já lido pelo gate check 3 (Task 5); regex de data idêntica no bash (Task 3) e no Python (Task 4).
- **Placeholders**: nenhum TBD; todas as edições têm texto/código completo.
