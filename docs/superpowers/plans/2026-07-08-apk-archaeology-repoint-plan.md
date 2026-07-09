# apk-archaeology v0 — Re-apontamento (aceleração) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Trazer o centro de gravidade do v0 de volta pra aceleração — tornar o passo 5 executável, atravessar o último passo uma vez produzindo um artefato de handoff real, e corrigir o critério de aceite na origem — sem refazer o v0.

**Architecture:** 3 moves do re-apontamento mínimo (design `2026-07-08-apk-archaeology-repoint-design.md`): (1) `node → arquivo` em `extract_graph.py` + particionamento mecânico por prefixo de pacote no `SKILL.md`; (2) um artefato de handoff na língua do time (US candidata + CA/Cenário Gherkin + esqueleto DTO) a partir dos dados já em disco; (3) emenda do AC da §9 do spec original. Opera sobre o run do NewPipe já em `~/dev/apk-archaeology-lab/demo-run/newpipe/`.

**Tech Stack:** Python 3 stdlib puro (convenção do repo — selftest com `assert` + exit code, sem pytest), Markdown. Sem dependências novas.

> **Atualização de execução (2026-07-08).** A frente F1 (re-run em APK nova) foi **dobrada neste
> re-apontamento** por decisão do operador: o NewPipe é proxy público pobre (sem WebView, raso em
> regra) pro alvo real. Fixture de aceleração passou a ser **WordPress-Android** (pública, GPLv2,
> híbrida WebView) — run em `~/dev/apk-archaeology-lab/demo-run/wordpress/` (sha256 do APK em
> `provenance.txt` do run). As Tasks abaixo foram escritas pro NewPipe; aplicam-se ao run do
> WordPress *mutatis mutandis* (Task 1/move 1a é agnóstica de APK, já feita — commit `7e5c8db`).
> **Refino verificado no dry-run** (Task 2/move 1b): particionar pela chave top-level do `classify`
> degenera (`org/wordpress` = 9596 num blob); a regra real escrita no SKILL.md é **prefixo de pacote
> em profundidade** (raiz + ~3 segmentos → ~1121 partições de escala-feature). Handoff produzido:
> `examples/wordpress-handoff.md` (não `newpipe-handoff.md`). Move #3 e AC §9 inalterados no conteúdo
> (o AC aponta pro arquivo WordPress). O run WordPress revelou o **limite WebView**, incorporado ao §10 do spec.

## Global Constraints

- **Executar SÓ após a migração pro inglês estar mesclada na `main`** — `SKILL.md` e `examples/` (plugin `mobile`) estão no escopo da migração; editar antes = retrabalho/conflito.
- **Não executar enquanto a sessão de migração estiver ativa no mesmo working tree** — rodar em branch/worktree limpa a partir da `main` já migrada (risco de commit varrer WIP alheio / checkout race).
- **Idioma por arquivo**: `SKILL.md` e `examples/*.md` (plugin migrado) → **EN**; corpo de `extract_graph.py` (docstrings/comentários) → **pt-BR** (migração só toca `# desc:`); `docs/superpowers/specs|plans` → **pt-BR** (fora de escopo).
- **Schema `node_files` aditivo** — preservar `nodes` como lista de nomes simples; NÃO trocar por lista de objetos (quebraria selftest/consumidores). Nome simples colide → valor é **lista** de arquivos.
- **Zero número novo de ROI/produtividade/tempo-economizado** (spec original §10/§13).
- **Redação de segredo intacta** — nada da Telecorp; nenhum literal fora de `~/dev/apk-archaeology-lab/` (spec original §8).

## Preconditions (antes da Task 1)

- [ ] Migração EN mesclada na `main` (checar: `SKILL.md` do apk-archaeology em inglês).
- [ ] Branch de trabalho criada a partir da `main` migrada (`git checkout -b feat/apk-archaeology-repoint`).
- [ ] Run em disco presente: `~/dev/apk-archaeology-lab/demo-run/newpipe/{graph.json,endpoints.json,jadx/sources}`. Se ausente, regenerar via plano original Task 7 steps 1-2.

---

### Task 1: `extract_graph.py` — join `node → arquivo` (move #1a)

**Files:**
- Modify: `plugins/mobile/skills/apk-archaeology/scripts/extract_graph.py` (função `extract_graph`, ~L95-130)
- Test: `plugins/mobile/skills/apk-archaeology/scripts/selftest_extract_graph.py`

**Interfaces:**
- Produces: `extract_graph()` passa a retornar, além de `nodes`/`edges`/`artifact_warnings`, a chave `node_files: dict[str, list[str]]` — nome simples de classe → lista ordenada de caminhos de arquivo (relativos a `sources_dir`) onde uma classe de negócio com esse nome foi declarada. Mesma filtragem dos `nodes` (sintética e `unclassifiable` nunca entram).

