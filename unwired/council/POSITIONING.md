# Conselho de Posturas Epistêmicas — Posicionamento

## Antes de tudo: o status do que segue

O que vem abaixo é uma **hipótese forte**, não um resultado. Ela se apoia em literatura de HCI sobre overreliance (estabelecida em outros contextos, extrapolada para este) e num trial interno com **N=1 por postura**. Os claims de *mecanismo* — que o Conselho força um modo de raciocínio, que os nomes roteiam procedimentos distintos — são apostas declaradas, não fatos medidos. Leia o resto com isso em mente. Um manifesto sobre calibração epistêmica que se apresentasse como prova seria a primeira coisa a falhar no próprio teste.

## A coisa que ele é

O Conselho é projetado para operar como uma **cognitive forcing function**. A ideia, direto: um AI fluente, rápido e concordante facilita aceitar a primeira resposta plausível e reforçar o enquadramento que você já trouxe. O Conselho existe para criar as condições de uma segunda olhada nos pontos onde aceitar barato sai caro — *condições*, não garantia: invocar uma postura pode ele mesmo ser um ato automático. A deliberação não está em chamar o nome; está no procedimento que o nome dispara.

A formulação que o move: dentro do que o AI te entrega, **é o único elemento cujo propósito declarado é resistir ao seu próprio enquadramento.** O resto do que um assistente produz — código, review, breakdown — está, por construção, a serviço de te levar adiante. O Conselho está a serviço de te fazer parar e olhar de novo. Essa assimetria é o produto. (Um reviewer humano, um teste que falha, um linter também resistem ao seu framing — por isso o claim é restrito ao AI-side e ao *propósito primário*: nenhuma dessas outras peças existe para isso.)

Não é spec, não é tarefa, não é pipeline. São seis **modos de raciocínio** que se vestem de propósito. A saída de cada um é **um movimento sobre o seu raciocínio** — um reframe, uma hipótese mantida viva, um ponto de propagação que você não tinha visto — nunca um artefato a mais.

## Por que não "mais perspectivas"

Quase todo toolkit do gênero vende a mesma coisa: *decisões melhores via diversidade de perspectivas.* O Conselho recusa isso de propósito. Ele vende **preservação do seu julgamento** — e é explícito ao dizer que não aumenta diretamente a taxa de decisões corretas. O que ele tenta reduzir é a taxa de decisões *não-deliberadas*; se isso melhora o resultado depende da qualidade do seu julgamento, que ele preserva mas não substitui.

O problema-alvo não é falta de informação. É um padrão de overreliance documentado em HCI: na presença de um sistema fluente, o operador tende a confiar rápido e a interrogar menos, e a confiança no sistema cresce sem que a qualidade da decisão acompanhe. Mais confiança no AI **não** é monotonicamente boa. (A literatura mediu isso sobretudo em automação com loop de feedback curto; transferir o efeito para decisão de software com o Conselho como implementação é extrapolação plausível, não fato aplicado. E o deslize-para-resposta-rápida é só um dos mecanismos — *automation bias* e atrofia de habilidade são adjacentes e não são resolvidos da mesma forma; ficam fora deste claim.)

## A nuance que não pode ser apagada

Aqui é onde a maioria dos sistemas mente para si mesma.

**Anti-sycophancy não vem de nomear a postura.** O mesmo Claude, no mesmo thread em que vinha concordando, é capaz de *performar* ceticismo — vestir "Zeno", soar adversarial, e ainda curvar tudo para o *lean* que você demonstrou. Chamar a postura não produz a propriedade.

A propriedade vem de **separação estrutural**: contexto isolado, prompt adversarial, review anonimizado — o raciocínio acontece sem ver para onde você torcia.

