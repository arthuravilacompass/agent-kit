# Playbook Ferramental — Deeplink / App Link Android

Comandos concretos. Todos exigem sandbox desabilitada (rede local + adb + acesso ao CoreSimulator/device).

## 1. Conectar ao device sem cabo (adb wifi, Android 11+)

Depuração sem fio tem **duas etapas com portas diferentes** (ambas mudam a cada sessão):

```bash
# Device: Opções do desenvolvedor → Depuração sem fio → ativar
# "Parear com código" mostra IP:PORTA_A + código de 6 dígitos:
adb pair 192.168.1.11:41505 535891      # PORTA_A (pairing) + código
# A tela principal de Depuração sem fio mostra OUTRO IP:PORTA_B (conexão):
adb connect 192.168.1.11:34977          # PORTA_B (connect) — DIFERENTE da de pairing
adb devices                             # confirmar
```
Mac e device na mesma rede wifi. Com mais de um device, mire com `adb -s <IP:PORTA_B> ...` em todo comando.

## 2. Qual comando responde qual pergunta

| Pergunta | Comando |
|---|---|
| Versão do Android / SDK | `adb -s $S shell getprop ro.build.version.release` / `.sdk` |
| App instalado / versão | `adb -s $S shell dumpsys package <pkg> \| grep -E "versionName\|versionCode"` |
| Domínio **verificado**? (porta 2) | `adb -s $S shell pm get-app-links <pkg>` → `verified` / `1024` |
| Estado interno completo (verificação + selection) | `adb -s $S shell "dumpsys package <pkg> \| grep -A20 'Domain verification state'"` |
| Filtros que o SO **registrou** | `adb -s $S shell "dumpsys package <pkg> \| grep -iE 'Scheme\|Authority'"` |
| **O intent-filter casa?** (porta 3, DECISIVO) | `adb -s $S shell am start -a android.intent.action.VIEW -c android.intent.category.BROWSABLE -d "<url>" <pkg>` |
| Quem o sistema escolhe (viés de shell!) | `adb -s $S shell cmd package resolve-activity --brief -a android.intent.action.VIEW -c android.intent.category.BROWSABLE -d "<url>"` |
| Decisão real no tap | `logcat` — ver seção 4 |

**Leitura do `am start`:** `START_INTENT_NOT_RESOLVED` / `unable to resolve` = filtro não casa. Abre a `MainActivity` = casa. Rode sempre um **host de controle** (sem o elemento suspeito) pra isolar a variável.

## 3. Inspecionar o APK (estático, sem device)

```bash
BT="$HOME/Library/Android/sdk/build-tools/35.0.0"
"$BT/apksigner" verify --print-certs app.apk | grep -i "SHA-256"   # cert que assinou (compara com assetlinks)
"$BT/aapt" dump badging app.apk | grep "^package:"                 # package + versionCode
"$BT/aapt" dump xmltree app.apk AndroidManifest.xml | grep -iE "intent-filter|autoVerify|host|uri-relative|pathPrefix"
```

## 4. Capturar a decisão real do tap (logcat)

```bash
adb -s $S logcat -c                                   # limpar buffer
# tocar o link no device, DEPOIS:
adb -s $S logcat -d -v time ActivityTaskManager:I '*:S' | grep -iE "START u0.*(VIEW|<seu-dominio>)"
```
Sinais-chave:
- `cmp=<pkg>/...MainActivity` → App Link roteou pro app ✅
- `cmp=com.android.chrome/...IntentDispatcher` → foi pro navegador
- `CustomTabsIntent#shouldAlwaysUseBrowserUI() = false` → o app de origem abriu em **Custom Tab** (bypassa App Links — resultado inválido como teste de matching)
- `cmp=com.google.android.keep/...LinkResolverActivity` → o Keep interceptou com o próprio resolvedor (idem)

## 5. Validar assetlinks / AASA por host (lado web)

```bash
for h in www.exemplo.com exemplo.com link.exemplo.com; do
  curl -sS -m 15 -o /dev/null -w "%{http_code} %{content_type} server=%header{server}\n" \
    "https://$h/.well-known/assetlinks.json"
done
```
- Compare o `sha256_cert_fingerprints` publicado com o cert do APK (seção 3). Têm que bater.
- Hosts distintos podem ter backends distintos (CDN, servidor web dedicado, apex sem serviço). AASA/assetlinks servido por um host NÃO cobre o outro automaticamente. Confira cada host que seu app declara.

## 6. Forçar re-verificação / manipular selection (experimentos)

```bash
adb -s $S shell pm verify-app-links --re-verify <pkg>
adb -s $S shell pm set-app-links-user-selection --user 0 --package <pkg> true <host>
```
⚠️ Isso muda o estado do device — reverta / avise se for device de outra pessoa.

## Ordem de diagnóstico recomendada

1. `pm get-app-links` → domínio verificado? (se não, é porta 2: assetlinks/cert/host)
2. `am start ... <pkg>` no link problemático + **host de controle** → isola porta 3 (matching)
3. Se matching falha → `aapt dump xmltree` + `git show` do manifesto → achar o elemento (ex.: `uri-relative-filter-group`)
4. Cross-check por versão de Android (12 ok / 15 quebra = feature de matching nova)
5. Só então tap real (de um app que delega, não Custom Tab) pra confirmação end-to-end
