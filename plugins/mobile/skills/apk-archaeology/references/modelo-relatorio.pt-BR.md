# Modelo de Relatório — Engenharia Reversa de APK → Backlog

**Projeto/Aplicativo:** [preencher] · **Pacote (`applicationId`):** [preencher] · **Versão do APK / build:** [preencher]
**Autor(a) / Equipe:** [preencher] · **Data:** [preencher] · **Versão do documento:** [preencher]

> **Status: modelo provisional.** Este modelo consolida um método validado, até o momento, em **um** aplicativo
> público não ofuscado, em profundidade de aproximadamente um épico. Não é um método geral nem comprovado em
> apps ofuscados (R8/ProGuard) ou com lógica *server-driven* — use cada seção como estrutura reutilizável, não
> como garantia de cobertura. Nenhuma seção deste modelo promete economia de tempo/esforço ("ROI"): sem medição
> real, esse número seria inventado.
>
> **Regra de ouro:** `legacy-observed ≠ target-approved` — tudo que este relatório descreve é **o que o
> aplicativo legado faz hoje**. É insumo para o Product Owner decidir **manter / mudar / tirar** cada
> comportamento antes de virar item de backlog — nunca um requisito aprovado por si só.
>
> **Legenda de origem** (aplique em cada campo/linha preenchida a partir deste modelo):
> 🟢 **recuperado do código** (âncora `arquivo:linha`) · 🟡 **observado/inferido** (o PO ratifica) ·
> ⬜ **fora do alcance da engenharia reversa** (design/PO/time preenche)

---

## Sumário