- Isso foi **demonstrado no trial (N=1) nos dois subagents isolados, Maxwell e Zeno** — em domínio estrutural. Eles rodam fora do thread, recebem só o problema, e acharam coisas que o thread não pediria: Maxwell, um consumidor lendo o coordinator direto (largura); Zeno, uma janela de um frame com estado inconsistente (tempo), sem overlap com a passada default. N=1 mostra que a separação produziu cobertura *diferente* — não prova que produz cobertura *correta* em geral, e a vantagem pode encolher em decisões que dependem do contexto semântico do thread (naming, produto), onde o isolamento vira desvantagem. A separação reduz o viés de contexto do thread, não o viés da distribuição de treino do modelo base.
- Nos quatro overlays inline (Schrödinger, Bohr, Epicurus, Sagan) **não há separação estrutural** — só disposição. **V1 materializou os dispositivos in-thread**: um *Restate Gate* (passo 0, divergência SIM/NÃO) e o *steelman* obrigatório do lado oposto no callout. Eles elevam o custo de performar concordância — mas rodam no mesmo thread que viu o *lean*, então seguem **disposição, não garantia**. A separação estrutural real não veio de um "review anonimizado" embutido (cortado no V1); veio da **cláusula de escalonamento** para o subagent isolado `epistemic-council` (modo cego). Sem escalar, o overlay é uma boa disposição; a propriedade adversarial só é estrutural fora do thread.

Um manifesto sobre anti-sycophancy que fingisse que seus overlays já são adversariais seria, ele mesmo, sycophantic. V1 honra isso: os overlays ganharam dispositivos que elevam o custo, mas só o escalonamento isolado reivindica a propriedade. Um projeto de origem chegou a desenhar um fluxo de validação faseado (mecânico + retrospectiva-com-stake + A/B isolado) que se recusa a dar nota de accuracy — se for reproduzir esse desenho, projete-o de novo no contexto do novo projeto em vez de herdar o registro antigo.

## A aposta sobre identidade

O nome — Bohr, Maxwell, Zeno — **não é cosmético: é a posição assumida do Conselho.** Mas a ordem honesta é esta. A encarnação em *inference-time* (o modelo "vestindo" Bohr agora) é uma **extrapolação declarada** do que se observa em *training-time* — plausível, não verificada por ablação. *Se* ela se sustenta, cada nome roteia para uma interrogação e um procedimento distintos (persona vectors selecionam *como* o problema é atacado), e isso separa o Conselho do padrão dominante "role = task", onde a persona é decoração sobre o mesmo prompt. A hipótese rival não foi descartada: o efeito pode vir das associações de treino com os personagens, não do procedimento — e nesse caso a propriedade é específica do modelo usado, não transferível. Trocar "Schrödinger" por "Postura de Superposição" e comparar o output é o teste que ainda não rodou.

O que é **FATO** e o que é **APOSTA**:

- **Demonstrado (N=1):** a separação estrutural produz cobertura diferenciada *na medida da própria separação* — nos subagents, em domínio estrutural.
- **Fundamentado em literatura (extrapolado):** forcing functions reduzem overreliance em System-1; a transferência para este workflow é aposta plausível, não medida aqui.
- **Fato (problema, não solução):** calibração de confiança em AI é problema real. Que *este* design recalibre essa confiança é a aposta.
- **APOSTA (não medida):** que vestir as posturas preserva *soberania epistêmica* — sua capacidade de seguir fazendo boas perguntas — e que há um efeito de segunda ordem em que você *internaliza* as posturas e interroga melhor sem o tooling. Plausível por analogia com a literatura de metacognição e scaffolding cognitivo; sem medição direta neste contexto. Não será apresentado como mais do que aposta.

## Autoridade, gatilho, cliente

**Autoridade: só advisory.** Ofereço, não decido. Nunca bloqueia, nunca exige, nunca trava o seu commit. Preservar o seu julgamento e depois sequestrá-lo seria contradição na própria tese.

**Gatilho:** decisões de **alto custo de reversão**, **pré-commit** — contrato de API compartilhada, mudança de estado persistido, merge difícil de desfazer. E, igualmente, quando o custo de reversão é **incerto ou subestimado** — porque aí o System-2 ainda não foi ativado e a forcing function tem mais trabalho a fazer. **Silêncio** no trabalho mecânico de uma decisão já clara: a forcing function que dispara sempre vira ruído e ensina a ser ignorada.

**Cliente:** solo, opt-in. Escrito primeiro para o seu uso. Compartilhável com a squad depois — só por opt-in explícito, nunca imposto no fluxo de quem não pediu.

