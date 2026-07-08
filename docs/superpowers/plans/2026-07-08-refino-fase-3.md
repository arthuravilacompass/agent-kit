# Refino Fase 3 — Identidade pública + docs (D16) — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Consolidar docs 4→2 (GOVERNANCE absorve SKILL-CONTRACT; OPERATIONS absorve unwired/README), criar D16 (governança de descriptions com gate), reescrever o README na hierarquia nova com glossário, registrar a referência model-vs-effort no `core:methodology`, e preparar a higiene pública (versões, tag, instruções de About/topics/demo) — com os 5 gates verdes em **cada commit**.

**Architecture:** 6 tasks sequenciais, commit por task **direto na `main`** (convenção autorizada pelo operador na Fase 2, mesma data; **push e tag-push são ação do operador, nunca deste fluxo**). Ordem por dependência: docs 4→2 primeiro (D16 nasce dentro da §Contrato já absorvida), depois D16+find-and-cut, methodology, README (descreve a estrutura final), versões/CHANGELOG, e fechamento com review adversarial do range completo. Tag local só DEPOIS do review tratado.

**Tech Stack:** Markdown (docs + skills), bash (`check-governance.sh`), python3 stdlib (`generate_inventory.py`), manifests JSON.

**Fonte:** `docs/superpowers/specs/2026-07-07-refino-pos-auditoria-design.md` §5 (Fase 3), §6 (D16), §7 (riscos). Item 3.5 (model/effort) é adição do operador de 2026-07-08, fora da spec.

## Global Constraints

- **Gate quíntuplo verde antes de cada commit** (rodar da raiz do repo):
  ```bash
  bash scripts/check-provenance.sh
  claude plugin validate .          # NÃO está no CI — só local; obrigatório em toda task
  ./evals/run-evals.sh
  python3 scripts/generate_inventory.py --check
  bash scripts/check-governance.sh
  ```
- **NO-PUSH**: nenhum `git push` neste fluxo. Tag é criada local na Task 6, nunca pushada.
- **Council congelado**: `git diff plugins/council/` deve sair **vazio** ao fim de cada task — condição do censo (spec §3.3). O gate D16 novo ISENTA `plugins/council/` explicitamente.
- **Provisórios congelados no find-and-cut** (decisão do operador nesta fase, extensão da lógica do council): as descriptions dos 4 wired-provisórios não-council (`core/bug-report`, `team/refine-live`, `team/refine-async`, `mobile/figma-to-component`) NÃO são reescritas — todas já passam nos tetos; mexer em gatilho no meio da janela de validação contamina a medição do censo. Registrar no CHANGELOG.
- **INVENTORY.md nunca à mão**: sempre `python3 scripts/generate_inventory.py` e commit do resultado no MESMO commit que mudou skills/descriptions/gerador.
- **D16 nasce atômico**: a entrada no ledger, o texto normativo e o check no gate entram no MESMO commit (Task 2) — o check 2 do `check-governance.sh` deixa vermelho ID citado sem entrada.
- **Todo grep de aceite** usa `--exclude-dir=superpowers --exclude-dir=.superpowers` — spec e este plano citam os padrões varridos legitimamente. NUNCA "corrigir" a spec ou este plano.
- **CHANGELOG histórico é imutável** — entradas antigas não são reescritas; datas são permitidas LÁ e proibidas nos docs de superfície (README, OPERATIONS, GOVERNANCE — checagem: `grep -E '20[0-9]{2}-' <arquivo>` sem match).
- **Não tocar**: corpos de skill além dos listados (proibição da onda: "não reescrever skills por dentro" — as descriptions do find-and-cut e o bullet novo do methodology são as ÚNICAS exceções sancionadas), hooks de enforcement, `plugins/council/**`.
- Nunca escrever nomes reais de conta/empresa/cliente em arquivo do repo (denylist do `check-provenance.sh` casa por substring — inclusive o nome da conta GitHub do operador; as instruções de About/topics vão no REPORT ao operador, não em arquivo).
- Mensagens de commit em inglês, terminadas com `Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>`.
- Idioma (D14): docs e descriptions em pt-BR; código/comandos/paths em inglês.

