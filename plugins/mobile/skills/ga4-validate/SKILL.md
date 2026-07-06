---
name: ga4-validate
description: Invoque para validar tracking GA4 (tela × evento, antes × depois de uma mudança) num app Flutter rodando no simulador/emulador — dirige o app, captura o evento real com params, screenshota, casa tela × evento, monta a tabela de CTs e o report visual. Gatilhos em pt-BR — "valida os eventos GA4 dessa tela", "confirma o tracking antes e depois dessa mudança", "captura o evento real desse componente".
---

# GA4 Validate — Validação de tracking GA4 (tela × evento, antes × depois)

Roteiro reusável para validar eventos GA4 de componentes de um app Flutter rodando no simulador/emulador: dirige o app, captura o evento **real** com params, screenshota, casa tela × evento, e monta o registro (tabela de CTs + report visual). Serve US de GA4 novas e regressivos (comparação antes × depois).

Reusa a plumbing de transporte do skill `mobile:export-logs` e o skill `mobile:marionette` para dirigir o app.

## Config do projeto

Preencha antes de usar: quais eventos/telas fazem parte do escopo, se o projeto tem alguma camada de tracking além da chamada direta ao SDK de analytics (ex.: middleware próprio que só dispara sob certas condições), e o nome dos arquivos-alvo pra instrumentação temporária (§Método A). O mecanismo de captura (3 vias abaixo) é universal Firebase/GA4 + Dart VM service — não muda entre projetos.

## Quando usar

- US de tracking que precisa de evidência **tela × evento** (ex.: `view_promotion`/`select_promotion`/`view_item_list`/`select_item`/`select_content`, ou os nomes de evento do seu projeto).
- **Regressivo de GA4:** capturar baseline ("antes"), aplicar a mudança, re-capturar idêntico ("depois"), comparar CT a CT.

## O que produz

1. Por componente/CT: o **evento real capturado** (nome + params) + **screenshot** da tela.
2. **Tabela de CTs** (esperado × capturado × veredito).
3. (Opcional) **Report visual** — comece pela casca `ga4-report-template.html` (deste skill) e preencha as seções. Publicar via a ferramenta de artifact do seu setup, se houver.

## Pré-requisitos (explícitos, nunca default silencioso)

| Input | Como resolver |
|---|---|
| Device | `xcrun simctl list devices booted` (iOS) / `adb devices` (Android) |
| Backend | variável de ambiente que decide o backend (não o `--flavor` sozinho) — ver skill `mobile:marionette` |
| Build com a camada de tracking completa | se o projeto tem tracking adicional além do SDK direto (middleware, decorator), confirme que o build sob teste inclui essa camada — um build sem ela dá falso-negativo |
| Camada extra só dispara sob condição | se sua camada de tracking extra tem uma pré-condição (ex.: só dispara com sessão autenticada, ou só em determinado ambiente), confirme que a condição está satisfeita antes de concluir "não dispara" |
| Logado / estado | fluxos autenticados exigem login; o componente-alvo precisa renderizar na tela testada |

## Métodos de captura — 3 camadas que medem coisas DIFERENTES (não é "uma melhor")

Cada camada observa um ponto distinto do fluxo — escolha pela pergunta que precisa responder:

- **A. Reader `vm_service` — *wire-truth*** (o que sai de fato, pós-sanitização de params). Agent-readable.
- **B. DebugView — *recepção Firebase*** (o que o Firebase recebeu). Spot-check manual em prod; console web, o agente não lê/screenshota.
- **C. Decorator/interceptor na interface de analytics — *boundary*** (o que o app **chamou**, antes de qualquer sanitização) — só existe se o projeto tiver esse seam. Mede a boundary, não o fio: params reconstruídos, pode não ver tracking adicional (middleware) que roda depois da chamada de analytics, e pode falso-flagar nomes que a sanitização normaliza (ex.: hífen virando underscore). Complementa A/B, não substitui.

| Situação | Método |
|---|---|
| **ambiente sem stream de debug vinculado** (DebugView precisa de stream prod-like) | **A. Reader** |
| **Registro reprodutível** (CTs, antes×depois, o agente precisa ler/screenshotar) | **A. Reader** |
| **Camada de tracking adicional (middleware) do projeto** | zero-touch se o skill `mobile:export-logs` já cobrir a chamada HTTP · ou **A** instrumentando o ponto de envio · ou proxy (Charles/Proxyman). DebugView **não** mostra middleware fora do SDK de analytics. |
| **prod + spot-check manual rápido** | **B. DebugView** |
| **cobertura ampla zero-touch** (se o projeto já tiver o decorator) | **C. Decorator** |

### A. Reader `vm_service` (agent-readable)

**Gotcha central:** `dart:developer.log()` **NÃO cai no log do sistema operacional** (`simctl log stream` / equivalente); e os helpers de analytics geralmente só logam no `catch` (silêncio no sucesso). Então captura-se **instrumentando** + lendo o stream `Logging` do VM service.

