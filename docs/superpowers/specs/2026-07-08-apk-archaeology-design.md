# Design — apk-archaeology (skill provisional, plugin mobile)

**Data**: 2026-07-08 · **Status**: provisional/experimental — **NÃO wired**. Graduação condicionada a uso real no próximo cliente, não a este draft.
**Insumos**: precedente TF 2023 (achado em zip corporativo no OneDrive), 2 spikes reais ("Telecorp" — pseudônimo pra um app comercial real de telecom brasileira, ofuscado — e NewPipe, OSS, limpo), revisão crítica Fable, revisão crítica adversarial Opus, 7 rounds de decisão via AskUserQuestion.

## 1. Contexto e objetivo

O próximo projeto (cliente ainda não definido) começa com migração de app Android nativo → Flutter. O cliente vai entregar uma APK beta do app legado — segundo ele, sem ofuscação (informação recebida, ainda não verificada contra artefato real). Objetivo: ter pronta, antes do projeto começar, uma capacidade genérica de extrair valor de APK legado, seguindo a mesma lógica de "construir tooling portátil antes de precisar" que já rege o resto do agent-kit.

Precedente: em 2023, no engajamento TF, o time já fez esse tipo de esforço — engenharia reversa de 11 apps legado (Android+iOS), output em Markdown+HTML por pacote Java. Confirma que o padrão já é valioso nesse contexto de consultoria; não é ideia nova, é repetição de algo que já funcionou.

## 1.1 Prior art e posicionamento

Rodada de pesquisa aplicada (2026-07-08, verificada — não memória de modelo):

