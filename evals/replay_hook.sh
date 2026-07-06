#!/usr/bin/env bash
# replay_hook.sh — harness de replay OFFLINE para hooks do agent-kit. Injeta um
# JSON de evento fake no stdin de um hook, captura o stdout e valida a FORMA da
# saída (hookSpecificOutput.additionalContext ou permissionDecision). Sem LLM,
# sem rede, sem tocar settings.
#
# POR QUE ESTE HARNESS: prova, de forma re-rodável, que a MECÂNICA do replay (stdin
# → hook → stdout → JSON) funciona — independente de qual hook específico está sendo
# exercitado no momento.
#
# Uso:
#   evals/replay_hook.sh --selftest                 # mecânica do harness vs mock hook descartável
#   evals/replay_hook.sh <hook.sh> <evento.json>     # replay genérico (- = stdin)
#     <hook.sh> aceita path absoluto/relativo OU nome bare (ex.: "plan-autoload.sh"),
#     resolvido contra HOOK_DIR (plugins/core/hooks/) quando não encontrado como está.
set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
HOOK_DIR="${REPO_ROOT}/plugins/core/hooks"   # hooks reais do kit — não workspace, não path fixo externo
SENTINEL="REPLAY-SELFTEST"

# ---- $TMPDIR fix (correção 1): nunca /tmp hardcoded. Fallback repo-local se
# TMPDIR não estiver setado (alguns runners de CI não exportam TMPDIR). ----
EVAL_TMP="${TMPDIR:-$REPO_ROOT/.eval-tmp}"
EVAL_TMP="${EVAL_TMP%/}"   # TMPDIR no macOS costuma vir com "/" final
mkdir -p "$EVAL_TMP"

if ! command -v python3 &>/dev/null; then
  echo "ERRO: python3 necessário para validar o JSON de saída." >&2
  exit 2
fi

# ---- helpers de asserção -------------------------------------------------------
PASS=0
FAIL=0
ok()   { echo "  [PASS] $1"; PASS=$((PASS + 1)); }
bad()  { echo "  [FAIL] $1"; FAIL=$((FAIL + 1)); }

# Roda um hook com um JSON de evento no stdin; ecoa o stdout capturado.
# Invoca via `bash "$hook"` (não `"$hook"` direto): não depende do bit +x do hook —
# hooks são despachados pelo Claude Code, não necessariamente executáveis no FS — e
# não muta o modo do arquivo do repo.
run_hook() {
  local hook="$1" event="$2"
  printf '%s' "$event" | bash "$hook"
}

# ---- modo replay genérico ------------------------------------------------------
resolve_hook() {
  local hook="$1"
  if [ -f "$hook" ]; then
    printf '%s' "$hook"
  elif [ -f "$HOOK_DIR/$hook" ]; then
    printf '%s' "$HOOK_DIR/$hook"
  else
    printf '%s' "$hook"   # deixa o caller reportar "não encontrado"
  fi
}

generic_replay() {
  local hook src event
  hook="$(resolve_hook "$1")"
  src="$2"
  if [ ! -x "$hook" ] && [ ! -f "$hook" ]; then
    echo "ERRO: hook não encontrado: $1 (procurado como está e em $HOOK_DIR/)" >&2; exit 2
  fi
  if [ "$src" = "-" ]; then event="$(cat)"; else event="$(cat "$src")"; fi
  local out; out="$(run_hook "$hook" "$event")"
  printf '%s\n' "$out"
  # valida: saída vazia (silêncio) OU JSON parseável
  if [ -z "$out" ]; then
    echo "(saída vazia — silêncio; válido para hooks advisory)" >&2
  elif printf '%s' "$out" | python3 -c "import sys,json; json.load(sys.stdin)" 2>/dev/null; then
    echo "(saída é JSON válido)" >&2
  else
    echo "AVISO: saída não-vazia e não-JSON." >&2; exit 1
  fi
}

