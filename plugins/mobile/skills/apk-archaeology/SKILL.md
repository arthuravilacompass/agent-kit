---
name: apk-archaeology
description: "STATUS: provisional — invoque para extrair valor de um APK Android legado (descompilado) rumo a uma migração pra Flutter: fluxos/regras de negócio, contratos de API, grafo de módulo, com bandas de confiança explícitas. Não wired — refinar após primeiro uso real."
disable-model-invocation: true
---

# apk-archaeology — Extração de valor de APK legado (provisional)

> **STATUS: provisional/experimental.** Template de consolidação e contrato de handoff
> são refinados após o primeiro uso real num cliente — ver design doc:
> `docs/superpowers/specs/2026-07-08-apk-archaeology-design.md`.

Extrai 3 dimensões de um APK Android legado — fluxos/regras de negócio (A), contratos
de API (B), grafo de módulo (C) — como insumo pra migração nativo→Flutter. Adapta o
padrão do `core:archaeology` (dispatch paralelo por dimensão → consolidação estruturada)
pra uma fonte compilada/possivelmente ofuscada em vez de código-fonte vivo.

## Quando Usar

Você tem um `.apk` de um app legado que vai (ou pode vir a) ser migrado pra Flutter, e
quer uma spec candidata + contratos de API + fronteiras de módulo antes de planejar a
migração. Não é análise de segurança/malware — é preparação de migração.

## Input

Caminho pra um arquivo `.apk`.

## Steps

### 1. Decompilar

```
scripts/decompile.sh <caminho.apk> <dir_trabalho>
```

Produz `<dir_trabalho>/jadx/sources/` (Java legível) e `<dir_trabalho>/apktool/`
(manifest/resources).

### 2. Classificar pacotes

```
python3 scripts/classify_packages.py <dir_trabalho>/jadx/sources scripts/known-libs.json --out <dir_trabalho>/classify.json
```

3 baldes: `known-third-party` / `business-candidate` / `unclassifiable`. Ver design
doc §6 pra por que `unclassifiable` existe e não é opcional.

### 3. Extrair endpoints (Dimensão B — fato)

```
python3 scripts/extract_endpoints.py <dir_trabalho>/jadx/sources <dir_trabalho>/classify.json --out <dir_trabalho>/endpoints.json
```

Roda sobre `business-candidate ∪ unclassifiable`. Redação de segredo é automática —
confira `secrets_redacted` no output; se > 0, **não** exponha o `endpoints.json` bruto
fora do ambiente local antes de confirmar que nenhum literal vazou (grep manual como
segunda checagem é aceitável nesta fase provisional).

### 4. Extrair grafo de módulo (Dimensão C — reconstrução)

```
python3 scripts/extract_graph.py <dir_trabalho>/jadx/sources <dir_trabalho>/classify.json --out <dir_trabalho>/graph.json
```

Só sobre `business-candidate`. Note `artifact_warnings` no output — classes sintéticas
filtradas são esperadas, não bug.

### 5. Síntese da Dimensão A (agente — fan-out)

Particione `graph.json` em unidades de trabalho (componente conexo do grafo é o método
mais simples pra v0 — duas classes ligadas por edge caem na mesma partição; classes
sem edge formam partições de 1). Para CADA partição, dispare um agente com este
contexto:

- As classes da partição (código-fonte de `jadx/sources/<pacote>/`).
- Endpoints de `endpoints.json` que citam arquivos dessa partição.
- Entry points nomeados (Activities/Fragments/ViewModels do manifest ou reconhecíveis
  por convenção de nome) e string resources de `apktool/res/values/strings.xml`, como
  âncora.

Instrua o agente: sintetize fluxos/regras de negócio observáveis nesta partição. Toda
regra citada em `arquivo:linha`. **Regra de âncora**: se não conseguir amarrar uma
regra numa string, endpoint ou entry point concreto, marque como `unanchored` — não
maquie como inferência de baixa confiança normal. Nunca trate classes de pacote
`unclassifiable` como lógica de negócio.

### 6. Consolidar

Uma síntese, 3 bandas SEMPRE separadas visualmente, nunca achatadas:

```markdown
## Proveniência
- Input: <nome do apk> · <hash sha256> · versões jadx/apktool · wall-clock · máquina

## B — Contratos de API (fato)
[lista de endpoints com tag business/unclassifiable, arquivo:linha]

## C — Grafo de módulo (reconstrução — ver artifact_warnings)
[resumo do grafo: clusters, acoplamento, nós sintéticos filtrados]

## A — Fluxos e regras de negócio (inferência tiered)
[por partição: regras com tier de confiança + arquivo:linha; unanchored destacado à parte]

## O que isto NÃO é
[ver design doc §10 — não mede produtividade, comportamento legado ≠ aprovado,
 regra de baixa frequência pode ter sido esquecida, etc.]
```

## Regras invioláveis

- `unclassifiable` nunca é tratado como lógica de negócio pelo agente (passo 5).
- Toda string de alta entropia/formato de chave conhecido é redigida antes de qualquer
  output persistido (passo 3) — nunca o valor literal.
- As 3 bandas de confiança nunca são achatadas no mesmo nível na consolidação (passo 6).
- Regra sem âncora concreta sai como `unanchored`, não como inferência normal.
- Conteúdo extraído de APK de terceiro sem autorização (não o cliente atual) nunca sai
  do ambiente local — ver design doc §8 (governança de publicação).