- [ ] **Step 1: Estender o selftest (falha primeiro)**

Adicionar em `selftest_extract_graph.py`, logo após o bloco de asserts de classe sintética (após a linha `assert not any(n.startswith("LoginActivity$") ...`):

```python
        # node_files: join node -> arquivo(s) reais (move #1a do re-apontamento)
        assert "LoginActivity" in result["node_files"], result["node_files"]
        assert any(
            f.endswith("LoginActivity.java") for f in result["node_files"]["LoginActivity"]
        ), result["node_files"]["LoginActivity"]
        # a mesma filtragem dos nodes vale pra node_files:
        assert not any(
            k.startswith("LoginActivity$") for k in result["node_files"]
        ), "classe sintética vazou pra node_files"
        assert "b" not in result["node_files"], "classe unclassifiable vazou pra node_files"
```

- [ ] **Step 2: Rodar o teste, confirmar que falha**

Run: `python3 plugins/mobile/skills/apk-archaeology/scripts/selftest_extract_graph.py`
Expected: `KeyError: 'node_files'` (a chave ainda não existe no retorno).

- [ ] **Step 3: Implementar `node_files` em `extract_graph()`**

Em `plugins/mobile/skills/apk-archaeology/scripts/extract_graph.py`, na função `extract_graph`:

Adicionar a inicialização junto de `all_classes`:
```python
    all_classes = set()
    node_files = {}  # nome simples -> conjunto de arquivos (relativos) onde foi declarada
```

Dentro do laço de arquivos, calcular o caminho relativo e registrar por classe:
```python
                full = os.path.join(root, fname)
                rel = os.path.relpath(full, sources_dir)
                for class_name, parents, interfaces in parse_file(full):
                    all_classes.add(class_name)
                    node_files.setdefault(class_name, set()).add(rel)
                    for parent in parents:
                        raw_edges.append((class_name, parent, "extends"))
                    for iface in interfaces:
                        raw_edges.append((class_name, iface, "implements"))
```

Incluir `node_files` no dict de retorno (ordenado e determinístico):
```python
    return {
        "nodes": sorted(all_classes),
        "node_files": {k: sorted(v) for k, v in sorted(node_files.items())},
        "edges": edges,
        "artifact_warnings": sorted(set(artifact_warnings)),
    }
```

- [ ] **Step 4: Rodar o teste, confirmar que passa**

Run: `python3 plugins/mobile/skills/apk-archaeology/scripts/selftest_extract_graph.py`
Expected: `OK: todas as asserções passaram (edges corretos, unclassifiable excluído, sintética filtrada)`

- [ ] **Step 5: Regenerar `graph.json` do run real e conferir `node_files`**

Run:
```bash
python3 plugins/mobile/skills/apk-archaeology/scripts/extract_graph.py \
  ~/dev/apk-archaeology-lab/demo-run/newpipe/jadx/sources \
  ~/dev/apk-archaeology-lab/demo-run/newpipe/classify.json \
  --out ~/dev/apk-archaeology-lab/demo-run/newpipe/graph.json
python3 -c "import json; g=json.load(open('$HOME/dev/apk-archaeology-lab/demo-run/newpipe/graph.json')); print('nodes:', len(g['nodes']), '| node_files:', len(g['node_files']))"
```
Expected: `node_files` não-vazio, contagem próxima de `nodes` (cada node com ≥1 arquivo).

- [ ] **Step 6: Commit**

```bash
git add plugins/mobile/skills/apk-archaeology/scripts/extract_graph.py \
        plugins/mobile/skills/apk-archaeology/scripts/selftest_extract_graph.py
git commit -m "feat(mobile): extract_graph node->file join (apk-archaeology repoint move 1a)"
```

---

### Task 2: `SKILL.md` passo 5 — particionamento mecânico por prefixo de pacote (move #1b)

**Files:**
- Modify: `plugins/mobile/skills/apk-archaeology/SKILL.md` (passo 5 "Synthesis of Dimension A" — o bloco de ressalva + a instrução de particionamento)

**Interfaces:**
- Consumes: `graph.json` com `node_files` (Task 1) + `classify.json`.
- Produces: nada programático — instrução de orquestração mecanicamente executável (remove a dependência de escolha manual de cluster).

> Nota de idioma: `SKILL.md` estará em **inglês** pós-migração. Escrever o conteúdo abaixo em EN, adaptando à prosa migrada ao redor. O texto abaixo é a INTENÇÃO do conteúdo, não string a colar literal.

- [ ] **Step 1: Substituir a ressalva "known caveat" e a instrução de cluster manual**

Remover o bloco de ressalva (`> **Ressalva conhecida ...**`) e a frase "escolha clusters pequenos e com nome reconhecível à mão". Substituir por uma instrução mecânica (conteúdo, em EN):

