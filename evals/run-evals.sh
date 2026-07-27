#!/usr/bin/env bash
# run-evals.sh — Tier 1 (determinístico) da suíte de evals do agent-kit.
# Lê evals/cases/hook-cases.jsonl, roda cada hook real do kit (plugins/core/hooks/)
# com o payload sintético e confere: exit code, presença/ausência de substring na
# saída combinada (stdout+stderr) e, quando aplicável, side-effects em disco
# (hooks silenciosos como read-ledger só são observáveis pelo que gravam em
# STATE_DIR, não pela saída).
#
# Correção 1 (fixtures nunca /tmp hardcoded): todo path de fixture deriva de
# $TMPDIR, com fallback pra <repo>/.eval-tmp se TMPDIR não estiver setado — hoje o
# harness quebraria sob sandbox que restringe write a um diretório específico.
#
# Correção 2 (stderr entra na captura, e os canais ficam SEPARADOS): a captura
# original usava `2>/dev/null`, descartando stderr; expect_contains contra uma
# mensagem de stderr nunca batia. A correção seguinte trocou pra `2>&1`, o que
# resolveu aquilo e criou um defeito pior: com os canais fundidos, um caso não
# conseguia distinguir "o hook escreveu em stderr" de "o modelo recebeu". Os dois
# não são a mesma coisa — stderr de um hook que sai com 0 NÃO chega ao modelo
# (só ao transcript); só chega via hookSpecificOutput.additionalContext em stdout,
# ou via stderr quando o exit é 2. Quatro casos de fail-open do citation-check
# ficaram verdes enquanto o aviso era invisível pro leitor a quem ele se dirigia.
# Agora stdout e stderr são capturados separadamente; expect_contains /
# expect_not_contains seguem valendo sobre a união (compatibilidade com os casos
# existentes), e expect_stdout_contains / expect_stderr_contains permitem afirmar
# QUAL canal carregou a mensagem — que é o que um caso de fail-open precisa dizer.
#
# Nota (não-concorrência, 2026-07-13): este harness NÃO é concurrency-safe —
# EVAL_ROOT é um path fixo compartilhado, apagado com `rm -rf` no início de cada
# run; runs concorrentes se pisam e matam silenciosamente fixtures/markers uns
# dos outros (reproduzido: pares concorrentes falham 0-7 casos com assinatura de
# saída vazia; runs seriais dão 100% verde). Rode sempre serialmente.
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
#   expect_contains            (opcional) substring que DEVE aparecer na saída (stdout+stderr)
#   expect_not_contains        (opcional) substring que NÃO PODE aparecer na saída (stdout+stderr)
#   expect_stdout_contains     (opcional) substring que DEVE aparecer em stdout SOMENTE —
#                              o canal model-visible de um hook que sai com 0 (envelope
#                              hookSpecificOutput.additionalContext). Use isto, não
#                              expect_contains, pra qualquer aviso que precise CHEGAR ao
#                              modelo: expect_contains passa igual se a mensagem sair por
#                              stderr, que num exit 0 o modelo nunca vê.
#   expect_stderr_contains     (opcional) substring que DEVE aparecer em stderr SOMENTE —
#                              o canal do relatório de bloqueio (exit 2), o único exit em
#                              que o Claude Code realimenta stderr pro modelo.
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
# Fixtures: nenhum hook restante precisa de filesystem de apoio pré-criado.
# session-start: aponta CLAUDE_PLUGIN_ROOT pro plugin real (plugins/core) no caso
# happy; no edge aponta pra um path que não existe — sem fixture a criar.
# ---------------------------------------------------------------------------

# model-routing fixtures (2026-07-13): session-model state files pré-criados
# (mirroram o contrato de escrita de session-start.sh) — um por sessão de teste, pra
# isolar "silencia por extensão .md" de "silencia por marker" sem ambiguidade.
MR_STATE="$EVAL_ROOT/model-routing-data/state"
mkdir -p "$MR_STATE"
printf "claude-fable-5" > "$MR_STATE/session-model-eval-mr-fable"
printf "claude-sonnet-5" > "$MR_STATE/session-model-eval-mr-sonnet"
printf "claude-fable-5" > "$MR_STATE/session-model-eval-mr-fable-md"

# codegen-staleness fixtures: a fake module with one stale and one fresh generated file
CG="$EVAL_ROOT/codegen-fixture/lib"
mkdir -p "$CG"
printf "part 'stale_store.g.dart';\nclass StaleStore {}\n" > "$CG/stale_store.dart"
printf "// generated\n" > "$CG/stale_store.g.dart"
touch -t 202001010000 "$CG/stale_store.g.dart"          # generated far older than source
printf "part 'fresh_store.g.dart';\nclass FreshStore {}\n" > "$CG/fresh_store.dart"
touch -t 202001010000 "$CG/fresh_store.dart"            # source older than generated
printf "// generated\n" > "$CG/fresh_store.g.dart"
printf "final int x = 1;\n" > "$CG/plain.dart"

# lifecycle-check fixtures
LC="$EVAL_ROOT/lifecycle-fixture/lib"
mkdir -p "$LC"
printf "class S {\n  int x = 1;\n}\n" > "$LC/no_dispose_store.dart"
printf "class S {\n  int x = 1;\n  void dispose() {}\n}\n" > "$LC/has_dispose_store.dart"

