#!/usr/bin/env bash
# run-evals.sh — Tier 1 (determinístico) da suíte de evals do agent-kit.
# Lê evals/cases/hook-cases.jsonl, roda cada hook real do kit (plugins/core/hooks/)
# com o payload sintético e confere: exit code, presença/ausência de substring no
# stdout e, quando aplicável, side-effects em disco (hooks silenciosos como
# read-ledger só são observáveis pelo que gravam em STATE_DIR, não pelo stdout).
#
# Correção 1 (fixtures nunca /tmp hardcoded): todo path de fixture deriva de
# $TMPDIR, com fallback pra <repo>/.eval-tmp se TMPDIR não estiver setado — hoje o
# harness quebraria sob sandbox que restringe write a um diretório específico.
#
# Placeholders no JSONL, substituídos por texto ANTES do parse JSON de cada linha
# (permite paths portáveis entre máquinas/CI sem hardcode):
#   {{TMPDIR}}     → raiz de fixtures desta run (ver EVAL_TMP abaixo)
#   {{REPO_ROOT}}  → raiz deste repo (casos que precisam de CLAUDE_PLUGIN_ROOT real)
#
# Schema de um caso (1 JSON por linha; linhas em branco/`#...` são ignoradas):
#   desc                       (obrigatório) descrição humana do caso
#   hook                       (obrigatório) path do hook relativo à raiz do repo
#   input                      (obrigatório) payload JSON injetado no stdin do hook
#   expect_exit                (obrigatório) exit code esperado
#   env                        (opcional) dict de env vars pra essa invocação
#   expect_contains            (opcional) substring que DEVE aparecer no stdout
#   expect_not_contains        (opcional) substring que NÃO PODE aparecer no stdout
#   expect_side_file           (opcional) path que DEVE existir após rodar o hook
#   expect_side_file_contains  (opcional, usa junto com expect_side_file) substring
#                              que o side file deve conter
#   expect_side_file_missing   (opcional) path que NÃO PODE existir após rodar o hook
#
# Uso: ./evals/run-evals.sh   → exit 0 = tudo verde; exit 1 = alguma falha.
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
CASES="$SCRIPT_DIR/cases/hook-cases.jsonl"

if [[ ! -f "$CASES" ]]; then
  echo "ERRO: $CASES não encontrado" >&2
  exit 1
fi

if ! command -v python3 &>/dev/null; then
  echo "ERRO: python3 necessário" >&2
  exit 1
fi

# ---------------------------------------------------------------------------
# $TMPDIR fix (correção 1): nunca /tmp hardcoded. Fallback repo-local se TMPDIR
# não estiver setado.
# ---------------------------------------------------------------------------
EVAL_TMP="${TMPDIR:-$REPO_ROOT/.eval-tmp}"
EVAL_TMP="${EVAL_TMP%/}"          # TMPDIR no macOS costuma vir com "/" final
EVAL_ROOT="$EVAL_TMP/agent-kit-evals"
rm -rf "$EVAL_ROOT"               # cada run parte do zero — elimina markers/estado de sessão anterior
mkdir -p "$EVAL_ROOT"

# ---------------------------------------------------------------------------
# Fixtures: filesystem de apoio para os casos que precisam (plan-autoload lê
# docs/).
# ---------------------------------------------------------------------------
TODAY="$(date +%Y-%m-%d)"
OLD_STAMP="$(date -v-100H +%Y%m%d%H%M 2>/dev/null || date -d '100 hours ago' +%Y%m%d%H%M)"

# plan-autoload: plano recente (<72h, happy) e plano com mtime velho (>72h, edge)
mkdir -p "$EVAL_ROOT/plan-autoload-happy/docs/superpowers/plans"
echo "# plano de teste" > "$EVAL_ROOT/plan-autoload-happy/docs/superpowers/plans/${TODAY}-eval-test-plan.md"

mkdir -p "$EVAL_ROOT/plan-autoload-stale/docs/superpowers/plans"
STALE_PLAN="$EVAL_ROOT/plan-autoload-stale/docs/superpowers/plans/${TODAY}-eval-old-plan.md"
echo "# plano velho" > "$STALE_PLAN"
touch -t "$OLD_STAMP" "$STALE_PLAN"