- Particionar por **prefixo de pacote**: para cada chave `business-candidate` em `classify.json`, a partição é o conjunto de classes cujo arquivo (via `graph.json["node_files"]`) está sob aquele diretório de pacote.
- Cada partição carrega seus arquivos (de `node_files`), os endpoints de `endpoints.json` cujo `file` cai na partição, e os entry points nomeados + string resources como âncora.
- Componente conexo bruto fica documentado como alternativa descartada (degenerou em 1 blob no app real testado).

- [ ] **Step 2: Verificar que o particionamento roda mecanicamente no run real (smoke, throwaway)**

Run:
```bash
python3 - <<'PY'
import json, os
run = os.path.expanduser("~/dev/apk-archaeology-lab/demo-run/newpipe")
g = json.load(open(f"{run}/graph.json"))
c = json.load(open(f"{run}/classify.json"))
biz = [k for k, v in c["packages"].items() if v["bucket"] == "business-candidate"]
parts = {}
for cls, files in g["node_files"].items():
    for f in files:
        for key in biz:
            if f.startswith(key + "/"):
                parts.setdefault(key, set()).add(cls)
                break
top = sorted(parts, key=lambda k: -len(parts[k]))[:10]
for k in top:
    print(f"{k}: {len(parts[k])} classes")
print("total partitions:", len(parts))
PY
```
Expected: várias partições nomeadas por pacote com contagens sãs (não um único blob de centenas) — confirma que a unidade de trabalho é mecânica, não escolhida à mão.

- [ ] **Step 3: Commit**

```bash
git add plugins/mobile/skills/apk-archaeology/SKILL.md
git commit -m "docs(mobile): mechanical package-prefix partitioning in apk-archaeology step 5 (repoint move 1b)"
```

---

### Task 3: `examples/newpipe-handoff.md` — atravessar o último passo (move #2)

**Files:**
- Create: `plugins/mobile/skills/apk-archaeology/examples/newpipe-handoff.md`

**Interfaces:**
- Consumes: uma partição mecânica (Task 2; fallback: partição "Streaming Services" já sintetizada na demo), os arquivos-fonte dela, e `endpoints.json`.
- Produces: artefato de handoff consumível por `tech-breakdown`/`spec-refine` (US candidata + CA como cenário Gherkin + esqueleto DTO).

> Não é TDD — é execução + curadoria. Idioma: **EN** (plugin migrado). Formato **provisional** (design §5) — confirmar campos no kickoff.

- [ ] **Step 1: Escolher a partição e reunir insumos**

Escolher 1 partição da Task 2 (preferir uma com classes nomeadas e endpoints associados; fallback: "Streaming Services" = `StreamingService`/`YoutubeService`/`BandcampService`/`PeertubeService`). Reunir: arquivos-fonte da partição (via `node_files`), endpoints de `endpoints.json` cujo `file` cai na partição.

- [ ] **Step 2: Sintetizar as User Stories candidatas da partição**

Seguir o passo 5 do `SKILL.md`: regras observáveis viram US candidatas — "As a `<role>`, I want `<capability>`, so that `<benefit>`". Só a **capability** ancorada (tier `high`/`medium`/`unanchored` + `arquivo:linha`); **papel e benefício marcados como inferência** (não estão no código). Reaproveitar as claims já verificadas da demo quando a partição coincidir (ex.: os 4 claims `alta` verificados 4/4).

- [ ] **Step 3: Gerar CA como Cenário Gherkin (por US) + esqueleto DTO (Dimensão B)**

CA/Cenário: para cada US de tier alto/médio (Step 2), o Critério de Aceite como cenário Gherkin `Given/When/Then` tagueado `@legacy-observed @tier-<t>` + `arquivo:linha` + `# PO must ratify`. O CA é o cenário testável da US — deriva da capability já sintetizada, não é síntese nova.

DTO: para 3-5 endpoints `business` da partição, stub Dart DTO+Entity+mapper, cada um anotado com endpoint de origem + `arquivo:linha` + tier + banner `legacy-observed ≠ target-approved`.

- [ ] **Step 4: Montar `examples/newpipe-handoff.md`**

Estrutura (EN):
```markdown
# apk-archaeology — v0 handoff artifact (NewPipe)

> Downstream artifact consumable by `tech-breakdown`/`spec-refine`. Format provisional
> (design §5), pinned at first real client use. Companion to `newpipe-demo.md` (viability);
> this proves the acceleration step, not the fidelity of extraction.
> **legacy-observed ≠ target-approved** — every story/criterion below is a hypothesis about
> the LEGACY app, input for PO reconciliation, never an acceptance criterion on its own.
> A user story's **role** and **benefit** are INFERENCE (not in the bytecode); only the
> capability is anchored to evidence.

## Candidate user stories — partition `<package-key>` (Dimension A)
### US-1
As a `<role — inferred>`, I want `<capability — [tier], evidence: <file>:<line>>`,
so that `<benefit — inferred>`.

**Acceptance criteria (legacy-observed):**
```gherkin
@legacy-observed @tier-<t>
Scenario: <capability expressed as behavior>
  Given <context>
  When <action>
  Then <observed legacy outcome>   # <file>:<line> — PO must ratify
