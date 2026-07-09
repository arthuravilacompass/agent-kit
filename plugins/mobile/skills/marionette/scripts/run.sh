#!/usr/bin/env bash
# App launch via the marionette entrypoint + deterministic capture of the VM service URI.
# Usage: run.sh -d <simulator-device-id> [-f <flavor>] [-e <env-file>] [-t <timeout-s>] [-a <app-dir>]
set -euo pipefail

FLAVOR="dev"
ENV_FILE=""
DEVICE=""
TIMEOUT=600
DRY_RUN=0
APP_DIR_OVERRIDE=""
URI_FILE="/tmp/marionette_vm.uri"
LOG_FILE="/tmp/marionette_run.log"

usage() { echo "usage: run.sh -d <device-id> [-f flavor=dev] [-e env-file=derived from flavor] [-t timeout-s=600] [-a app-dir] [-n dry-run]" >&2; exit 2; }

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

# Device id is an explicit prerequisite — no silent default pointing at someone else's machine.
[[ -n "$DEVICE" ]] || { echo "ERROR: device id required (-d). List with: xcrun simctl list devices booted" >&2; usage; }

# Common convention: dev → env.json; other flavors → env_<flavor>.json. Override with -e.
# Adjust this convention to match your project's (see references/SETUP.md).
if [[ -z "$ENV_FILE" ]]; then
  if [[ "$FLAVOR" == "dev" ]]; then ENV_FILE="env.json"; else ENV_FILE="env_${FLAVOR}.json"; fi
fi

# Resolve the app dir: defaults to the current directory. Use -a if the app lives in
# another path (e.g. a monorepo with the app in a subfolder).
if [[ -n "$APP_DIR_OVERRIDE" ]]; then
  APP_DIR="$APP_DIR_OVERRIDE"
else
  APP_DIR="$(pwd)"
fi
if [[ ! -f "$APP_DIR/lib/main_marionette.dart" ]]; then
  echo "ERROR: lib/main_marionette.dart not found in $APP_DIR (point to the app with -a)" >&2
  exit 1
fi
cd "$APP_DIR"

[[ -f "$ENV_FILE" ]] || { echo "ERROR: env file '$ENV_FILE' does not exist in $APP_DIR (point to another with -e)" >&2; exit 1; }

# Surface the real backend: the variable that decides the AppFlavor (project config) — never assume.
BACKEND="$(python3 -c "import json; print(json.load(open('$ENV_FILE')).get('ENVIRONMENT', '<missing>'))" 2>/dev/null || echo '<unavailable>')"
echo "==> native flavor: $FLAVOR | env file: $ENV_FILE | backend (ENVIRONMENT): $BACKEND"
if [[ "$BACKEND" == "<missing>" ]]; then
  echo "WARNING: '$ENV_FILE' does not define the expected backend key — check your project's convention." >&2
fi

if [[ "$DRY_RUN" == "1" ]]; then
  echo "==> dry-run: resolved app dir = $APP_DIR | device = $DEVICE | nothing launched."
  exit 0
fi

# Kill duplicate runs (known trap: VM service won't attach with stale runs piled up).
pkill -f "main_marionette" 2>/dev/null && sleep 1 || true

rm -f "$URI_FILE"
echo "==> flutter run in background (log: $LOG_FILE)..."
nohup flutter run -t lib/main_marionette.dart --flavor "$FLAVOR" \
  --dart-define-from-file="$ENV_FILE" -d "$DEVICE" \
  --vmservice-out-file "$URI_FILE" >"$LOG_FILE" 2>&1 &
FLUTTER_PID=$!

for ((i = 0; i < TIMEOUT; i += 5)); do
  if [[ -s "$URI_FILE" ]]; then
    # Guard against reading mid-write: two equal reads = stable content.
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
    echo "ERROR: flutter run died — tail of $LOG_FILE:" >&2
    tail -20 "$LOG_FILE" >&2
    exit 1
  }
  sleep 5
done

echo "ERROR: timeout (${TIMEOUT}s) waiting for URI at $URI_FILE — see $LOG_FILE." >&2
echo "If the simulator accumulated state (several launch/kill cycles), reboot without erase — see Gotchas in SKILL.md." >&2
exit 1