# bash-autoapprove-readonly / claude-dir-guard: asserções são só sobre a string
# do comando — não precisam de fixture em disco.
# session-start: aponta CLAUDE_PLUGIN_ROOT pro plugin real (plugins/core) no caso
# happy; no edge aponta pra um path que não existe — sem fixture a criar.

PASS=0
FAIL=0
LINE_NO=0

while IFS= read -r raw_line; do
  LINE_NO=$((LINE_NO + 1))
  [[ -z "$raw_line" || "$raw_line" == \#* ]] && continue

  # Substituição de placeholders ANTES do parse JSON.
  line="${raw_line//\{\{TMPDIR\}\}/$EVAL_TMP}"
  line="${line//\{\{REPO_ROOT\}\}/$REPO_ROOT}"

  desc=$(python3 -c "import json,sys; print(json.loads(sys.argv[1])['desc'])" "$line")
  hook=$(python3 -c "import json,sys; print(json.loads(sys.argv[1])['hook'])" "$line")
  expect=$(python3 -c "import json,sys; print(json.loads(sys.argv[1])['expect_exit'])" "$line")
  contains=$(python3 -c "import json,sys; print(json.loads(sys.argv[1]).get('expect_contains',''))" "$line")
  not_contains=$(python3 -c "import json,sys; print(json.loads(sys.argv[1]).get('expect_not_contains',''))" "$line")
  side_file=$(python3 -c "import json,sys; print(json.loads(sys.argv[1]).get('expect_side_file',''))" "$line")
  side_needle=$(python3 -c "import json,sys; print(json.loads(sys.argv[1]).get('expect_side_file_contains',''))" "$line")
  side_missing=$(python3 -c "import json,sys; print(json.loads(sys.argv[1]).get('expect_side_file_missing',''))" "$line")
  env_json=$(python3 -c "import json,sys; d=json.loads(sys.argv[1]); print(json.dumps(d['env']) if 'env' in d else '')" "$line")
  payload=$(python3 -c "import json,sys; print(json.dumps(json.loads(sys.argv[1])['input']))" "$line")

  # Env override per-case (não global): parseia campo "env" do JSON e injeta
  # apenas na invocação deste caso.
  env_args=()
  if [[ -n "$env_json" ]]; then
    while IFS= read -r pair; do
      [[ -n "$pair" ]] && env_args+=("$pair")
    done < <(python3 -c "import json,sys; d=json.loads(sys.argv[1]); [print(f'{k}={v}') for k,v in d.items()]" "$env_json")
  fi

  hook_path="$REPO_ROOT/$hook"
  if [[ ! -f "$hook_path" ]]; then
    FAIL=$((FAIL + 1))
    echo "  ✗ $desc (hook não encontrado: $hook_path)"
    continue
  fi

  if [[ ${#env_args[@]} -gt 0 ]]; then
    out=$(echo "$payload" | env "${env_args[@]}" bash "$hook_path" 2>/dev/null)
  else
    out=$(echo "$payload" | bash "$hook_path" 2>/dev/null)
  fi
  actual=$?

  ok=1
  [[ "$actual" != "$expect" ]] && ok=0
  if [[ -n "$contains" ]] && ! echo "$out" | grep -qF "$contains"; then
    ok=0
  fi
  if [[ -n "$not_contains" ]] && echo "$out" | grep -qF "$not_contains"; then
    ok=0
  fi
  if [[ -n "$side_file" ]]; then
    if [[ ! -f "$side_file" ]]; then
      ok=0
    elif [[ -n "$side_needle" ]] && ! grep -qF "$side_needle" "$side_file"; then
      ok=0
    fi
  fi
  if [[ -n "$side_missing" && -e "$side_missing" ]]; then
    ok=0
  fi

  if [[ $ok -eq 1 ]]; then
    PASS=$((PASS + 1))
    echo "  ✓ $desc"
  else
    FAIL=$((FAIL + 1))
    echo "  ✗ $desc (exit esperado=$expect, obtido=$actual; out=$(echo "$out" | head -c 120))"
  fi
done < "$CASES"

echo ""
echo "Evals tier-1: $PASS passou, $FAIL falhou."
[[ $FAIL -eq 0 ]] || exit 1
exit 0