1. [Introdução e Objetivo](#1-introdução-e-objetivo)
2. [Escopo e Limitações](#2-escopo-e-limitações)
3. [Metodologia](#3-metodologia)
4. [Inventário de Componentes Técnicos (CT)](#4-inventário-de-componentes-técnicos-ct)
5. [Framework CT → RF → US](#5-framework-ct--rf--us)
6. [Épico e User Stories detalhadas](#6-épico-e-user-stories-detalhadas)
7. [Matriz de Rastreabilidade](#7-matriz-de-rastreabilidade)
8. [Escopo de Autorização e Uso Responsável](#8-escopo-de-autorização-e-uso-responsável)
9. [Anexos](#9-anexos)

---

## 1. Introdução e Objetivo

Este documento é um **modelo (template)** para estruturar relatórios de engenharia reversa de aplicativos
Android (APK) cujo objetivo é recuperar ou reconstruir documentação funcional em formato ágil — User Stories
(US), Regras de Negócio (RN) e Critérios de Aceite (CA) — a partir do comportamento observado no binário e no
código decompilado, cada afirmação ancorada em evidência (`arquivo:linha`) e classificada por origem.

**Quando usar:**
- **Migração/reescrita** de um aplicativo legado sem documentação atualizada (ex.: para outra stack/tecnologia).
- **Retomada de manutenção** por uma equipe diferente da que construiu o sistema original.
- **Auditoria de comportamento pré-integração** — entender o que um app (próprio ou concorrente autorizado) faz
  antes de decidir como integrá-lo ou substituí-lo.
- **Reconstrução de backlog** para um produto cuja documentação se perdeu ao longo do tempo.

**O que este relatório não é.** O relatório final é **insumo para o Product Owner**, não um substituto da
validação de negócio: o código mostra **como o sistema foi implementado**, não necessariamente como ele
**deveria** funcionar. Toda RN inferida é sinalizada como tal até confirmação — comportamento legado recuperado
pode ser um bug legado (a ratificação humana é a salvaguarda, não um carimbo).

---

## 2. Escopo e Limitações

**Identificação**
- Aplicativo / pacote (`applicationId`): [preencher]
- Versão / `versionCode` (build) analisado: [preencher]
- Plataforma e ambiente: [Android — versão mínima/alvo do SDK — preencher]
- Licença / autorização de análise: [preencher — ver §8]

**Módulos/fluxos incluídos no escopo:** [preencher — ex.: login, carrinho, checkout]
**Módulos/fluxos explicitamente fora do escopo:** [preencher]

**Limitações conhecidas** (aplicam-se ao relatório inteiro, não só às linhas marcadas ⬜):
- **Ofuscação de código** (R8/ProGuard) — nomes tornam-se ilegíveis (ex.: âncora vira `c/a.java:17` em vez de
  `LoginActivity.java:178`).
- **Certificate pinning** — pode bloquear captura de tráfego quando a camada de análise dinâmica (§3.2) rodar.
- **Código nativo (`.so`) não decompilado** — lógica invisível à leitura estática.
- **Lógica dependente de backend / WebView / remote-config** — roda fora do binário, fora do alcance desta
  análise; vira **ponto cego delimitado** (🟢 aponta o limite; a decisão de manter ou nativizar é ⬜).

> **Aviso de degradação (conhecido, ainda não sistematizado).** Dois vetores corroem a confiabilidade deste
> método e nenhum dos dois tem, hoje, um mapa campo-a-campo de degradação: **ofuscação mata a legibilidade**
> das âncoras; **comportamento dinâmico** (remote-config, testes A/B, conteúdo montado em WebView, reflection)
> **mata a observabilidade** da análise estática. Trate qualquer seção deste relatório proveniente de um app
> ofuscado ou fortemente *server-driven* com cautela redobrada — ver `method.md`.

---

## 3. Metodologia

### 3.1 Análise Estática

Consiste em decompilar o pacote sem executá-lo — manifesto, DEX→Java/Smali, layouts XML, strings e endpoints
literais. **O pipeline que roda hoje** (decompilação → classificação de pacotes → extração de endpoints →
extração do grafo de módulos → síntese da camada de regras/fluxos → consolidação) está descrito em
`../SKILL.md` (seção *Steps*, passos 1–6) — **fonte única**; não é reproduzido aqui para evitar que este modelo
e o pipeline real divirjam com o tempo (já aconteceu uma vez com um diagrama desatualizado). Este relatório
consome a saída consolidada desse pipeline e a traduz na cadeia CT → RF → US → RN → CA (§4 a §7).

### 3.2 Análise Dinâmica (v2 log-based — opcional nesta rodada)

A análise dinâmica **log-based** (rodar o app, dirigir os fluxos por `adb`/`uiautomator`, ler `adb logcat` e
cruzar com o extrato estático — **comportamento, não tráfego**) pode ou não ter sido executada. Marque:

- **[ ] Não executada** — qualquer alegação que dependeria dela (comportamento em runtime, config remota,
  classificação nativo/WebView/Custom-Tab por tela) permanece **⬜ fora do alcance** deste relatório.
- **[ ] Passagem fina executada** — resuma os datums observados (sequência real de navegação;
  nativo/WebView/Custom-Tab por tela reachable; fetch de remote-config/feature-flags no boot) como
  **validação do instrumento**, não análise completa.

Spec e **cláusula anti-laundering** em `references/method.md` ("Dynamic analysis (v2)"). Mira os dois vetores
de degradação do §2 (interior de WebView, remote-config/A-B que a estática não vê) e serve de **2ª fonte**
para triangular a análise estática antes da ratificação. `marionette` **não** dirige APK nativo (é Flutter).

---

## 4. Inventário de Componentes Técnicos (CT)

Lista bruta dos componentes identificados na engenharia reversa, **antes de qualquer interpretação de
negócio**. É a base rastreável para as seções seguintes (§5 em diante).

| ID | Componente | Tipo | Descrição técnica | Evidência (`arquivo:linha`) | Origem |
|---|---|---|---|---|---|
| CT-01 *(exemplo — substituir)* | `LoginActivity` | Tela | Autenticação por e-mail/senha; obtém e persiste token de sessão | `LoginActivity.java:[preencher]` | 🟢 |
| CT-02 *(exemplo — substituir)* | `CartFragment` | Tela | Exibição dos itens do carrinho e cálculo do subtotal | `cart/CartFragment.java:[preencher]` | 🟢 |
| CT-03 *(exemplo — substituir)* | `DiscountCalculator` | Classe de regra | Cálculo de desconto a partir de um cupom informado | `checkout/DiscountCalculator.java:[preencher]` | 🟢 |
| CT-04 | [preencher] | [Tela/Fragment/ViewModel/Worker/Classe de regra/API] | [preencher] | `[arquivo:linha]` | 🟢/🟡 |
| … | | | | | |

Tipos sugeridos: **Tela**, **Fragment**, **ViewModel**, **Worker/Service**, **Classe de regra**, **API/endpoint**.
Uma linha por componente relevante do escopo (§2) — não é preciso listar todo o app, só o que alimenta as US do
épico em análise.

---

## 5. Framework CT → RF → US

### 5.1 Estrutura da User Story

Toda US derivada de engenharia reversa segue: **"Como [persona], quero [ação/capability], para [benefício]"** —
mas as três partes **não têm a mesma origem**:

- **[ação/capability]** 🟢 é a parte ancorável — recuperada diretamente do fluxo/CT observado.
- **[persona]** e **[benefício]** 🟡 são inferidos a partir do fluxo de tela (ex.: "usuário final", "operador de
  retaguarda") — **o PO confirma** antes de tratar como fato de produto.

Entre o CT (componente técnico) e a US (história) existe um passo explícito, o **RF — Requisito Funcional
observado**: a frase factual "o app permite X hoje", que ainda não é uma US (sem persona/benefício) mas já não
é mais um componente bruto. Ver glossário (§9.1).

### 5.2 Tabela de Mapeamento

| ID US | RF observado | User Story | CTs | RN | Confiança |
|---|---|---|---|---|---|
| US-CART-01 *(exemplo — substituir)* | RF-01: o app permite aplicar um cupom de desconto no carrinho | Como cliente, quero aplicar um cupom de desconto no carrinho, para pagar um valor menor pelo pedido | CT-02, CT-03 | RN-01, RN-02 *(ver §6, nested)* | Alta |
| US-[EPIC]-02 | RF-[preencher] | [preencher] | [preencher] | [preencher] | [preencher] |
| … | | | | | |

> As RN listadas aqui são **referência**, não catálogo — o conteúdo de cada RN vive dentro da US correspondente
> em §6 (regra do documento: nada de catálogo global de RN/CA separado da US).

---

## 6. Épico e User Stories detalhadas

Formato validado na sessão de referência: cada US do épico é desenvolvida por completo — história, contexto,
regras, critérios de aceite e cobertura — **dentro da própria US**. Não existe catálogo global de RN nem de CA:
a Matriz de Rastreabilidade (§7) é a única vista consolidada/flat, e é gerada a partir do que está aqui, não o
contrário.

### Épico — [nome do épico, preencher] *(exemplo abaixo: "Carrinho e Checkout")*

**Mapa do épico** *(visão geral — uma linha por US; preencher conforme o épico crescer)*

| ID | Capability | Evidência-chave | Confiança |
|---|---|---|---|
| US-CART-01 *(exemplo)* | Aplicar cupom de desconto no carrinho | `DiscountCalculator.java:[preencher]` | Alta |
| US-CART-02 | [preencher] | `[arquivo:linha]` | [preencher] |

---

#### US-CART-01 — Aplicar cupom de desconto no carrinho *(exemplo — substituir por US real)*

**História**
Como cliente que já tem itens no carrinho, 🟡
quero aplicar um cupom de desconto, 🟢
para pagar um valor menor pelo pedido. 🟡
<sub>🟢 capability ancorada em `DiscountCalculator` · 🟡 persona e benefício são inferência — PO confirma</sub>

**Contexto** *(invertido: a RE dá o "hoje"; o PO dá o "porquê")*
- 🟢 **Observado no legado:** o app aplica desconto ao subtotal quando um código de cupom válido é informado e
  o subtotal atinge um valor mínimo. `DiscountCalculator.java:[preencher]`
- 🟡 **Escopo candidato:** replicar esse comportamento no aplicativo/stack de destino — PO decide manter/mudar/tirar.
- ⬜ **A preencher pelo PO/negócio:** motivação do cupom no produto novo · meta (ex.: ticket médio, conversão) ·
  muda algo do legado (regras de acumulação, teto de desconto)? · prioridade. `legacy-observed ≠ target-approved`

**Regras de negócio observadas (RN — numeradas dentro desta US)** 🟢
| RN | Regra | Evidência | Origem |
|---|---|---|---|
| RN-01 | Desconto de cupom só é aplicado se o subtotal atingir o **valor mínimo exigido** | `DiscountCalculator.java:[preencher]` | 🟢 |
| RN-02 | Apenas **um cupom** pode estar ativo por pedido | `DiscountCalculator.java:[preencher]` | 🟡 *(comportamento ao inserir 2º cupom não confirmado em tela — a validar)* |
| RN-03 | [preencher] | `[arquivo:linha]` | 🟢/🟡 |

**Critérios de Aceite (BDD, `@legacy-observed`)** 🟢 *(o PO ratifica antes de virar critério aprovado)*
```gherkin
@legacy-observed @tier-alta
Cenário 1 — Cupom válido com subtotal suficiente
  Dado que o subtotal do carrinho é igual ou superior ao valor mínimo exigido
  Quando o cliente insere um cupom válido
  Então o desconto é aplicado e o novo total é exibido        # DiscountCalculator.java:[preencher] — PO ratifica

Cenário 2 — Subtotal insuficiente
  Dado que o subtotal do carrinho é inferior ao valor mínimo exigido
  Quando o cliente insere um cupom válido
  Então o sistema informa que o valor mínimo não foi atingido
  E o cupom não é aplicado                                    # DiscountCalculator.java:[preencher]

Cenário 3 — Segundo cupom (comportamento a confirmar)
  Dado que já existe um cupom aplicado ao pedido
  Quando o cliente insere um segundo cupom
  Então [comportamento observado — preencher]                 # RN-02 — 🟡 requer validação com negócio
```

**Cobertura de cenários** *(honestidade no nível do cenário — não achatar)*
| Cenário esperado num ticket | Status | Nota |
|---|---|---|
| Caminho feliz (cupom válido + subtotal suficiente) | 🟢 preenchido | Cenário 1 |
| Subtotal insuficiente | 🟢 preenchido | Cenário 2 |
| Segundo cupom / acumulação | 🟡 análogo/inferido | Cenário 3 — comportamento não confirmado em tela, só no código |
| Cupom expirado / inválido | ⬜ não observado | não recuperável nesta leitura → decisão do time |
| Erro de rede ao validar cupom | ⬜ não observado | idem — a definir com PO/UX |

**Contrato recuperado (ponto de partida da integração)** 🟢
- `DiscountCalculator.applyCoupon(cartSubtotal, couponCode)` → `{ discountedTotal, discountAmount }`
  *(assinatura ilustrativa — substituir pela assinatura real, com `arquivo:linha`)*
- ⬜ *Arquitetura-alvo* (mesmo backend de cupons? validação client-side ou server-side no app novo?) = decisão do time.

**Dependências & sequência de migração** 🟢 *(direcional, do grafo — não é a planta final)*
- Este fluxo (`checkout/carrinho`) depende de: [preencher — ex.: catálogo de produtos, autenticação].
- [preencher: é fundação de quantas áreas? é folha (baixo acoplamento)?] → ordem sugerida de migração.
- ⬜ Sequência final confirmada pelo time.

**Notas / perguntas abertas**
- 🟡 Validar com o negócio se cupons são cumulativos ou se o 2º substitui o 1º (RN-02).
- ⬜ [preencher outras perguntas específicas do épico real]

**Figma / layout-alvo** ⬜ — não existe no APK legado; design do app novo é do time de UX. *(slot: [link do Figma])*

**Definition of Ready (DoR)** ⬜ *(processo do time — a RE não preenche)*
- [ ] Contexto de negócio preenchido pelo PO
- [ ] Figma do fluxo-alvo aprovado
- [ ] Critérios `@legacy-observed` **ratificados** (manter/mudar/tirar) pelo PO
- [ ] Contrato-alvo definido (reusar backend legado ou novo?)
- [ ] Cenários de erro/edge (⬜ acima) decididos
- [ ] Estimativa realizada

**Definition of Done (DoD)** ⬜ *(processo do time)*
- [ ] Implementado conforme Figma-alvo
- [ ] Cenários ratificados cobertos por teste
- [ ] Integração com o backend-alvo
- [ ] Code review aprovado · [ ] PO validou comportamento

---

## 7. Matriz de Rastreabilidade

Consolida a cadeia completa — **CT ↔ RF ↔ US ↔ RN ↔ CA** — numa única vista flat, com o nível de
confiança de cada achado. É gerada a partir do conteúdo nested de §6, nunca o inverso.

| CT | RF | US | RN | CA (cenário) | Status/Confiança |
|---|---|---|---|---|---|
| CT-02, CT-03 *(exemplo)* | RF-01 | US-CART-01 | RN-01 | Cenário 1, 2 | Confirmado em código e em tela |
| CT-03 *(exemplo)* | RF-01 | US-CART-01 | RN-02 | Cenário 3 | Inferido — requer validação com negócio |
| [preencher] | [preencher] | [preencher] | [preencher] | [preencher] | [preencher] |

**Escala de Status/Confiança** (use consistentemente em todo o relatório):
- **Confirmado em código e em tela** — comportamento visível tanto no código quanto na UI observável.
- **Confirmado em código, sem evidência em tela** — âncora sólida, mas não visto rodando.
- **Inferido** — reconstruído a partir de comportamento indireto ou de um fluxo análogo/irmão.
- **Requer validação com o negócio** — hipótese explícita, sem âncora suficiente para tier mais alto.

---

## 8. Escopo de Autorização e Uso Responsável

- Realizar a engenharia reversa **apenas** sobre aplicativos próprios ou com **autorização contratual/documental
  explícita** do detentor dos direitos.
- Respeitar os **termos de uso da loja de distribuição**, as **licenças de bibliotecas de terceiros** embutidas
  no APK e a legislação de **propriedade intelectual** aplicável.
- Tratar dados pessoais eventualmente expostos durante a análise (ex.: em tráfego de rede, quando a análise
  dinâmica do §3.2 estiver em uso) conforme a legislação de proteção de dados vigente (ex.: **LGPD**), evitando
  exposição desnecessária no relatório final.
- **Toda RN reconstruída neste relatório é uma hipótese até validação formal** com a equipe de negócio ou
  Product Owner — inclusive as marcadas 🟢, que são fiéis ao código, não necessariamente ao comportamento
  correto ou desejado.

---

## 9. Anexos

### 9.1 Glossário

| Termo | Definição |
|---|---|
| **CT** | Componente Técnico — item bruto do inventário (tela, fragment, viewmodel, worker, classe de regra, endpoint), antes de qualquer interpretação de negócio. |
| **RF** | Requisito Funcional observado — a frase factual "o app permite X hoje", ponte entre o CT e a US; ainda sem persona/benefício. |
| **US** | User Story — "Como/quero/para" derivada do RF; capability 🟢 ancorada, persona/benefício 🟡 inferidos. |
| **RN** | Regra de Negócio — condição, gatilho, cálculo ou validação observada no código; numerada **dentro de cada US**, não em catálogo global. |
| **CA** | Critério de Aceite — cenário testável em Gherkin (`@legacy-observed`), **aninhado** na US que descreve; referenciado na Matriz (§7) por número de cenário. |
| **legacy-observed** | Tag que marca todo comportamento como "o que o app legado faz hoje" — nunca um requisito aprovado; ver banner do documento. |
| **Tier** (`@tier-alta` etc.) | Banda de confiança de um critério de aceite/regra — não deve ser achatada; convive lado a lado com o que é fato (endpoint), reconstrução (grafo) ou inferência (regra de negócio). |
| **Unanchored** (não ancorado) | Regra ou afirmação que não pôde ser amarrada a uma string, endpoint ou ponto de entrada concreto — marcada como tal, nunca disfarçada de inferência de baixa confiança comum. |
| **Ponte cega** (blind spot) | Trecho de comportamento que roda fora do alcance da análise (ex.: dentro de WebView, em backend, em remote-config) — delimitado (🟢 "aqui para de ser recuperável"), nunca preenchido por suposição. |

### 9.2 Como usar este modelo — ordem de preenchimento

1. Preencha o cabeçalho de identificação e o **§2 Escopo e Limitações** primeiro — sem isso, o resto do
   relatório não tem moldura.
2. Rode ou consulte o pipeline de análise estática (§3.1, fonte única em `SKILL.md`) e preencha o
   **§4 Inventário de CT** a partir da saída consolidada.
3. Agrupe CTs relacionados em RFs e depois em US no **§5.2**, referenciando os CTs e apontando as RN que vêm em
   seguida.
4. Para cada US, desenvolva a seção completa em **§6**: história, contexto invertido, RN nested, CA em Gherkin,
   cobertura de cenários, contrato, dependências, notas abertas, Figma/DoR/DoD (estes últimos deliberadamente
   vazios — não é papel da RE preenchê-los).
5. Consolide tudo na **Matriz de Rastreabilidade (§7)** — ela nasce do conteúdo de §6, não é preenchida
   independentemente.
6. Antes de publicar a versão final, **valide com o PO/negócio** cada item marcado 🟡, e leve os itens ⬜ para o
   time decidir. Nenhuma US deste relatório é um requisito aprovado até essa etapa acontecer.