## Estado medido (base dos números deste plano)

Descriptions em bytes UTF-8 (frontmatter `description:`), medição de 2026-07-08:

- Estouram 350: `core/methodology` 531 e `core/pipeline` 610 (classe roteador, teto 700 — passam); `mobile/deeplink-debug` 354 e `mobile/ga4-validate` 409 (cortar).
- Agregados atuais: core 3762 · council 1858 · team 811 · mobile 3258.
- Fora de forma ("responde só quando invocar"): `core/compound` ("Write-back Estrutural de Fim de Track" — sem gatilho nenhum).
- Versões atuais: core 0.3.0, council 0.1.0, team 0.1.0, mobile 0.2.0. Tags existentes: só `gate-day3-pass`. `gh` CLI não instalado.

---

### Task 1: Docs 4→2 (item 3.2)

GOVERNANCE absorve SKILL-CONTRACT como `## Contrato de SKILL.md (D14)`; OPERATIONS absorve unwired/README como `## 5.`; os dois parsers de §Conformidade mudam de arquivo e de nível de heading; nota de numeração dos IDs migra pro CHANGELOG.

**Files:**
- Modify: `docs/GOVERNANCE.md` (absorve o contrato; intro e entrada D14 do ledger atualizadas; nota de numeração sai)
- Delete: `docs/SKILL-CONTRACT.md`
- Modify: `docs/OPERATIONS.md` (nova §5 com a tabela de unwired, datas removidas)
- Modify: `unwired/README.md` (vira ponteiro de 3 linhas)
- Modify: `scripts/check-governance.sh` (check 3: `CONTRACT`, regex de seção)
- Modify: `scripts/generate_inventory.py` (`CONTRACT_PATH`, `collect_conformity`, texto do banner)
- Modify: `README.md` (só as 2 refs quebradas — linhas 125 e 127; a reescrita completa é Task 4)
- Modify: `unwired/handoff-gate/handoff-gate.sh` (comentário linha 15: `unwired/README.md` → `docs/GOVERNANCE.md`)
- Modify: `CHANGELOG.md` (nota de numeração + registro da consolidação)
- Regenerate: `INVENTORY.md`

**Interfaces:**
- Produces: seção `### Conformidade` DENTRO de `docs/GOVERNANCE.md`, imediatamente antes de `## Ledger de decisões` — a Task 2 adiciona `### Descriptions (D16)` ANTES dela. Formato de entrada inalterado: `` - `<path>` — <esqueleto> ``.

- [ ] **Step 1: Absorver o contrato no GOVERNANCE**

Em `docs/GOVERNANCE.md`, inserir entre `## Teto do tier sempre-ativo` e `## Ledger de decisões` a seção `## Contrato de SKILL.md (D14)` com o conteúdo de `docs/SKILL-CONTRACT.md` transformado assim:
1. Todo heading do contrato desce um nível: `## Os três esqueletos` → `### Os três esqueletos`, `### postura` → `#### postura`, etc. `## Conformidade` → `### Conformidade` (fica a ÚLTIMA subseção do contrato, imediatamente antes de `## Ledger de decisões`).
2. O H1 e a linha de intro do contrato ("Formato de autoria... Complementa `docs/GOVERNANCE.md`...") são substituídos por esta intro de seção:
   > Formato de autoria de toda skill do kit. Enforcement mecânico: `scripts/check-governance.sh` lê a §Conformidade abaixo.
3. Na `### Política de idioma`, o parêntese datado `(alargada na fusão de 2026-07-08)` é removido — GOVERNANCE não carrega data histórica (o CHANGELOG já registra a fusão); a linha vira `Exceção grandfathered: ...`. As datas FUNCIONAIS do doc (prazos D17 em §Provisórios ativos) não são afetadas.
4. O parágrafo **Escopo** e todo o resto entram verbatim.