- **A metade dianteira do pipeline é commodity.** Decompilar (jadx) + agente LLM pra recuperação de identificador/string já é software pronto: [OpenAPK](https://openapk.ai/) (AGPL v3, jadx + agente), [JADX-AI](https://skywork.ai/skypage/en/jadx-ai-android-reverse-engineering/1981230616948953088), e papers de *agentic reverse engineering* de 2026 ([2604.14317](https://arxiv.org/pdf/2604.14317), [2606.06838](https://arxiv.org/pdf/2606.06838)). Todos com finalidade de **auditoria/segurança**, não migração.
- **A metade traseira é o espaço vazio.** Ninguém sintetiza fluxo/regra de negócio com bandas de confiança pra *reconstruir noutra stack*. Não há produto maduro de migração nativo→Flutter AI-driven (só marketing de consultoria sem case verificável). Isso sustenta a novidade do case: o par "extração-pra-migração cross-stack mobile" é genuinamente novo.
- **Reuso com caveat de governança**: se reaproveitar a camada determinística do OpenAPK, **só o código open-source, self-hosted** — nunca o workspace cloud deles com APK de cliente sob NDA (mesma classe de risco de §7/§8). AGPL é copyleft: ok pra tooling interno não-distribuído, registrado como restrição.
- **Não-dependência**: [LLM4Decompile](https://github.com/albertan017/LLM4Decompile) resolve binário→C (assembly stripado). Nosso caso é DEX→Java via jadx, que retém muito mais estrutura — problema mais fácil. **Não precisamos de decompilação por LLM**; jadx basta. Citado como contexto de fronteira, não como base técnica.

## 2. Vocabulário

| Conceito | Nesta skill |
|---|---|
| **Harness** | Runtime que transforma um LLM em worker de software — aqui, Claude Code (Bash/Read/Write + sandbox) executando jadx/apktool/scripts |
| **Orchestration** | Coordenação do fluxo entre componentes — aqui, o `SKILL.md` do apk-archaeology, a sequência fixa dos passos abaixo |
| **Agent** | O modelo executando trabalho dentro do harness — aqui, SÓ o passo de síntese da Dimensão A. Todo o resto é Harness+Orchestration determinístico, zero LLM |
| **Compound** | A arquitetura completa: scripts + SKILL.md + `known-libs.json` + modelo de confiança + regra de redação, empacotados como capacidade reutilizável. Uso mais amplo que a skill `core:compound` (que é especificamente o gate de write-back de fim de sessão) — dois sentidos do mesmo termo coexistindo. |

## 3. Status e critério de graduação

**Por que provisional, não wired**: o critério de graduação do próprio kit (recorrência ≥2×, estabilização em uso real, não-especificidade de projeto) não está satisfeito — há 1 precedente (TF 2023) e zero uso real (só um spike de viabilidade contra apps de teste). Graduar uma skill fim-a-fim agora, com template de consolidação e contrato de handoff travados, seria graduar com n=1.

- **Provisional, refinado após o primeiro uso real** (existe concreto o suficiente pra a demo rodar, mas não é contrato final): o template de consolidação e o contrato de handoff pra `tech-breakdown`/`spec-refine`. A demo do v0 usa uma versão de trabalho desses; o primeiro uso real no cliente é quem fixa o formato definitivo.
- **Corretude — fixo neste draft** (previnem falha concreta, não são preferência a validar depois): os 3 baldes de classificação (previnem vazamento de endpoint de SDK pro balde de negócio), as 3 bandas de confiança (previnem lavagem de inferência como fato), a redação de segredo (previne credencial em artefato persistido), a governança de publicação.
- **Arquitetura — decidido mas aberto a alternativa**: o fan-out de síntese (1 agente por unidade de trabalho). É a escolha atual de escala; alternativas (map-reduce, sumarização hierárquica) continuam na mesa se a implementação mostrar que não escala. Detalhes abaixo.

## 4. Dimensões-alvo

| Dimensão | O que extrai | Vira insumo de |
|---|---|---|
| **A — Fluxos e regras de negócio** | Telas, navegação, entidades, regras implícitas no código | Spec candidata / critério de aceite |
| **B — Contratos de API/rede** | Endpoints, payloads, headers de auth, SDKs de terceiro | Camada de repository/DTO do Flutter novo |
| **C — Módulos/grafo de dependência** | Grafo de referência entre pacotes/classes de negócio | Fronteiras de módulo + sequenciamento de épico na migração |

**Conscientemente fora do v1**: inventário de UI/telas, catálogo de SDK de terceiro como entregável próprio (emerge de graça como efeito colateral de B).

> As três dimensões **não têm o mesmo grau de confiança** — B é fato, C é reconstrução, A é inferência. A ambição de A ("regras → critério de aceite") só vale acompanhada dos limites de §10 e §11; não leia esta tabela isolada. O modelo de bandas está em §5 [6] e §10.

## 5. Arquitetura

```
apk-archaeology <caminho-do.apk>
        │
        ├─ [1] decompile.sh           jadx (source legível) + apktool (manifest/resources)
        │
        ├─ [2] classify_packages.py   3 BALDES, não binário:
        │                             · known-third-party   (casou known-libs.json)
        │                             · business-candidate  (pacote com nome real de app)
        │                             · unclassifiable      (pacote de 1-2 letras / ofuscado —
        │                                                     pode ser negócio OU lib renomeada)
        │
        ├─ [3] extract_endpoints.py   Dimensão B — FATO. Grep estrutural de URL/path em
        │                             (business-candidate ∪ unclassifiable), exclui só
        │                             known-third-party. Cada endpoint TAGUEADO por proveniência:
        │                             · [business]      atribuição confiável ao app
        │                             · [unclassifiable] pode ser SDK renomeado — humano decide
        │                             (sob ofuscação, o endpoint real cai em unclassifiable —
        │                              gatear só em business-candidate perderia o dado; medido
        │                              no spike: backend real aparece em 7 arquivos ofuscados
        │                              vs 6 nomeados). REDAÇÃO DE SEGREDO obrigatória em ambos
        │                             (alta entropia / formato de chave conhecido nunca
        │                             aparece literal no output).
        │
        ├─ [4] extract_graph.py       Dimensão C — RECONSTRUÇÃO, não fato. Grafo de referência
        │                             (extends/implements/tipo de campo) SÓ em business-candidate,
        │                             estilo Lakos. (Assimetria deliberada com [3]: endpoint é
        │                             fato que queremos de qualquer pacote; fronteira de módulo
        │                             só faz sentido sobre código nomeado — incluir a sopa
        │                             ofuscada só adiciona nós sem rótulo. Em app ofuscado o grafo
        │                             fica degenerado — esperado; Telecorp não grada C.)
        │                             Carrega caveat de artefato de decompilador
        │                             (generics apagados, classes sintéticas tipo
        │                             `$ExternalSyntheticLambda0`, inlining do R8).
        │
        ├─ [5] fan-out síntese A      Dimensão A — INFERÊNCIA tiered. 1 agente por unidade de
        │                             trabalho derivada do grafo de C (não um agente monolítico —
        │                             não escala: NewPipe=866 classes de negócio, Telecorp=7466,
        │                             cliente real pode ter 10-20k). Método de particionamento
        │                             (componente conexo / detecção de comunidade / prefixo de
        │                             pacote) a definir na implementação — é o que a demo calibra.
        │                             Cada agente recebe só sua partição + endpoints relacionados +
        │                             entry points nomeados + string resources (via apktool) como
        │                             âncora. NUNCA trata `unclassifiable` como lógica de negócio.
        │                             REGRA DE ÂNCORA (lição COBOL→Java, §11.1): regra sintetizada
        │                             que NÃO amarra numa evidência determinística (string /
        │                             endpoint / entry point) é marcada como `unanchored` e sai
        │                             como FLAG explícito — não como inferência de baixa confiança.
        │                             É exatamente onde o LLM alucina; não deixar passar disfarçado.
        │
        └─ [6] consolidar             Mapa único, mas as 3 BANDAS de confiança nunca são
                                      achatadas no mesmo nível:
                                      · B = fato
                                      · C = reconstrução (com ressalva de artefato)
                                      · A = inferência tiered (por cluster, citada arquivo:linha)
```

**Por que [2]-[4] vêm antes do agente**: são determinísticos — parsing, não julgamento. O agente só entra em [5], onde a tarefa é genuinamente síntese.

## 6. `known-libs.json` — fragilidade conhecida e documentada

Fingerprint por nome de pacote **é frágil por design sob ofuscação real**: o dado da Telecorp mostra 561/569 pacotes top-level virando 1-2 letras — se uma lib de terceiro for flatten junto, o casamento por nome não acha nada, e ela cai (por default) em `unclassifiable`, nunca incorretamente em `business-candidate`. É por isso que a classificação tem 3 baldes e não 2: um esquema binário (negócio vs. terceiro) forçaria essa lib não-reconhecida a virar "negócio" e vazaria os endpoints dela pra Dimensão B; o balde `unclassifiable` absorve exatamente esse caso duvidoso. A demo com a Telecorp vai medir empiricamente essa taxa de sobrevivência.

Prior art documentado como escape hatch, não implementado no v0: **LibScout**, **LibRadar** — fingerprint estrutural/hash que sobrevive à renomeação. Se `known-libs.json` por nome se provar insuficiente no uso real, esse é o caminho, não uma reinvenção.

**Achado empírico (verificação do plano, NewPipe real)**: a fragilidade por nome não é só falso-negativo em app ofuscado — também gera **falso-positivo em app limpo**. O pacote real `us/shandian/giga` (biblioteca de download legítima, embutida no NewPipe) colidiu com o regex de ofuscação (2 letras minúsculas) e foi classificado `unclassifiable`, mesmo o NewPipe não sendo ofuscado. Prefixos curtos estilo ccTLD (`us.`, `io.`, `me.`, `be.`) são o padrão de risco. Efeito assimétrico: inofensivo na Dimensão B (endpoint ainda é extraído, só com tag `unclassifiable` em vez de `business` — menos preciso, não perdido); perda real na Dimensão C (a classe fica fora do grafo, que só cobre `business-candidate`). Não bloqueia o v0 — é exatamente o tipo de imprecisão que o scorecard da demo (§10) existe pra reportar, não esconder.

## 7. Segurança — redação de segredo é requisito de design

APK decompilado rotineiramente expõe API keys/tokens hardcoded. A saída da Dimensão B é um artefato **persistido** (Markdown, pode ser commitado/anexado a card) — sem redação, isso é o modo de falha "credencial em README/commit/log". Requisito, não afterthought: todo match de alta entropia ou formato de chave conhecido no extrator de B é fingerprintado e reportado como *"N segredos potenciais encontrados — redigidos"*, nunca o valor literal.

## 8. Governança de publicação (separada da regra de redação)

Redação protege o *segredo*. Esta regra protege a *estrutura* — pra quem você mostra o quê. "Telecorp" é pseudônimo deste doc (e de qualquer exemplo derivado) pro app comercial real de telecom usado no spike — mas trocar o rótulo só resolve metade do problema:

| Artefato | Status |
|---|---|
| NewPipe (GPLv3, fonte pública) | Shareable — pode virar exemplo/demo/case, com o código-fonte real ao lado |
| Telecorp — **estatística agregada sobre o comportamento da ferramenta** (ex.: taxa de pacotes ofuscados, recall do fingerprint, contagem de segredos redigidos) | Shareable sob o pseudônimo — é dado sobre a ferramenta, não sobre o negócio da empresa real |
| Telecorp — **conteúdo extraído** (lista real de endpoint, mapa real de SDK, qualquer string literal única do app: domínio de backend, nome de pacote real, etc.) | **Interno.** Trocar o rótulo não anonimiza um domínio real ou um pacote real — eles entregam a empresa de novo independente do nome usado no texto. Árvore decompilada descartada após o uso na demo. |

A metodologia entregável ao cliente real assume **APK do próprio cliente, entregue por ele pra esse fim** (RE autorizada, ele é dono da IP) — nunca documenta "rode isso contra APK arbitrário de terceiro".

## 9. Demo v0 — plano e critério de aceite

**NewPipe = demo principal, pipeline completo (passos 1-6, incluindo o agente).** Único caso com *ground truth* (fonte pública no GitHub) — o único onde dá pra gradear fidelidade. Grading **não-circular**: o gabarito vem do repo-fonte real do NewPipe, nunca do nosso próprio output decompilado (senão o número de fidelidade se autoconfirma).

**Telecorp = apêndice, só passos [1]-[4] (B+C), sem agente.** Não dá pra gradear síntese sem fonte — rodar o agente ali queimaria token produzindo inferência não-verificável. Serve a dois propósitos específicos: (a) medir taxa de sobrevivência do fingerprint por nome sob ofuscação real; (b) prova positiva de que a redação de segredo dispara (app comercial tem chance real de ter chave embutida; o NewPipe limpo pode não ter nada pra redigir). As **estatísticas agregadas** desse apêndice (taxa de ofuscação, recall do fingerprint, contagem de segredos redigidos) podem aparecer no exemplo/case sob o pseudônimo Telecorp — o **conteúdo extraído** (endpoints reais, mapa de SDK real) não (§8).

**Critério de aceite da demo** (a demo é entregável do v0 — precisa de AC explícito, senão "demo" vira alvo móvel):
- Pipeline roda NewPipe fim-a-fim sem intervenção manual.
- Produz o mapa tiered (3 bandas visualmente distintas).
- Scorecard de fidelidade computado contra o repo-fonte real do NewPipe, com números reais (não estimados).
- Smoke da Telecorp confirma: redação disparando em pelo menos um host de backend real identificado no spike + zero segredo literal no output + taxa de classificação `unclassifiable` reportada.
- Produz ao menos um artefato de jusante no formato de handoff — ≥1 User Story candidata (Dimensão A) com Critério de Aceite como cenário Gherkin (`legacy-observed`) + esqueleto DTO de ≥3 endpoints da Dimensão B (`examples/wordpress-handoff.md`), consumível por `tech-breakdown`/`spec-refine`, demonstrando as etapas Spec/Implementação/Testes de §11. Sem esta linha o define-done aponta só pra confiança.

## 10. Formato de saída

- **Cabeçalho de proveniência**: input (app + versão + hash), versões de ferramenta (jadx/apktool), wall-clock, máquina. Reprodutibilidade = credibilidade.
- **Mapa tiered**: as 3 bandas (B fato / C reconstrução+ressalva / A inferência tiered) sempre visualmente separadas, nunca achatadas.
- **Scorecard de fidelidade** (só no caso NewPipe, é o único gradável):
  - B: X endpoints extraídos / Y na fonte real → recall + contagem de falso-positivo.
  - C: concordância de fronteira de módulo vs. estrutura real de pacote; nº de nós sintéticos/artefato filtrados.
  - A: N claims de alta confiança, M verificados verdadeiros contra a fonte, K falsos → **número de calibração**. Se high-confidence tiver algum falso, reporta — não esconde.
- **Caixa obrigatória "O que isto NÃO é"**: não mede produtividade (sem baseline, sem migração real); fidelidade medida em referência limpa (NewPipe), não em código ofuscado (Telecorp é apêndice à parte); comportamento legado recuperado ≠ comportamento desejado aprovado (gate do PO permanece); **a Dimensão A foi demonstrada primeiro em referência pobre em regra de negócio (NewPipe é player de mídia); o handoff F1 (`examples/wordpress-handoff.md`) já a exercita em regra de negócio real de self-service (busca/checkout de domínio no WordPress), mas continua não-medido e não-ofuscado — e expõe o LIMITE WEBVIEW: em app híbrido a lógica de negócio roda dentro do WebView (server-rendered JS), invisível à análise estática; a Dimensão A recupera o shell nativo + URL de carga + regras de navegação/allow-list, não a lógica no WebView**; inferência de A pode errar mesmo em tier alto — o tier é calibrado, não garantido; **regra de negócio de baixa frequência é esquecida por design** (lição COBOL→Java, §11.1) — a spec candidata é insumo pra reconciliação humana, não substituto dela.
- **Deliberadamente fora do v0**: tempo economizado, "% mais rápido", ROI, "N semanas comprimidas" — zero baseline, qualquer número desses agora seria fabricado.

## 11. Tese de aceleração — onde isso entra no ciclo Spec → Plano → Implementação → Testes → Validação

| Etapa | Ganho | Limite honesto |
|---|---|---|
| **Spec** | Substitui "spec por memória institucional falível" por "spec candidata com evidência citável" — o ganho mais forte e defensável | É hipótese sobre comportamento *legado*, não decisão sobre comportamento *desejado*. PO decide manter/mudar/descartar cada regra. Aceleração é em descoberta, não em decisão de produto |
| **Plano** | Dimensão C informa sequenciamento de épico — módulos acoplados migram juntos, módulos-folha migram isolados primeiro | — |
| **Implementação** | Dimensão B vira esqueleto de repository/DTO (padrão DTO+Entity+mapper); Dimensão A orienta estrutura de tela | Orienta, não gera código |
| **Testes** | Fluxos de A (tiered) podem virar esqueleto de cenário BDD antes da implementação existir — comportamento legado como oráculo inicial | **Risco real**: comportamento legado pode ser *bug* legado. Tag obrigatória `legacy-observed ≠ target-approved` — cenário nunca vira critério de aceite sem ratificação explícita do PO. Sem essa tag, a seção Testes fura o gate de decisão-de-produto que a seção Spec respeita |
| **Validação contra a Spec** | No v1 (estático), processo humano de sempre, só informado por spec com mais evidência | Validação real = **teste de equivalência comportamental** (legado vs. novo lado a lado) — a salvaguarda pra que o campo maduro de modernização (COBOL→Java) convergiu. É o v2 dinâmico (§12); no v1 não existe |

### 11.1 Lições da modernização de legado assistida por IA (COBOL→Java)

Campo maduro e documentado (IBM watsonx Code Assistant for Z, review independente CROZ). Convergência forte, aplicada aqui:

- **O valor está em ENTENDER/EXTRAIR, não em transpilar.** Transformação automática linha-a-linha produz "legado expresso na stack nova" — carrega a dívida e raramente é production-ready. O LLM é *motor de documentação*, e a stack nova se escreve do zero a partir da regra extraída. Valida a decisão de A orientar, não gerar código.
- **Regra sem âncora = alucinação** (encodada na regra de âncora do §5 [5]).
- **Regra de baixa frequência é esquecida por design.** Falha esperada, não acidente. Consequência de processo: entre "spec candidata" e "vira plano" existe um **passo de reconciliação humana** com especialista de domínio — a spec candidata é insumo pra essa conversa, não substituto dela. Conecta com o gate do PO (§11, linha Spec/Testes).
- **Salvaguarda que virou padrão**: guardrail determinístico em camadas + validação humana + teste de equivalência comportamental. Não confiar no output. Nossas 3 bandas de confiança são a materialização da primeira camada.

## 12. Deferido para v2 — documentado, não construído agora

- **Análise dinâmica** (driving real via `marionette` + captura de tráfego tipo `ga4-validate`/`export-logs`): fecha a "só metade da evidência" (o app roda, análise estática é só metade). Só faz sentido de escopo/esforço no v0 contra o APK real do cliente — em app de teste como NewPipe seria legalmente viável (GPL) mas não muda o veredito de escopo desta rodada.
- **Benchmark quantitativo com oráculo**: buildar um app OSS com `minifyEnabled true` guardando o `mapping.txt` como gabarito de-para — mede recall do fingerprint sob ofuscação *conhecida*. Ideia forte (sugerida pelo Fable), mas é harness de calibração separado, não bloqueia o v0.
- `known-libs.json` cresce organicamente com uso real; hoje é uma lista curada pequena (~20-30 libs comuns).

## 13. Gancho de medição para case futuro

O v0 sustenta um case de **capacidade com fidelidade medida** ("recuperamos estrutura verificável e spec-candidata citada em evidência, com taxa de erro medida e limitada"). Não sustenta um case de **resultado/ROI** ("economizou N semanas") — isso exige v2 dinâmico + uso real no cliente + baseline, que não existem ainda. Não fabricar esses números agora.

No primeiro uso real no cliente novo, capturar: tempo até a primeira spec-rascunho, número de ciclos de revisão com o PO, quantidade de comportamentos recuperados que ninguém do time lembrava. Isso vira o case depois, com dado real — mesma lógica de não graduar a skill com n=1 (§3).

## 14. Riscos / achados abertos dos spikes

- Retrofit vs. Ktor/OkHttp na Telecorp: achado 1 arquivo referenciando `retrofit2.`, mas zero anotação `@retrofit2.http.*` com retenção RUNTIME (que sobreviveria a R8 se fosse uso real de interface de API) — sinal de que não é o padrão principal, não conclusivo.
- Compose na Telecorp: sinal fraco (`.setContent(` 1 match; `androidx.compose.` 0 matches, possivelmente inlining do R8) — inferência, não fato confirmado.
- Fingerprint por nome de pacote pode falhar quase por completo sob ofuscação pesada — é exatamente o que a demo/apêndice da Telecorp vai medir, não uma suposição a esconder.

## 15. Local de trabalho (não versionado)

Ferramentas e amostras (jadx, APKs, árvores decompiladas) vivem em `~/dev/apk-archaeology-lab/`, fora de qualquer repo git — descartável e regenerável a partir de comandos documentados. A árvore decompilada da Telecorp é apagada após a demo (§8).