# di-mismatch fixtures: fake project with an injection.config.dart mentioning OldService only
DI="$EVAL_ROOT/di-fixture/lib"
mkdir -p "$DI"
printf "class NewService {\n  int x = 1;\n}\n" > "$DI/new_service.dart"
printf "class OldService {\n  int x = 1;\n}\n" > "$DI/old_service.dart"
printf "// GENERATED\ngh.factory<OldService>(() => OldService());\n" > "$DI/injection.config.dart"

# citation-check fixtures (fix round 1, 2026-07-27): a real read-ledger for "cc-real-session"
# (covers some/fake/verified.dart:10-20, NOT some/fake/bar.dart — the fixtures at
# evals/fixtures/citation-check/agent-kit-findings/{fabricated,verified}.findings.json cite
# bar.dart and verified.dart
# respectively), a NEWER "decoy" ledger for a different session that WOULD wrongly cover
# bar.dart if auto-discovery ever grabbed it instead of the session actually passed via
# --session, and an empty ledger for "cc-empty-ledger-session".
#
# ALL THREE mtimes are pinned with `touch -t`, and the empty one is pinned OLDEST on
# purpose. Pinning only two of them (the first version of these fixtures) left the empty
# ledger carrying its run-time mtime, which made IT — not the decoy — the most recent file
# in this dir. discover_ledger()'s "most recent" fallback then picked an empty ledger, so
# dropping --session from the hook still produced "unverified", and the decoy never got
# exercised: the mutation that deletes the --session pass-through survived the suite while
# the comment above claimed the decoy was newer. Verified by mutation testing, fix round 1.
CC_STATE="$EVAL_ROOT/citation-check-data/state"
mkdir -p "$CC_STATE"
printf '{"file":"some/fake/verified.dart","start":10,"end":20,"tool":"Read","ts":1}\n' \
  > "$CC_STATE/read-ledger-cc-real-session.jsonl"
touch -t 202001010000 "$CC_STATE/read-ledger-cc-real-session.jsonl"
printf '{"file":"some/fake/bar.dart","start":1,"end":100,"tool":"Read","ts":1}\n' \
  > "$CC_STATE/read-ledger-cc-decoy-session.jsonl"
touch -t 202301010000 "$CC_STATE/read-ledger-cc-decoy-session.jsonl"
: > "$CC_STATE/read-ledger-cc-empty-ledger-session.jsonl"
touch -t 201901010000 "$CC_STATE/read-ledger-cc-empty-ledger-session.jsonl"

# Fix round 3 (2026-07-27): the hook matches the CONTAINING DIRECTORY (parent component
# == agent-kit-findings), not the basename alone. This fixture is a directory whose name
# merely CONTAINS that string — the bash pre-filter is a substring test and lets it
# through, python's parent-component test is an equality and must not. The file has to
# EXIST and carry gate-tripping content, or the case would come back exit 0 through the
# isfile guard and pin nothing whichever way python's test was written.
CC_NEARMISS="$EVAL_ROOT/agent-kit-findings-backup"
mkdir -p "$CC_NEARMISS"
cp "$REPO_ROOT/evals/fixtures/citation-check/agent-kit-findings/fabricated.findings.json" \
   "$CC_NEARMISS/fabricated.findings.json"

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
  stdout_contains=$(python3 -c "import json,sys; print(json.loads(sys.argv[1]).get('expect_stdout_contains',''))" "$line")
  stderr_contains=$(python3 -c "import json,sys; print(json.loads(sys.argv[1]).get('expect_stderr_contains',''))" "$line")
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

  # Canais separados (ver "Correção 2" no cabeçalho): stderr num arquivo por caso,
  # nunca fundido com stdout na captura. `out` = stdout puro, `err` = stderr puro,
  # `both` = a união, só pra manter expect_contains/expect_not_contains como estavam.
  ERR_FILE="$EVAL_ROOT/.case-stderr"
  if [[ ${#env_args[@]} -gt 0 ]]; then
    out=$(echo "$payload" | env "${env_args[@]}" bash "$hook_path" 2>"$ERR_FILE")
  else
    out=$(echo "$payload" | bash "$hook_path" 2>"$ERR_FILE")
  fi
  actual=$?
  err=$(cat "$ERR_FILE" 2>/dev/null)
  both="$out
$err"

  ok=1
  [[ "$actual" != "$expect" ]] && ok=0
  if [[ -n "$contains" ]] && ! echo "$both" | grep -qF "$contains"; then
    ok=0
  fi
  if [[ -n "$not_contains" ]] && echo "$both" | grep -qF "$not_contains"; then
    ok=0
  fi
  if [[ -n "$stdout_contains" ]] && ! echo "$out" | grep -qF "$stdout_contains"; then
    ok=0
  fi
  if [[ -n "$stderr_contains" ]] && ! echo "$err" | grep -qF "$stderr_contains"; then
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
    echo "  ✗ $desc (exit esperado=$expect, obtido=$actual; stdout=$(echo "$out" | head -c 100); stderr=$(echo "$err" | head -c 100))"
  fi
done < "$CASES"

echo ""
echo "Evals tier-1: $PASS passou, $FAIL falhou."
[[ $FAIL -eq 0 ]] || exit 1
exit 0