Ainda em GOVERNANCE:
- Linha 3 (intro do doc): trocar `o formato de autoria de skills vive em `docs/SKILL-CONTRACT.md` (D14)` por `o formato de autoria de skills vive na §Contrato de SKILL.md deste doc (D14)`.
- Entrada **D14** do ledger: trocar `Texto normativo e lista de conformidade: `docs/SKILL-CONTRACT.md`` por `Texto normativo e lista de conformidade: §Contrato de SKILL.md deste doc`.
- Intro do `## Ledger de decisões`: remover a frase `A numeração é esparsa por origem: os IDs nasceram na numeração contínua do material de auditoria/spec do projeto de origem (fora deste repo — o gate de proveniência recusa importá-lo); este ledger cobre os IDs citados aqui, reconstituídos de evidência in-repo.` (migra pro CHANGELOG no Step 5). O resto da intro (regra do próximo ID livre + formato de entrada) fica.

Deletar `docs/SKILL-CONTRACT.md` (`git rm`).

- [ ] **Step 2: OPERATIONS absorve unwired/README; unwired/README vira ponteiro**

Em `docs/OPERATIONS.md`, adicionar ao final (após `## 4. Gate de qualidade`):

```markdown
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
```

Nota: as datas da tabela original (2026-07-07, 2026-07-06) NÃO entram — OPERATIONS é doc de superfície sem datas; os registros datados já existem no `CHANGELOG.md`.

Substituir TODO o conteúdo de `unwired/README.md` por:

```markdown
# unwired/

Matéria-prima genericizada aguardando prova de uso — nada aqui é carregado pelo Claude Code (custo de contexto zero). Inventário e racional por item: [docs/OPERATIONS.md](../docs/OPERATIONS.md) §5; ciclo de vida e regra de promoção: [docs/GOVERNANCE.md](../docs/GOVERNANCE.md).
```

Em `unwired/handoff-gate/handoff-gate.sh` linha 15, trocar a referência `unwired/README.md` por `docs/GOVERNANCE.md` (a regra de promoção vive lá).

- [ ] **Step 3: Atualizar os dois parsers de Conformidade**

`scripts/check-governance.sh` (check 3):

```bash
CONTRACT="docs/GOVERNANCE.md"
```

e o sed que extrai a seção passa a ser delimitado (a seção não é mais o fim do arquivo):

