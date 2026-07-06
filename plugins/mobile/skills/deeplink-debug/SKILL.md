---
name: deeplink-debug
description: Invoque quando um deeplink/App Link abre no navegador em vez do app, falha ao rotear, abre a tela errada, ou você precisa validar comportamento de deeplink num device. Sintomas — "abre no navegador", "não abre o app", link está verified mas ainda abre no navegador, quebrou depois de reativar, funciona numa versão de Android/iOS mas não em outra.
---

# Deeplink / App Link Debugging (Android)

## Config do projeto

Troque os hosts/domínios dos exemplos abaixo pelos do seu app. O mecanismo (as três portas, os comandos `adb`/`am`/`logcat`, a validação de assetlinks/AASA) é genérico Android/iOS e não muda entre projetos.

## Overview

Um App Link abrindo no navegador tem **três portas independentes**, e a forma mais rápida de perder horas é deixar um sinal verdadeiro-mas-tangencial (`verified`) fechar o caso cedo demais.

**Princípio central: `verified` ≠ `matches`.** Verificação de domínio (assetlinks) e matching de intent-filter são passos *separados* do Android. Um domínio pode estar `verified` enquanto o intent-filter não casa nenhum path — o app está aprovado pro domínio mas não declara regra que capture a URL.

## As três portas (verifique nesta ordem)

1. **Roteamento do SO (app de origem):** o app que recebe o tap decide como abrir o link. **Custom Tab bypassa App Links inteiramente** — WhatsApp, Google Keep, Google Messages abrem links num Chrome tab embutido e nunca consultam o resolver. Um resultado "navegador" vindo desses apps não prova nada.
2. **Verificação (assetlinks):** o domínio pertence ao app? → `pm get-app-links` (`verified` / `1024`). Responde *só* a porta 2.
3. **Matching (intent-filter):** a URL casa com uma regra que o app declarou? → o teste decisivo abaixo.

## Método de diagnóstico

Teste as portas diretamente em vez de tocar em apps (que têm viés). O teste decisivo é **matching**, forçando o package:

```
adb shell am start -a android.intent.action.VIEW -c android.intent.category.BROWSABLE -d "<url>" <pkg>
```
- `START_INTENT_NOT_RESOLVED` → o filtro não casa nada (bug de matching).
- abre o app → matching OK.

**Sempre rode um controle:** o mesmo comando num host cujo intent-filter difere pelo único elemento que você suspeita (ex.: um host sem o novo `<uri-relative-filter-group>`). Caso falha + controle passa com uma variável diferente = causa provada.

Cruze com **distribuição de versão**: "funciona no Android 12/iOS, quebra no 15+" aponta pra uma feature de matching que só existe em Android mais novo (ex.: `uri-relative-filter-group`, API 35+).

## Viés de instrumento (não trate como evidência)

| Instrumento | Por que mente |
|---|---|
| Tap do WhatsApp / Keep / Messages | Custom Tab — bypassa App Links por design |
| `am start` sem pkg / `cmd package resolve-activity` | contexto de shell — sempre resolve pro navegador, ignora verificação de App Link |
| `pm get-app-links: verified` | responde verificação, NÃO matching |

## Playbook completo de comandos

Ver [references/PLAYBOOK.md](references/PLAYBOOK.md) — pareamento adb wifi, tabela completa "qual comando responde qual pergunta", captura de logcat (`ActivityTaskManager` START + `CustomTabsIntent`), inspeção de APK (`apksigner`/`aapt`), e validação de assetlinks por host.

## Common mistakes

- Concluir "não é o app, é o método de teste" a partir de `verified` + navegador. Essa é a armadilha real — verifique matching com `am start pkg=` antes de culpar o canal.
- Empilhar taps falhos (todos Custom Tab) como se fossem evidência de bug. Viés repetido ≠ confirmação.
- Comparar o manifest atual contra o *último commit que funcionava* em vez da *versão que de fato funcionou* — o diff real às vezes está numa baseline mais antiga do que a comparação assume.
