# Guia de preenchimento — modelo de relatório apk-archaeology

> **Companheiro do template** `modelo-relatorio.pt-BR.md`. Para **quem preenche** o relatório (e quem mantém o template) — **não** vai para o cliente. O *método* de análise (pipeline, reach map, spec da dinâmica) vive em `method.md`/`SKILL.md` — fonte única, não reescrito aqui.

## Ordem de preenchimento

1. Cabeçalho de identificação + **§2 Escopo e Limitações** — a moldura primeiro (inclua o status de alcance do run, se aplicável).
2. Rode/consulte a **Fundação** do pipeline (`SKILL.md`, *Steps* — decompila/classifica + veredito de alcance/grafo/persistência/colheita, roda 1× por APK) e preencha o **§4 Inventário de CT** a partir da saída consolidada; o **loop por-feature** sintetiza os deliverables (contrato/estado/testes) sobre cada fatia.
3. **Triagem.** Agregue os CTs/RN relevantes num dossiê por feature e decida o `intent` de cada um (preserve/fix/redesign/remove — as 3 pré-condições em §5.1). Só um dossiê `pronto_para_us` avança.
4. Agrupe CTs decididos em RF e depois em US no **§5**, dentro de épicos organizados por dimensão de risco (§6) — não tela por tela.
5. Desenvolva cada US no **§6** (vista de decisão do PO): história, RN, CA em Gherkin, cobertura de cenários, decisões/perguntas abertas.
6. Preencha o **§7** (insumos do dev): contrato recuperado, dependências e sinal de ordem de migração, no nível do épico.
7. Consolide na **Matriz (§8)** — nasce de §6, nunca o inverso.
8. **Substitua todos os exemplos** (`LoginActivity`, cupom etc.). Valide com o PO cada item 🟡 e leve os ⬜ ao time antes de publicar.

## Convenções

- **`origin` por afirmação (fixo):** 🟢 recuperado do código (âncora `arquivo:linha`) · 🟡 inferido (hipótese de engenharia, sem âncora direta) · ⬜ fora do alcance. Nunca disfarce uma regra sem âncora concreta de inferência comum — marque o ponto cego. `origin` não muda depois de escrito; quem confirma o achado é `confidence` (2ª fonte / PO), quem decide o que fazer é `intent` (§5.1) — não confundir os três.
- **Status de alcance do run:** se o run rodou sob parede conhecida (ofuscação pesada, tamper, contrato fora do bytecode), preencha `normal`/`degradado`/`no-go` em §2 — não invente um `normal` só para simplificar; o campo existe para o cliente calibrar quanto do relatório é extração direta vs. inferência sob limite.
- **RN dentro da US, sem catálogo global** — a Matriz (§8) é a única vista consolidada, gerada a partir de §6. É uma aposta estrutural validada em ~1 épico por rodada; se a citação cruzada entre épicos escalar mal, reavalie explicitamente.
- **Status de cobertura (§8):** "confirmado em código **e** em tela" (2ª fonte da dinâmica) diz mais que "só em código". Registre a triangulação, não uma escala paralela.
- **Derivação da US** (o que é 🟢 capability vs. 🟡 persona/benefício) e o mecanismo do pipeline: consulte a *Reach map* de `method.md`; não reescreva aqui.

## Entrega em `.md`

O entregável do cliente é o **`modelo-relatorio.pt-BR.md` preenchido**, entregue como Markdown — **sem conversão**. O diagrama do §3 é **Mermaid inline**, que renderiza nativo no GitHub/GitLab/VS Code/Obsidian; não há pandoc nem imagem embarcada (era de lá que vinham os erros de formatação do `.docx`, por isso a entrega migrou para `.md`). Se o destinatário usar um viewer sem Mermaid, exporte um PNG opcional (`mermaid-cli`) ao lado — mas o `.md` é a fonte. **Entregue só o relatório**, nunca este guia.

*(Changelog do modelo: no histórico do git, não no template.)*