## Anti-contaminação de output do AI (ritual)

O Conselho guarda as **decisões do dev**, não as **saídas do AI**. Mas a saída do AI enviesa silenciosamente o próximo passo quando viaja para um contexto que não tem como conferi-la — um **handoff, resumo de sessão, "prompt da próxima sessão", spec entregue a um implementer, descrição de PR**. Aí o framing do AI vira premissa do próximo executor sem revisão. É a lacuna que *define* a lacuna: o Conselho não a pega, o usuário pega.

**Ritual (não mecanizado — disposição, medir antes de gatear):** antes de entregar um artefato dessa classe *context-seeding*, passá-lo por **review cego** — um subagent isolado (`epistemic-council` / equivalente de exploração) que recebe só a instrução de verificação, **sem o thread nem o framing**. Auto-check no mesmo thread = disposição, não garantia (mesma falha dos overlays inline).

**Checklist mecânico** (verificável sem leitura semântica): (1) sem valores-esperados pré-escritos; (2) framing neutro; (3) aponta-para-a-fonte em vez de re-narrar conclusões.

Por que ritual e não hook: é o ganho *dev-side* mais honesto e verificável do Conselho ("o AI para de enviesar silenciosamente o próximo passo"), mas mecanizar a detecção da classe *context-seeding* sem leitura semântica é incerto — adiado até o ritual provar que paga. Praticado à mão num projeto de origem (validação por subagent cego; limpa). Detalhe e decisão aberta ficam em notas internas do projeto de origem, não incluídas aqui.

## Atualização pós-auditoria (achados de uma validação anterior)

Um ciclo de validação adversarial (workflow multi-agente) + auditoria do mecanismo em disco, rodado num projeto de origem, mudou o enquadramento assim:

- **AI-side vs dev-side (achado central).** A fricção de System-2 que o V1 fabrica é executada **quase toda no lado do AI**, que delibera e entrega o resultado pronto. O ganho que de fato acrua ao **developer** hoje é *output mais lúcido para consumir*, não *developer mais lúcido*. "Cobertura diferenciada" e "interrupção do System-1" são ganhos **AI-side** sólidos — não soberania epistêmica do dev. Separar os dois explicitamente é a correção de pitch.
- **Não é "multiplicativo".** O ganho combinado é **interação condicional** cujo sinal depende de [criticidade da decisão] × [calibração da fricção] × [engajamento real] — pode ser zero ou negativo (fricção mal-calibrada degrada throughput; um dos efeitos hipotetizados na literatura de referência não foi suportado). Nada o sustenta como produto sempre-positivo.
- **2ª ordem = dívida permanente** (antes: "aposta não-medida"). A internalização é **estruturalmente impossível de emergir** no horizonte curto sem (1) prática ativa, (2) fading estruturado, (3) feedback de outcome, (4) densidade de várias semanas — e silêncio-no-mecânico vs densidade-de-prática são incompatíveis sem um **modo de prática separado** que o V1 não tem. Registrada como dívida permanente, não propriedade no roadmap.
- **Confirmado em disco (num projeto de origem):** os 3 subagents cegos existiam de fato (separação anti-sycophancy real, mas opt-in/rara). Um corpus episódico local foi semeado com casos reais do trial — deixou de ser teatro como *recall* (retorna análogos e exibe desfecho). Mas o **produtor automático de outcome seguia ausente por escolha**: o recall não ranqueia por outcome, então não há loop de calibração automático — cabear isso no merge foi adiado (medir-depois).

---

O trial mediu seis posturas; cinco pagaram o custo. Epicurus ficou sub-medido — pode ter sido acidente do problema-alvo (design já enxuto; re-testar num design gordo), pode ser limitação estrutural da postura (cortar o excesso talvez exija um modelo de valor que só Sagan fornece). As duas hipóteses seguem abertas. N=1 por postura dá direção, não licença. O Conselho é uma hipótese forte sobre como manter um humano lúcido ao lado de um AI persuasivo — e é honesto o bastante para dizer onde ainda não provou que funciona.
