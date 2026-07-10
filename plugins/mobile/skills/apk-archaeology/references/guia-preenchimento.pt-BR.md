# Guia de preenchimento — modelo de relatório apk-archaeology

> **Companheiro do template** `modelo-relatorio.pt-BR.md`. Para **quem preenche** o relatório (e quem mantém o template) — **não** vai para o cliente. O *método* de análise (pipeline, reach map, spec da dinâmica) vive em `method.md`/`SKILL.md` — fonte única, não reescrito aqui.

## Ordem de preenchimento

1. Cabeçalho de identificação + **§2 Escopo e Limitações** — a moldura primeiro.
2. Rode/consulte o pipeline estático (`SKILL.md`, *Steps*) e preencha o **§4 Inventário de CT** a partir da saída consolidada.
3. Agrupe CTs em RF e depois em US no **§5**.
4. Desenvolva cada US no **§6** (vista de decisão do PO): história, RN, CA em Gherkin, cobertura de cenários, decisões/perguntas abertas.
5. Preencha o **§7** (insumos do dev): contrato recuperado, dependências e sinal de ordem de migração, no nível do épico.
6. Consolide na **Matriz (§8)** — nasce de §6, nunca o inverso.
7. **Substitua todos os exemplos** (`LoginActivity`, cupom etc.). Valide com o PO cada item 🟡 e leve os ⬜ ao time antes de publicar.

## Convenções

- **Origem por afirmação:** 🟢 recuperado do código (âncora `arquivo:linha`) · 🟡 inferido (o PO ratifica) · ⬜ fora do alcance. Nunca disfarce uma regra sem âncora concreta de inferência comum — marque o ponto cego.
- **RN dentro da US, sem catálogo global** — a Matriz (§8) é a única vista consolidada, gerada a partir de §6. É uma aposta estrutural validada em ~1 épico por rodada; se a citação cruzada entre épicos escalar mal, reavalie explicitamente.
- **Status de cobertura (§8):** "confirmado em código **e** em tela" (2ª fonte da dinâmica) diz mais que "só em código". Registre a triangulação, não uma escala paralela.
- **Derivação da US** (o que é 🟢 capability vs. 🟡 persona/benefício) e o mecanismo do pipeline: consulte a *Reach map* de `method.md`; não reescreva aqui.

## Entrega em `.md`

O entregável do cliente é o **`modelo-relatorio.pt-BR.md` preenchido**, entregue como Markdown — **sem conversão**. O diagrama do §3 é **Mermaid inline**, que renderiza nativo no GitHub/GitLab/VS Code/Obsidian; não há pandoc nem imagem embarcada (era de lá que vinham os erros de formatação do `.docx`, por isso a entrega migrou para `.md`). Se o destinatário usar um viewer sem Mermaid, exporte um PNG opcional (`mermaid-cli`) ao lado — mas o `.md` é a fonte. **Entregue só o relatório**, nunca este guia.

*(Changelog do modelo: no histórico do git, não no template.)*