```bash
paths=$(sed -n '/^### Conformidade/,/^## /p' "$CONTRACT" | grep -oE '`plugins/[^`]+`' | tr -d '`')
```

Atualizar o comentário do check e a mensagem de erro que citavam o arquivo antigo (a variável `$CONTRACT` já resolve na mensagem).

`scripts/generate_inventory.py`:

```python
CONTRACT_PATH = os.path.join(REPO_ROOT, "docs", "GOVERNANCE.md")
```

Em `collect_conformity()`: docstring passa a citar `docs/GOVERNANCE.md`; o gatilho de entrada vira `line.startswith("### Conformidade")` e a saída vira `if in_section and (line.startswith("## ") or line.startswith("### ")): break`.

No `generate()`, o texto do banner que cita o critério slash-only:

```python
        "Skills marcadas **slash-only** têm `disable-model-invocation: true` no frontmatter: "
        "rodam só via comando explícito (`/<plugin>:<nome>`), nunca por "
        "iniciativa do modelo (critério: `docs/GOVERNANCE.md` §Contrato de SKILL.md).",
```

- [ ] **Step 4: Consertar as 2 refs do README (mínimo — reescrita é Task 4)**

- Linha 125: `([detalhe](unwired/README.md))` → `([detalhe](docs/OPERATIONS.md))`
- Linha 127: a célula de `docs/` vira: `[GOVERNANCE.md](docs/GOVERNANCE.md) (ciclo de vida, contrato de SKILL.md, ledger de decisões) e [OPERATIONS.md](docs/OPERATIONS.md) (operação do dono, incl. unwired/)`

- [ ] **Step 5: CHANGELOG**

Em `## [Unreleased]` → `### Alterado`, adicionar:

```markdown
- **Docs 4→2 (Fase 3, 2026-07-08)** — `docs/GOVERNANCE.md` absorveu `docs/SKILL-CONTRACT.md` (§Contrato de SKILL.md, D14) e `docs/OPERATIONS.md` absorveu `unwired/README.md` (§5, tabela de itens preservada sem datas; o README de `unwired/` virou ponteiro). Parsers de §Conformidade (`check-governance.sh` check 3, `generate_inventory.py`) atualizados pro novo local. Nota de numeração migrada do GOVERNANCE: a numeração do ledger é esparsa por origem — os IDs nasceram na numeração contínua do material de auditoria/spec do projeto de origem (fora deste repo; o gate de proveniência recusa importá-lo); o ledger cobre os IDs citados no repo, reconstituídos de evidência in-repo.
```

- [ ] **Step 6: Regenerar inventário, gates, commit**

```bash
python3 scripts/generate_inventory.py
# gate quíntuplo (Global Constraints)
git add -A && git commit -m "docs: consolidate SKILL-CONTRACT into GOVERNANCE and unwired/README into OPERATIONS (Fase 3 item 3.2)"
```

Aceite da task: 5 gates verdes; `ls docs/` mostra só GOVERNANCE.md, OPERATIONS.md e superpowers/; `grep -rn "SKILL-CONTRACT" --include='*.md' --include='*.sh' --include='*.py' --exclude=CHANGELOG.md . | grep -v superpowers | grep -v .worktrees` = 0 hits (CHANGELOG excluído: a entrada histórica da Fase 1 cita o arquivo legitimamente — histórico é imutável).

---

### Task 2: D16 — governança de descriptions + find-and-cut (item 3.3)

**Files:**
- Modify: `docs/GOVERNANCE.md` (nova `### Descriptions (D16)` no §Contrato, ANTES de `### Conformidade`; entrada D16 no ledger)
- Modify: `scripts/check-governance.sh` (check 6 novo)
- Modify: `scripts/generate_inventory.py` (publica agregado por plugin)
- Modify: `plugins/core/skills/compound/SKILL.md` (description)
- Modify: `plugins/mobile/skills/deeplink-debug/SKILL.md` (description)
- Modify: `plugins/mobile/skills/ga4-validate/SKILL.md` (description)
- Modify: `CHANGELOG.md`
- Regenerate: `INVENTORY.md`

**Interfaces:**
- Consumes: `### Conformidade` como última subseção do §Contrato (Task 1). A D16 entra ANTES dela para que o parser de conformidade (que lê até o próximo heading) não engula linhas da D16.
- Produces: check 6 no gate com tetos hardcoded (padrão do repo: `CEILING=16384` hardcoded com doc como fonte).

- [ ] **Step 1: Texto normativo D16 no GOVERNANCE**

Inserir em `docs/GOVERNANCE.md`, dentro de `## Contrato de SKILL.md (D14)`, imediatamente antes de `### Conformidade`:

```markdown
### Descriptions (D16)

A `description` do frontmatter responde só **"quando invocar"** — gatilho situacional citável, não resumo do que a skill faz nem história. Tetos em bytes UTF-8 sobre o valor da linha `description:`, verificados por `scripts/check-governance.sh` (check 6):

- **≤ 350 bytes** por skill (esqueletos postura e procedimento).
- **≤ 700 bytes** para a classe roteador de invocação — descriptions que carregam a tabela de gatilhos de roteamento: `pipeline`, `methodology` e `mobx`. Cortar gatilho de roteador degrada a conversão que o censo mede.
- **Agregado por plugin**: core ≤ 4096 · team ≤ 1024 · mobile ≤ 3584 bytes. Mesma pressão de seleção do teto do sempre-ativo: description nova compete por espaço; subir teto é decisão de ledger.
- **`plugins/council/` está isento até o censo** — descriptions congeladas como condição da medição de conversão das posturas (§Provisórios ativos); o teto passa a valer pro council na decisão do censo.

A regra de forma (só "quando invocar") é critério de review; os tetos são o enforcement mecânico.
```

No `## Ledger de decisões`, adicionar após a entrada D15:

```markdown
- **D16** — Governança de descriptions: regra de forma (description responde só "quando invocar") + tetos por classe (350 bytes; roteador 700) + teto agregado por plugin, com `council` isento até o censo. Texto normativo: §Contrato de SKILL.md → Descriptions deste doc. Enforcement: `scripts/check-governance.sh` (check 6); agregado publicado por `scripts/generate_inventory.py` no `INVENTORY.md`.
```

- [ ] **Step 2: Check 6 no gate**

Adicionar a `scripts/check-governance.sh`, após o check 5 e antes do `exit $fail`:

```bash
# 6) Descriptions (D16): teto por skill (350; roteador 700) + agregado por plugin.
# council isento até o censo (docs/GOVERNANCE.md §Descriptions). Tetos hardcoded
# aqui, doc como fonte — mesmo padrão do CEILING do sempre-ativo.
if python3 - <<'PYEOF'
import os, re, sys

CEIL_DEFAULT, CEIL_ROUTER = 350, 700
ROUTERS = {"pipeline", "methodology", "mobx"}
AGG = {"core": 4096, "team": 1024, "mobile": 3584}
fail = 0
for plugin, agg_ceil in AGG.items():
    base = os.path.join("plugins", plugin, "skills")
    if not os.path.isdir(base):
        print(f"ERRO: {base} inexistente — D16 não medido")
        fail = 1
        continue
    total = 0
    for name in sorted(os.listdir(base)):
        p = os.path.join(base, name, "SKILL.md")
        if not os.path.isfile(p):
            continue
        with open(p, encoding="utf-8") as f:
            text = f.read()
        # description vive no frontmatter (delimitado pelos dois primeiros '---');
        # restringir a busca evita casar 'description:' em corpo de skill.
        parts = text.split("\n---", 2)
        fm = parts[0] + ("\n---" if len(parts) > 1 else "")
        m = re.search(r"^description: (.*)$", fm, re.M)
        if not m:
            print(f"ERRO: {p} sem 'description:' no frontmatter (D16)")
            fail = 1
            continue
        n = len(m.group(1).encode("utf-8"))
        total += n
        ceil = CEIL_ROUTER if name in ROUTERS else CEIL_DEFAULT
        if n > ceil:
            print(f"ERRO: description de {plugin}:{name} mede {n} bytes — teto {ceil} (D16)")
            fail = 1
    if total > agg_ceil:
        print(f"ERRO: agregado de descriptions de {plugin} mede {total} bytes — teto {agg_ceil} (D16)")
        fail = 1
    else:
        print(f"OK: descriptions de {plugin} — agregado {total} <= {agg_ceil} bytes (D16)")
sys.exit(fail)
PYEOF
then :; else fail=1; fi
```

- [ ] **Step 3: Gerador publica o agregado**

Em `scripts/generate_inventory.py`, função `render_plugin_section`, logo após `lines.extend(render_table(["Skill", "Contrato (D14)", "Descrição"], rows))` e antes do `lines.append("")` seguinte, inserir:

```python
    desc_total = sum(len(s["description"].encode("utf-8")) for s in skills)
    lines.append("")
    lines.append(f"Agregado de descriptions (D16): {desc_total} bytes.")
```

(O agregado é publicado pros 4 plugins, council incluso — a isenção do council é só do TETO, no gate.)

- [ ] **Step 4: Find-and-cut (3 descriptions; provisórios e council intocados)**

`plugins/core/skills/compound/SKILL.md` — description atual não tem gatilho ("Write-back Estrutural de Fim de Track"). Nova:

```
description: Invoque no fim de um track de trabalho relevante — gera o handoff estruturado da sessão (estado, decisões, próximos passos) que sobrevive ao /clear e alimenta a retomada via plan-autoload.
```

`plugins/mobile/skills/deeplink-debug/SKILL.md` (354 → ≤350): remover exatamente o trecho `, quebrou depois de reativar` da lista de sintomas; resto verbatim.

`plugins/mobile/skills/ga4-validate/SKILL.md` (409 → ≤350). Nova:

```
description: Invoque para validar tracking GA4 (tela × evento, antes × depois de uma mudança) num app Flutter no simulador — dirige o app, captura o evento real com params e monta a tabela de CTs com report visual. Gatilhos em pt-BR — "valida os eventos GA4 dessa tela", "confirma o tracking antes e depois dessa mudança".
```

Verificar cada uma com:

```bash
python3 -c "
import re,sys
for p in ['plugins/core/skills/compound/SKILL.md','plugins/mobile/skills/deeplink-debug/SKILL.md','plugins/mobile/skills/ga4-validate/SKILL.md']:
    m=re.search(r'^description: (.*)$', open(p,encoding='utf-8').read().split('\n---',2)[0], re.M)
    print(len(m.group(1).encode('utf-8')), p)
"
```

Esperado: todos ≤ 350.

- [ ] **Step 5: CHANGELOG**

Em `### Adicionado`:

```markdown
- **D16 — governança de descriptions (Fase 3, 2026-07-08)** — regra de forma ("quando invocar"), tetos por classe (350 bytes; roteador 700: `pipeline`, `methodology`, `mobx`) e agregado por plugin (core 4096 · team 1024 · mobile 3584), com check 6 novo no `check-governance.sh` e agregado publicado no `INVENTORY.md`. Find-and-cut aplicado: `compound` (ganhou gatilho), `deeplink-debug` e `ga4-validate` (cortadas pro teto). Congelados por condição de medição do censo: `plugins/council/` inteiro (condição da spec) e as descriptions dos 4 wired-provisórios não-council (`bug-report`, `refine-live`, `refine-async`, `figma-to-component`) — decisão do operador estendendo a mesma lógica; o teto passa a valer pra eles na decisão do censo.
```

- [ ] **Step 6: Regenerar, verificar council intacto, gates, commit**

```bash
python3 scripts/generate_inventory.py
git diff --stat plugins/council/   # esperado: saída vazia
# gate quíntuplo
git add -A && git commit -m "feat(governance): D16 description governance — form rule, per-class and per-plugin byte ceilings, gate check 6 (Fase 3 item 3.3)"
```

---

### Task 3: Referência model-vs-effort no methodology (item 3.5 — adição do operador)

**Files:**
- Modify: `plugins/core/skills/methodology/SKILL.md` (§Referência Técnica → Claude Code)

- [ ] **Step 1: Adicionar o bullet**

Em `## Referência Técnica` → `### Claude Code`, adicionar como último bullet da lista (após o bullet **Advisor nativo**):

```markdown
- **Model vs. effort**: dois eixos, não um. Trocar de modelo troca os pesos — o que o Claude *sabe*; effort regula quanto trabalho ele faz antes de dar por pronto — quantos arquivos lê, quanto verifica, quão longe vai numa tarefa multi-step sem checar com você. Resultado errado: primeiro conserte o input (prompt, tools, skills, contexto — a causa mais comum de erro não é setting); se ele pulou arquivo/teste/verificação, suba effort ("não tentou o suficiente"); se leu tudo, claramente tentou e segue confiantemente errado, suba de modelo ("não sabia o suficiente"). Effort é preferência geral por domínio, não ajuste por tarefa; em trecho rotineiro prolongado, descer de modelo corta custo e latência sem perder qualidade.
```

- [ ] **Step 2: Gates, commit**

A description do methodology não muda (531 bytes, classe roteador — segue ≤ 700; check 6 continua verde). INVENTORY não muda (corpo de skill não entra no inventário) — `--check` confirma.

```bash
# gate quíntuplo
git add plugins/core/skills/methodology/SKILL.md
git commit -m "docs(methodology): add model-vs-effort decision reference (knowing more vs. trying harder)"
```

---

### Task 4: README nova hierarquia + glossário (item 3.1)

**Files:**
- Modify: `README.md` (reescrita completa)

- [ ] **Step 1: Reescrever o README**

Conteúdo integral novo (as seções `Instalação`, `Requisitos` e `Princípios` reaproveitam o texto atual verbatim onde indicado):

````markdown
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

<!-- verbatim das seções atuais "1. Clonar (uma vez)" até "Desinstalar", sem mudança -->

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

<!-- verbatim da seção atual "Requisitos" -->

## Glossário

- **wired** — artefato que vive em `plugins/` e é carregado pelo Claude Code; custa contexto toda sessão, e por isso exige uso real comprovado pra entrar e pra permanecer.
- **unwired** — matéria-prima genericizada em `unwired/`; custo de contexto zero, aguardando prova de uso pra ser promovida.
- **grillado** — que passou pelo `grill-me`: interrogatório adversarial (entrevista ou escalação a um reviewer mais forte) que pressiona as decisões antes de dar um plano ou entrega por pronto.
- **gate** — verificação mecânica que precisa sair verde antes de qualquer commit: proveniência, manifests, evals, inventário e governança. Não depende de o modelo obedecer.
- **censo** — medição de uso real ao fim de um ciclo de cliente (`census_usage.py`) que decide o que continua wired, o que é demovido e o que sai; também resolve os prazos dos itens provisórios.

## Princípios

<!-- verbatim da seção atual "Princípios" (3 bullets) -->

---

[INVENTORY.md](INVENTORY.md) · [docs/GOVERNANCE.md](docs/GOVERNANCE.md) · [docs/OPERATIONS.md](docs/OPERATIONS.md) · [CHANGELOG.md](CHANGELOG.md)
````

Os três blocos `<!-- verbatim ... -->` são instruções de montagem: copiar o texto atual do README dessas seções sem alteração (Instalação: linhas 44–96 atuais; Requisitos: linhas 114–118; Princípios: linhas 130–134).

- [ ] **Step 2: Verificações da task**

```bash
grep -E '20[0-9]{2}-' README.md                  # esperado: sem match (sem datas)
grep -c 'Glossário' README.md                    # esperado: 1
# contagens da tabela dos plugins batem com o INVENTORY:
grep -E '^### (Skills|Agents|Hooks|Scripts|MCP) \(' INVENTORY.md
```

Conferir manualmente: todo termo interno usado no README (wired, unwired, grillado, gate, censo) tem entrada no glossário; a primeira dobra (título + parágrafo de identidade + bandeira) responde o-que/por-que/como sem tabela no meio do caminho.

- [ ] **Step 3: CHANGELOG + gates + commit**

Em `### Alterado`:

```markdown
- **README na hierarquia de identidade pública (Fase 3, 2026-07-08)** — frase de identidade → ledger de citação como bandeira → fluxo de entrega → tabela dos 4 plugins → seções avançadas (Conselho, governança, estrutura) → glossário de 5 termos (wired, unwired, grillado, gate, censo). Slot de demo (asciinema/GIF do pipeline) marcado como comentário até a gravação manual do operador.
```

```bash
# gate quíntuplo
git add README.md CHANGELOG.md && git commit -m "docs(readme): public-identity hierarchy — flag, flow, plugin table, glossary (Fase 3 item 3.1)"
```

---

### Task 5: Versões + registro da fase (item 3.4, parte commitável)

**Files:**
- Modify: `plugins/core/.claude-plugin/plugin.json` (`"version": "0.4.0"`)
- Modify: `plugins/mobile/.claude-plugin/plugin.json` (`"version": "0.2.1"`)
- Modify: `CHANGELOG.md`

Racional: core ganhou conteúdo novo (bullet do methodology) + description reescrita → minor (0.3.0 → 0.4.0); mobile só teve descriptions cortadas → patch (0.2.0 → 0.2.1); team e council intocados (team: os dois candidatos a mudança eram provisórios congelados; chat-draft já conforme).

- [ ] **Step 1: Bumps + CHANGELOG**

Editar os dois `plugin.json`. Em `### Alterado` do CHANGELOG:

```markdown
- **Versões (Fase 3, 2026-07-08)** — core 0.3.0 → 0.4.0 (referência model-vs-effort no `methodology`, description do `compound` com gatilho); mobile 0.2.0 → 0.2.1 (descriptions de `deeplink-debug` e `ga4-validate` cortadas pro teto D16). Tag `v0.4.0` (versão do plugin-âncora) criada local após o review adversarial da fase; push da tag é ação do operador.
```

- [ ] **Step 2: Gates + commit**

```bash
claude plugin validate .    # versões novas validam
# gate quíntuplo completo
git add -A && git commit -m "chore(release): bump core to 0.4.0 and mobile to 0.2.1 (Fase 3 item 3.4)"
```

---

### Task 6: Fechamento — review adversarial do range, tag, report ao operador

- [ ] **Step 1: Review adversarial do range completo**

Review cego do diff `fca2baa..HEAD` (histórico da onda: o último move mecânico teve 15 defeitos; a Fase 2 achou mais). O review EXECUTA os critérios de aceite (não só lê o diff):

```bash
bash scripts/check-provenance.sh && claude plugin validate . && ./evals/run-evals.sh \
  && python3 scripts/generate_inventory.py --check && bash scripts/check-governance.sh
ls docs/                                          # GOVERNANCE.md, OPERATIONS.md, superpowers/
git log --oneline fca2baa..HEAD                   # 5 commits, um por task
git diff fca2baa..HEAD --stat -- plugins/council/ # vazio
grep -E '20[0-9]{2}-' README.md docs/OPERATIONS.md   # sem match (GOVERNANCE carrega datas FUNCIONAIS de D17 — fora deste check)
grep -n 'fusão de 20' docs/GOVERNANCE.md              # sem match (data histórica não entra na absorção)
grep -rn 'SKILL-CONTRACT' --include='*.md' --include='*.sh' --include='*.py' --exclude=CHANGELOG.md . \
  --exclude-dir=superpowers --exclude-dir=.superpowers --exclude-dir=.worktrees   # 0 hits (histórico do CHANGELOG é imutável e cita o arquivo legitimamente)
```

Findings CONFIRMED do review são corrigidos ANTES do Step 2, com gates verdes de novo.

- [ ] **Step 2: Tag local (NUNCA pushada neste fluxo)**

```bash
git tag v0.4.0
git tag --list 'v*'   # esperado: v0.4.0
```

- [ ] **Step 3: Report ao operador — passos manuais restantes do item 3.4**

O report final da sessão entrega este checklist (nada disso vai em arquivo do repo — denylist de proveniência):

1. **Push**: `git push origin main --tags` (do operador; alias SSH pessoal).
2. **About do GitHub** (web UI ou `gh repo edit` de máquina com `gh`): description sugerida — `Disciplina de engenharia executável para Claude Code — metodologia, lentes de decisão e enforcement determinístico em 4 plugins (core, council, team, mobile).`
3. **Topics**: `claude-code`, `claude-plugins`, `flutter`, `agentic-coding`.
4. **Demo**: gravar ~30s do `core:pipeline` recebendo tarefa crua (asciinema ou GIF), commitar em `assets/` e substituir o comentário `<!-- demo: ... -->` do README pelo embed. Até lá, o aceite "mídia no README" da spec fica **aberto**.

## Critérios de aceite da fase (spec §5 Fase 3 + §9)

- 3.1: README reordenado (identidade → bandeira → fluxo → tabela → avançadas → glossário); zero termo interno sem glossário; zero data.
- 3.2: `docs/` com 2 docs canônicos; gates verdes pós-mudança; zero referência a `SKILL-CONTRACT`; nota de numeração no CHANGELOG.
- 3.3: check 6 (D16) verde; agregado por plugin publicado no INVENTORY; `git diff plugins/council/` vazio; D16 resolve no ledger.
- 3.4: versões bumpadas e coerentes com a tag local `v0.4.0`; About/topics/push/demo entregues como checklist do operador (bloqueados por `gh` ausente e gravação manual).
- 3.5: bullet model-vs-effort na §Referência Técnica → Claude Code do `methodology`.
