#!/usr/bin/env bash
# Launch do app via entrypoint marionette + captura determinística do URI do VM service.
# Uso: run.sh -d <simulator-device-id> [-f <flavor>] [-e <env-file>] [-t <timeout-s>] [-a <app-dir>]
set -euo pipefail

FLAVOR="dev"
ENV_FILE=""
DEVICE=""
TIMEOUT=600
DRY_RUN=0
APP_DIR_OVERRIDE=""
URI_FILE="/tmp/marionette_vm.uri"
LOG_FILE="/tmp/marionette_run.log"

usage() { echo "uso: run.sh -d <device-id> [-f flavor=dev] [-e env-file=derivado do flavor] [-t timeout-s=600] [-a app-dir] [-n dry-run]" >&2; exit 2; }

while getopts "d:f:e:t:a:n" opt; do
  case "$opt" in
    d) DEVICE="$OPTARG" ;;
    f) FLAVOR="$OPTARG" ;;
    e) ENV_FILE="$OPTARG" ;;
    t) TIMEOUT="$OPTARG" ;;
    a) APP_DIR_OVERRIDE="$OPTARG" ;;
    n) DRY_RUN=1 ;;
    *) usage ;;
  esac
done

# Device id é prerequisito explícito — sem default silencioso apontando pra máquina de alguém.
[[ -n "$DEVICE" ]] || { echo "ERRO: device id obrigatório (-d). Liste com: xcrun simctl list devices booted" >&2; usage; }

# Convenção comum: dev → env.json; demais flavors → env_<flavor>.json. Override com -e.
# Ajuste esta convenção pra bater com a do seu projeto (ver references/SETUP.md).
if [[ -z "$ENV_FILE" ]]; then
  if [[ "$FLAVOR" == "dev" ]]; then ENV_FILE="env.json"; else ENV_FILE="env_${FLAVOR}.json"; fi
fi

# Resolve o app dir: por padrão, o diretório atual. Use -a se o app vive em outro path
# (ex.: monorepo com o app numa subpasta).
if [[ -n "$APP_DIR_OVERRIDE" ]]; then
  APP_DIR="$APP_DIR_OVERRIDE"
else
  APP_DIR="$(pwd)"
fi
if [[ ! -f "$APP_DIR/lib/main_marionette.dart" ]]; then
  echo "ERRO: lib/main_marionette.dart não encontrado em $APP_DIR (aponte o app com -a)" >&2
  exit 1
fi
cd "$APP_DIR"

[[ -f "$ENV_FILE" ]] || { echo "ERRO: env file '$ENV_FILE' não existe em $APP_DIR (aponte outro com -e)" >&2; exit 1; }

# Surface o backend real: a variável que decide o AppFlavor (config do projeto) — nunca assuma.
BACKEND="$(python3 -c "import json; print(json.load(open('$ENV_FILE')).get('ENVIRONMENT', '<ausente>'))" 2>/dev/null || echo '<indisponível>')"
echo "==> flavor nativo: $FLAVOR | env file: $ENV_FILE | backend (ENVIRONMENT): $BACKEND"
if [[ "$BACKEND" == "<ausente>" ]]; then
  echo "AVISO: '$ENV_FILE' não define a chave de backend esperada — confira a convenção do seu projeto." >&2
fi

if [[ "$DRY_RUN" == "1" ]]; then
  echo "==> dry-run: app dir resolvido = $APP_DIR | device = $DEVICE | nada lançado."
  exit 0
fi

# Mata runs duplicados (trap conhecida: VM service não anexa com runs acumulados).
pkill -f "main_marionette" 2>/dev/null && sleep 1 || true

rm -f "$URI_FILE"
echo "==> flutter run em background (log: $LOG_FILE)..."
nohup flutter run -t lib/main_marionette.dart --flavor "$FLAVOR" \
  --dart-define-from-file="$ENV_FILE" -d "$DEVICE" \
  --vmservice-out-file "$URI_FILE" >"$LOG_FILE" 2>&1 &
FLUTTER_PID=$!

for ((i = 0; i < TIMEOUT; i += 5)); do
  if [[ -s "$URI_FILE" ]]; then
    # Guard contra leitura no meio do write: duas leituras iguais = conteúdo estável.
    RAW="$(cat "$URI_FILE")"
    sleep 1
    [[ "$RAW" == "$(cat "$URI_FILE")" ]] || continue
    [[ "$RAW" == http* || "$RAW" == ws* ]] || continue
    WS="$RAW"
    [[ "$WS" == http* ]] && WS="${WS/#http/ws}"
    WS="${WS%/}"
    [[ "$WS" == */ws ]] || WS="$WS/ws"
    echo "==> VM service: $RAW"
    echo "==> connect URI (marionette__connect): $WS"
    exit 0
  fi
  kill -0 "$FLUTTER_PID" 2>/dev/null || {
    echo "ERRO: flutter run morreu — tail de $LOG_FILE:" >&2
    tail -20 "$LOG_FILE" >&2
    exit 1
  }
  sleep 5
done

echo "ERRO: timeout (${TIMEOUT}s) esperando URI em $URI_FILE — veja $LOG_FILE." >&2
echo "Se o simulador acumulou estado (vários launch/kill), reboot sem erase — ver Gotchas do SKILL.md." >&2
exit 1