```

## API contracts (Dimension B) → DTO skeleton
### `<DtoName>` — from `<endpoint>` (`<file>:<line>`, tag=business, tier: <t>)
```dart
// legacy-observed ≠ target-approved — PO must ratify before this is a contract
class <DtoName> { /* fields inferred; confidence: <tier> */ }
```
```

- [ ] **Step 5: Conferir aceite do artefato**

- [ ] ≥1 US candidata com capability ancorada (tier + `arquivo:linha`), papel/benefício flagados como inferência, banner de ratificação presente.
- [ ] CA como cenário Gherkin por US de tier alto/médio, tagueado `@legacy-observed` + `arquivo:linha`.
- [ ] Esqueleto DTO de ≥3 endpoints, cada um citando origem.
- [ ] Nenhum segredo/endpoint da Telecorp; só conteúdo do NewPipe (fonte pública).

- [ ] **Step 6: Commit**

```bash
git add plugins/mobile/skills/apk-archaeology/examples/newpipe-handoff.md
git commit -m "docs(mobile): add apk-archaeology v0 handoff artifact (repoint move 2)"
```

---

### Task 4: Emendar o AC da §9 (move #3 — fix na origem)

**Files:**
- Modify: `docs/superpowers/specs/2026-07-08-apk-archaeology-design.md` (§9, lista "Critério de aceite da demo")
- Modify: `plugins/mobile/skills/apk-archaeology/examples/newpipe-demo.md` (cross-ref pro handoff)

**Interfaces:**
- Produces: define-done que exige a etapa de aceleração, não só confiança.

> Idioma: spec original → **pt-BR** (fora do escopo da migração). Demo → **EN** (plugin migrado).

- [ ] **Step 1: Adicionar a linha de handoff ao AC da §9 (pt-BR)**

Em `docs/superpowers/specs/2026-07-08-apk-archaeology-design.md` §9, acrescentar à lista "Critério de aceite da demo":

```markdown
- Produz ao menos um artefato de jusante no formato de handoff — ≥1 User Story candidata
  (Dimensão A) com Critério de Aceite como cenário Gherkin (`legacy-observed`) + esqueleto
  DTO de ≥3 endpoints da Dimensão B (`examples/newpipe-handoff.md`), consumível por
  `tech-breakdown`/`spec-refine`, demonstrando as etapas Spec/Implementação/Testes de §11.
  Sem esta linha o define-done aponta só pra confiança.
```

- [ ] **Step 2: Cross-ref na demo (EN)**

Em `examples/newpipe-demo.md`, na seção "O que isto NÃO é" / equivalente migrado, apontar que a etapa de aceleração é demonstrada no artefato companheiro `newpipe-handoff.md`.

- [ ] **Step 3: Commit**

```bash
git add docs/superpowers/specs/2026-07-08-apk-archaeology-design.md \
        plugins/mobile/skills/apk-archaeology/examples/newpipe-demo.md
git commit -m "docs: amend apk-archaeology demo AC to require handoff artifact (repoint move 3)"
```

---

## Self-Review (feito ao gerar este plano)

**Cobertura do design**: move #1a (Task 1) · move #1b (Task 2) · move #2 (Task 3) · move #3 (Task 4). Decisão §5 (2026-07-08): handoff na língua do time — US candidata + CA/Cenário Gherkin + esqueleto DTO (BDD subsumido no CA); campos exatos e arquivo-vs-seção ficam provisional, a confirmar no kickoff. Constraints de execução pós-migração no bloco Global Constraints + Preconditions. Deferidos (design §6): script de partição dedicado, app rico (F1), redesign amplo de saída (F2) — fora deste plano por design.

**Placeholders**: Task 1 carrega código real (test + impl). Tasks 2-4 são doc/curadoria — o "conteúdo" é o formato/estrutura, fornecido concretamente; a prosa-alvo em EN é adaptada à base migrada (declarado, não é placeholder).

**Consistência de tipo**: `node_files: dict[str, list[str]]` definido na Task 1 é consumido pela Task 2 (particionamento) e Task 3 (localizar arquivos da partição) com a mesma forma. Chave = nome simples de classe; casa com `nodes`.

**Dependências**: Task 1 → Task 2 (partição usa `node_files`); Task 3 depende de Task 2 (partição mecânica; fallback demo); Task 4 independente, por último.