# ---- mock hook descartável (só para --selftest) --------------------------------
# Hook trivial sem lógica de projeto: lê o evento inteiro do stdin e emite um
# hookSpecificOutput.additionalContext fixo, ecoando o hook_event_name recebido —
# o suficiente pra provar que o stdin chegou e o stdout foi capturado certo.
write_mock_hook() {
  local path="$1"
  cat > "$path" << 'MOCKEOF'
#!/usr/bin/env bash
set -uo pipefail
python3 -c "
import json, sys
try:
    event = json.load(sys.stdin)
except Exception:
    sys.exit(0)
name = event.get('hook_event_name', 'unknown')
print(json.dumps({'hookSpecificOutput': {'hookEventName': name, 'additionalContext': 'REPLAY-SELFTEST-OK'}}))
"
MOCKEOF
}

# ---- self-test ----------------------------------------------------------------
# mock_hook/tmp_event são globais (não "local"): a trap EXIT roda no escopo do
# script inteiro, depois que selftest() já retornou — "local" as tornaria unbound
# ali sob `set -u`.
mock_hook=""
tmp_event=""
selftest() {
  # X's DEVEM ser o fim do template — o mktemp BSD/macOS (/usr/bin/mktemp) não
  # randomiza quando há sufixo literal depois do run de X (ex.: "...XXXXXX.sh"
  # sai sem substituição, arriscando colisão/"File exists" em reruns).
  mock_hook="$(mktemp "${EVAL_TMP}/replay-${SENTINEL}-hook.XXXXXX")"
  tmp_event="$(mktemp "${EVAL_TMP}/replay-${SENTINEL}-event.XXXXXX")"
  trap 'rm -f "$mock_hook" "$tmp_event"' EXIT
  write_mock_hook "$mock_hook"

  echo "replay_hook --selftest → mock hook descartável em $mock_hook"
  echo "(valida a mecânica do harness — stdin/stdout/JSON — não lógica de nenhum hook real do kit)"
  echo

  # --- Cenário 1: Stop sintético via stdin → additionalContext esperado ---
  echo "Cenário 1 — Stop sintético (stdin) → hookSpecificOutput.additionalContext"
  local ev1 out1
  ev1='{"hook_event_name":"Stop","session_id":"'"${SENTINEL}"'","transcript_path":"","stop_hook_active":false}'
  out1="$(run_hook "$mock_hook" "$ev1")"
  if printf '%s' "$out1" | python3 -c "
import sys, json
d = json.load(sys.stdin)
h = d['hookSpecificOutput']
assert h['hookEventName'] == 'Stop', h
assert h['additionalContext'] == 'REPLAY-SELFTEST-OK', h
" 2>/dev/null; then
    ok "mock hook emitiu hookSpecificOutput.additionalContext válido para Stop"
  else
    bad "saída inesperada: ${out1:-<vazia>}"
  fi

  # --- Cenário 2: evento inválido no stdin → hook não quebra, silêncio ---
  echo "Cenário 2 — stdin inválido → sem saída espúria (guard do mock)"
  local out2
  out2="$(printf '%s' 'not-json' | bash "$mock_hook" 2>/dev/null || true)"
  if [ -z "$out2" ]; then
    ok "stdin inválido não produz saída espúria"
  else
    bad "esperava silêncio, veio: $out2"
  fi

  # --- Cenário 3: dispatch genérico (arquivo de evento) exercita o CLI real ---
  echo "Cenário 3 — dispatch genérico '\$0 <hook> <evento.json>' usa o mesmo run_hook"
  printf '%s' "$ev1" > "$tmp_event"
  local out3
  out3="$(generic_replay "$mock_hook" "$tmp_event" 2>&1)"
  if printf '%s' "$out3" | grep -q "REPLAY-SELFTEST-OK" && printf '%s' "$out3" | grep -q "saída é JSON válido"; then
    ok "dispatch genérico valida o mesmo mock hook via arquivo de evento"
  else
    bad "dispatch genérico não validou como esperado: $out3"
  fi

  echo
  echo "resultado: ${PASS} pass / ${FAIL} fail"
  [ "$FAIL" -eq 0 ] || exit 1
}

# ---- dispatch -----------------------------------------------------------------
case "${1:-}" in
  --selftest) selftest ;;
  "" | -h | --help)
    echo "uso: $0 --selftest | $0 <hook.sh|nome-bare> <evento.json|->"; exit 0 ;;
  *)
    [ $# -ge 2 ] || { echo "uso: $0 <hook.sh> <evento.json|->" >&2; exit 2; }
    generic_replay "$1" "$2" ;;
esac
