# apk-archaeology — Demo v0 (NewPipe)

> Skill provisional. Ver `docs/superpowers/specs/2026-07-08-apk-archaeology-design.md`
> pra decisões de design e limites. Este documento é o exemplo público (spec §8) —
> app OSS, GPLv3, fonte real ao lado do output.

## Proveniência

- **Input**: NewPipe v0.28.8 (`org.schabi.newpipe`) — APK público, [github.com/TeamNewPipe/NewPipe](https://github.com/TeamNewPipe/NewPipe)
  `sha256: d9fb2540b3a2a0b059c73a296f0cda1c06738426d013c626dbf088aea66629b3`
- **Ferramentas**: jadx 1.5.5 · apktool 3.0.2
- **Fonte de comparação (não-circular, spec §9)**: dois clones reais, não o output do próprio pipeline —
  `TeamNewPipe/NewPipe` @ v0.28.8 (app) + `TeamNewPipe/NewPipeExtractor` @ v0.26.3 (a lógica de negócio de
  fato vive num repositório separado, referenciado via dependência Gradle — achado do próprio processo de
  grading, ver §Lições abaixo)
- **Data**: 2026-07-08 · macOS (arm64)

## B — Contratos de API (fato)

- **213 endpoints extraídos** (business-candidate ∪ unclassifiable, known-third-party excluído) ·
  **324 literais de alta entropia redigidos** (nenhum aparece no output; a grande maioria são hashes/IDs
  isolados fora de contexto de URL, não segredo embutido em endpoint — só 2 dos 213 endpoints têm
  `[REDACTED]` embutido)

### Scorecard de fidelidade (grading não-circular, spec §9)

| Passo de correção | real_count | true_positive | false_positive | false_negative | recall |
|---|---|---|---|---|---|
| Ingênuo (app-only, com `test/`) | 96 | 30 | 95 | 66 | 0.31 |
| + só `app/src/main` (exclui teste) | 51 | 29 | 96 | 22 | 0.57 |
| + inclui `NewPipeExtractor` (versão correta, só produção) | 138 | 82 | 43 | 56 | 0.59 |
| + exclui comentário Javadoc do gabarito (contaminação do PRÓPRIO grader) | **99** | **82** | 43 | **17** | **0.83** |

**Recall final: 0.83** (82/99) — reportado com o percurso completo, não só o número final; cada
correção acima é rastreável e foi genuinamente descoberta rodando o pipeline, não estimada.

**43 falsos-positivos, categorizados** (nenhum verificado como alucinação pura):
- ~6 são de `org.jsoup` (lib de terceiro real, não cadastrada em `known-libs.json` → cai em
  `business-candidate` por não ser reconhecida — fragilidade já documentada na spec §6, agora com
  instância concreta e nome de lib real).
- Boa parte do restante (SoundCloud/Bandcamp/YouTube "API paths") são endpoints **reais**, construídos
  em código-fonte por concatenação de string (`BASE_URL + path + "?param="`), que o compilador/R8
  funde em uma constante única no bytecode — jadx decompila de volta como 1 literal, mas o gabarito
  (que lê o `.java` fonte, onde ainda são fragmentos separados) nunca vê essa forma fundida como
  string única. Não verificado exaustivamente item a item; padrão consistente com os casos checados.

## C — Grafo de módulo (reconstrução)

- **2067 nodes, 1450 edges, 232 classes sintéticas filtradas** (`artifact_warnings`) — volume de
  filtragem alto, esperado num app real com Compose/lambdas geradas pelo R8.
- Cluster usado como unidade de trabalho pra Dimensão A: componente conexo (922 componentes totais,
  maior com 678 nodes — dominado por classes de biblioteca cruzando os poucos `business-candidate` que
  fazem ponte; os 2 clusters usados na síntese abaixo foram escolhidos por serem pequenos e nomeados).

## A — Fluxos e regras de negócio (inferência tiered)

Duas partições sintetizadas — "Streaming Services" (4 classes: `StreamingService`, `YoutubeService`,
`BandcampService`, `PeertubeService`) e "Settings Fragments" (14 classes `*SettingsFragment`).
43 claims totais, a maioria `alta`, 3 corretamente marcadas `unanchored` (regra de âncora, spec §5[5]
— nenhuma decorada como inferência normal).

### Calibração (verificado contra a fonte real, amostra de 4 claims `alta`)

| Claim | Veredito | Evidência |
|---|---|---|
| YouTube declara 1 só idioma de UI ativo (`en-GB`), 109 países hardcoded | ✅ **verdadeiro, exato** | Os outros ~74 idiomas estão **comentados no source** (`/* ... */`) — nunca compilados. Contagem de país bate 109/109. O agente inferiu isso corretamente só a partir do bytecode, sem ver o comentário. |
| SoundCloud limita a 9 países (`AU,CA,DE,FR,GB,IE,NL,NZ,US`) | ✅ **verdadeiro, exato** | Lista bate caractere a caractere com `SoundcloudService.java`. |
| Playlist YouTube com id `RD*` roteia pro extractor de Mix | ✅ **verdadeiro, citação imprecisa** | Comportamento confirmado (`playlistId.startsWith("RD")`), mas no source vive em `YoutubeParsingHelper.java`, não `YoutubeService.java` como o agente citou — decompilado funde/organiza diferente do source (achado, não conclusão especulativa). |
| Import de inscrições do YouTube só aceita `INPUT_STREAM` | ✅ **verdadeiro** | Conceito confirmado em `SubscriptionExtractor.java`/`YoutubeSubscriptionExtractor.java`. |

**4/4 verificadas amostradas, 4 verdadeiras** (2 exatas, 1 com imprecisão de citação de arquivo, 1
confirmada sem checar linha exata) — amostra pequena, não é uma auditoria exaustiva dos 43 claims.
Reportado como está: nenhuma falsa encontrada na amostra, mas a amostra é pequena e não prova taxa de
erro zero pro conjunto inteiro.

## O que isto NÃO é

- Não mede produtividade — sem baseline, sem migração real feita.
- Fidelidade medida em referência limpa (NewPipe, sem ofuscação) — não em código ofuscado
  (ver apêndice Telecorp abaixo, só estatística agregada).
- Dimensão A demonstrada em referência pobre em regra de **negócio** (NewPipe é player de mídia —
  as regras encontradas são de roteamento/localização/UI, não pricing/entitlement/checkout/antifraude).
  Recuperação de regra de negócio real permanece projetada, não medida.
- Inferência de A pode errar mesmo em tier alto — o tier é calibrado (amostra de 4/4 aqui), não
  garantido pra todo o conjunto.
- Regra de negócio de baixa frequência pode ter sido esquecida — spec candidata é insumo pra
  reconciliação humana, não substituto dela.
- **O scorecard de B, no valor final (0.83), já é uma correção sobre 3 erros metodológicos do
  próprio processo de grading** (escopo de repo incompleto, versão errada da dependência, gabarito
  contaminado por comentário) — ver Lições abaixo. Isso não é "a ferramenta errou 3 vezes", é o
  processo de avaliação que precisou de 3 correções antes do número ser honesto.

## Apêndice — smoke Telecorp (app comercial real, pseudônimo — spec §8)

- **96,9% dos pacotes top-level caíram em `unclassifiable`** (558 de 576) — ofuscação real e pesada,
  confirmando empiricamente a fragilidade de fingerprint por nome documentada na spec §6.
- **847 segredos potenciais redigidos** — nenhum valor literal neste documento nem em qualquer lugar
  fora de `~/dev/apk-archaeology-lab/` (spec §8). Verificação técnica pós-hoc não achou nenhum literal
  residual dentro do campo `url` do output persistido (checagem restrita ao campo sensível, não ao
  JSON inteiro — um primeiro grep mais largo bateu em falso-positivo no campo `file`, que é caminho de
  classe, não segredo).
- 15 endpoints tagueados `business`, 38 `unclassifiable` — a maioria do conteúdo de negócio real cai
  fora do balde "confiável", como esperado sob ofuscação pesada (spec §6).
- **Conteúdo extraído** (endpoints reais, domínios reais) — NÃO incluído. Interno, spec §8.

## Lições do processo de grading em si (achado desta demo, não do design)

O maior aprendizado desta rodada não foi sobre o pipeline — foi sobre como gradear fidelidade
corretamente:

1. **Repo errado inicialmente.** A lógica de negócio do NewPipe vive num repositório SEPARADO
   (`NewPipeExtractor`), referenciado via `implementation(libs.newpipe.extractor)` no Gradle — não
   está no clone do app. 19 dos 21 claims da Partição "Streaming Services" citam arquivos que só
   existem nesse segundo repo.
2. **Versão errada do segundo repo.** Cloná-lo sem fixar tag pega a branch padrão atual, não a versão
   realmente empacotada no APK testado (`v0.26.3`, achado em `libs.versions.toml`) — o pipeline errado
   deu 656 URLs de gabarito; o correto, 138 (produção) / 656 com testes inclusos.
3. **Gabarito contaminado por comentário.** A regex do `grade_fidelity.py` (`"(https?://...)"`) não
   distingue string literal de comentário Javadoc (`<a href="https://...">`) — ambos têm aspas. 39 dos
   56 falsos-negativos "reais" eram, na verdade, links de documentação nunca compilados. Isso é uma
   limitação do MÉTODO de grading (comparação textual ingênua), simétrica à contaminação por `test/`
   já descrita acima — registrada aqui, não corrigida no `grade_fidelity.py` nesta rodada (correção
   ad-hoc no escopo do clone foi suficiente pra esta demo; corrigir a regex do grader é candidato a
   v2 se o padrão se repetir em uso real).