1. **Instrumentar (temporário — REVERTER no fim):** adicionar `log('[GA4] …')` logo **após** cada chamada de analytics bem-sucedida, por **âncora** (não por linha — linhas driftam), nos arquivos-alvo do seu projeto (config do projeto: onde a camada de analytics loga hoje). Logue o nome do evento + params-chave relevantes ao seu CT.
   - Se o projeto bloqueia `print`/`debugPrint` em código de produção (hook de lint, config do projeto), use `log()` — ele passa por esse tipo de gate.
2. **Capturar:** leia o stream `Logging` do VM service e filtre as linhas instrumentadas (ex.: `[GA4]`).

```dart
// Recipe: conectar ao VM service e escutar o stream Logging.
// Uso: dart run <este-arquivo>.dart <ws-uri>   (ws-uri vem do log do app: "Dart VM service is listening on")
import 'package:vm_service/vm_service.dart';
import 'package:vm_service/vm_service_io.dart';

Future<void> main(List<String> args) async {
  final service = await vmServiceConnectUri(args.first);
  await service.streamListen(EventStreams.kLogging);
  service.onLoggingEvent.listen((e) {
    final msg = e.logRecord?.message?.valueAsString;
    if (msg != null && msg.contains('[GA4]')) print(msg);
  });
  print('reader GA4 escutando em ${args.first} — dirija o app; Ctrl+C pra parar');
}
```

3. **Reverter:** `git checkout` nos arquivos instrumentados. **Confirme o repo limpo** (`git status --short lib/`) antes de encerrar.

### B. DebugView (zero-touch — spot-check manual em prod)

- **iOS sim:** `xcrun simctl launch booted <bundle> -FIRDebugEnabled YES`.
- **Android:** `adb shell setprop debug.firebase.analytics.app <package>`.
- Exige stream vinculado (prod); é console web — o agente não lê/screenshota programaticamente. Bom pra conferência manual, ruim pra registro reprodutível.

## Fluxo

1. **Preflight** — skill `mobile:marionette` disponível? Device booted? Build com a camada de tracking completa (se aplicável)? Ambiente = o esperado?
2. **Preparar captura** — método A (instrumentar) ou B (DebugView).
3. **Launch + connect** — skill `mobile:marionette` (`scripts/run.sh` → `marionette__connect`). Pegue a ws URI do log do app.
4. **Dirigir + screenshot** — `get_interactive_elements` → `tap`/`scroll_to`. Screenshot em disco quando o marionette só devolve inline (`xcrun simctl io booted screenshot <path>.png` ou equivalente Android). Coords do marionette são **lógicas**, não pixels.
5. **Capturar + casar** — o reader imprime o evento; **case tela × evento** e confirme a **origem** (o param de localização/tela = a tela testada — mata falso-positivo de outra tela).
6. **Registrar** — preencha a tabela de CTs (esperado × capturado × veredito). Marque `EMPÍRICO` (visto ao vivo) / `código` (verificado no fan-out, não exercitado) / `não dispara` (by-design).
7. **(Opcional) Report** — comece pela casca `ga4-report-template.html` e preencha as seções.
8. **Reverter** — desfazer a instrumentação; confirmar repos limpos.

## Regressivo — antes × depois

- A **rodada baseline** é o "antes" (guarde a TABELA-CTS + screenshots).
- Após a mudança, **re-rode IDÊNTICO** (mesmo método, device, build) → "depois".
- **Compare CT a CT.** Sucesso = os CTs-alvo mudaram do esperado. Atualize a coluna "depois" e troque painéis ilustrativos por payload real.

## Plataformas

| Plataforma | Status | Adaptação |
|---|---|---|
| **iOS Simulator / macOS / reader** | caminho canônico deste roteiro (provado numa rodada real) | — |
| **Android** | reader = **o mesmo** (é VM Dart, agnóstico); DebugView via `adb setprop`; screenshot via `adb exec-out screencap -p`; ws URI do `flutter run`/logcat | validar na primeira vez |
| **Windows** | **só Android** — iOS sim NÃO roda em Windows; `simctl` não existe (usar `adb`) | validar na primeira vez |

> Honestidade: valide cada adaptação de plataforma na primeira vez que for usada — não assuma que o mecanismo generaliza sem checar.

## Gotchas

- **Zero eventos da camada extra de tracking** → build sem essa camada, ou a pré-condição dela não foi satisfeita. Confirme ambos antes de reportar "não dispara".
- **Nomenclatura de param pode divergir entre a camada de middleware e o GA4 puro** (singular vs. plural, ou nomes ligeiramente diferentes pro mesmo conceito) — confira contra o esperado do seu projeto antes de marcar como bug.
- **Impressão por-componente** costuma ter threshold (ex.: ≥50% visível por 1s) e re-dispara ao voltar à tela — não é bug se disparar de novo.
- **Instrumentação não revertida** = risco de vazar log em commit. Sempre `git checkout` + verificar.

## Referências

- Dirigir o app: skill `mobile:marionette`
- Transporte VM service (reuso): skill `mobile:export-logs`
- Casca do report: `ga4-report-template.html` (este skill)
