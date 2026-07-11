#!/usr/bin/env bash
# desc: Post-install health check for the agent-kit plugin kit — one pass/fail/info line per check, with a one-line fix on failure.
# usage: bash scripts/doctor.sh [--maintainer]
#   (default)     colleague checks: claude CLI present, marketplace registered, plugins installed.
#   --maintainer  additionally runs kit-maintainer gates: check-ceiling.sh, check-provenance.sh,
#                 claude plugin validate ., generate_inventory.py --check.
set -uo pipefail
cd "$(dirname "$0")/.." || exit 1

MARKETPLACE="agent-kit"
REQUIRED_PLUGINS=(core)
ALL_PLUGINS=(core council team mobile)

MAINTAINER_MODE=0
for arg in "$@"; do
  case "$arg" in
    --maintainer) MAINTAINER_MODE=1 ;;
    -h|--help)
      echo "Usage: bash scripts/doctor.sh [--maintainer]"
      echo "  (default)     colleague checks: claude CLI present, marketplace registered, plugins installed"
      echo "  --maintainer  additionally run kit-maintainer repo gates (check-ceiling, check-provenance, plugin validate, inventory --check)"
      exit 0
      ;;
    *)
      echo "Unknown option: $arg" >&2
      echo "Usage: bash scripts/doctor.sh [--maintainer]" >&2
      exit 1
      ;;
  esac
done

overall_fail=0

pass() { echo "OK: $1"; }
info() { echo "INFO: $1"; }
fail() {
  echo "FAIL: $1"
  echo "  fix: $2"
  overall_fail=1
}

echo "=== agent-kit doctor ==="
echo

# 1) claude CLI present
if command -v claude >/dev/null 2>&1; then
  pass "'claude' CLI found ($(command -v claude))"
else
  fail "'claude' CLI not found on PATH" "install Claude Code, then re-run this script: https://docs.claude.com/claude-code"
  echo
  echo "Summary: FAIL (cannot run remaining checks without the 'claude' CLI)"
  exit 1
fi

# Prefer machine-readable output (claude plugin ... --json) over parsing the
# decorative TUI (the ❯ glyph and column layout are not a stable contract across
# CLI versions). Fall back to a tolerant text match — identifier as a standalone
# token, not anchored to a glyph or end-of-line — only if --json is unavailable.

# Python snippets are passed via `python3 -c` (code as an argv, not stdin) so that
# stdin stays free to carry the piped JSON — a heredoc on the same command would
# override the pipe instead of composing with it.
PY_MARKETPLACE_HAS=$(cat <<'PYEOF'
import json, sys
name = sys.argv[1]
try:
    data = json.loads(sys.stdin.read())
except Exception:
    sys.exit(2)
if not isinstance(data, list):
    sys.exit(2)
names = {str(x.get("name", "")) for x in data if isinstance(x, dict)}
sys.exit(0 if name in names else 1)
PYEOF
)

PY_PLUGIN_STATUS=$(cat <<'PYEOF'
import json, sys
target = sys.argv[1]
try:
    data = json.loads(sys.stdin.read())
except Exception:
    sys.exit(2)
if not isinstance(data, list):
    sys.exit(2)
matches = [x for x in data if isinstance(x, dict) and str(x.get("id", "")) == target]
if not matches:
    sys.exit(1)
enabled = any(bool(x.get("enabled")) for x in matches)
print("enabled" if enabled else "disabled")
sys.exit(0)
PYEOF
)

# marketplace_registered: 0 = found, 1 = not found (confirmed via json), 2 = json path unavailable/failed
marketplace_registered() {
  local json
  json="$(claude plugin marketplace list --json 2>/dev/null)" || return 2
  [ -n "$json" ] || return 2
  command -v python3 >/dev/null 2>&1 || return 2
  printf '%s' "$json" | python3 -c "$PY_MARKETPLACE_HAS" "$MARKETPLACE"
  return $?
}

# plugin_status <id>: 0 = found, 1 = not found, 2 = json path unavailable/failed.
# Sets PLUGIN_STATUS_DETAIL to "enabled"/"disabled" when found via json.
PLUGIN_STATUS_DETAIL=""
plugin_status() {
  local id="$1" json py_out py_rc
  PLUGIN_STATUS_DETAIL=""
  json="$(claude plugin list --json 2>/dev/null)" || return 2
  [ -n "$json" ] || return 2
  command -v python3 >/dev/null 2>&1 || return 2
  py_out="$(printf '%s' "$json" | python3 -c "$PY_PLUGIN_STATUS" "$id")"
  py_rc=$?
  PLUGIN_STATUS_DETAIL="$py_out"
  return "$py_rc"
}

# 2) marketplace registered
marketplace_registered
mp_rc=$?
if [ "$mp_rc" -eq 2 ]; then
  # No --json support (or python3/CLI unavailable) — tolerant text fallback:
  # match the identifier as a standalone token, not anchored to the ❯ glyph or EOL.
  marketplace_list="$(claude plugin marketplace list 2>&1)"
  if printf '%s\n' "$marketplace_list" | grep -qE '(^|[^A-Za-z0-9._-])'"${MARKETPLACE}"'([^A-Za-z0-9._-]|$)'; then
    mp_rc=0
  else
    mp_rc=1
  fi
fi
if [ "$mp_rc" -eq 0 ]; then
  pass "marketplace '${MARKETPLACE}' registered"
else
  fail "marketplace '${MARKETPLACE}' not registered" "run: bash scripts/install.sh (or: claude plugin marketplace add \"$(pwd)\")"
fi

# 3) per-plugin install status (core required, others optional by profile)
for p in "${ALL_PLUGINS[@]}"; do
  plugin_status "${p}@${MARKETPLACE}"
  p_rc=$?
  if [ "$p_rc" -eq 2 ]; then
    # No --json support — tolerant text fallback (no glyph/anchor dependency).
    # Status detail is dropped here: detection > decoration.
    plugin_list="$(claude plugin list 2>&1)"
    if printf '%s\n' "$plugin_list" | grep -qE '(^|[^A-Za-z0-9._-])'"${p}@${MARKETPLACE}"'([^A-Za-z0-9._-]|$)'; then
      p_rc=0
      PLUGIN_STATUS_DETAIL="status unknown"
    else
      p_rc=1
    fi
  fi
  if [ "$p_rc" -eq 0 ]; then
    pass "'${p}@${MARKETPLACE}' installed (${PLUGIN_STATUS_DETAIL:-status unknown})"
  else
    is_required=0
    for r in "${REQUIRED_PLUGINS[@]}"; do
      [ "$r" = "$p" ] && is_required=1
    done
    if [ "$is_required" -eq 1 ]; then
      fail "'${p}@${MARKETPLACE}' not installed (required)" "run: claude plugin install ${p}@${MARKETPLACE} (or: bash scripts/install.sh)"
    else
      info "'${p}@${MARKETPLACE}' not installed (optional — only needed for its profile; install with: claude plugin install ${p}@${MARKETPLACE})"
    fi
  fi
done

echo

# 4) repo self-checks (kit-maintainer gates only — not colleague-facing:
# provenance/ceiling failures aren't fixable by someone who just installed the kit).
if [ "$MAINTAINER_MODE" -ne 1 ]; then
  info "maintainer checks skipped (repo self-checks) — run with --maintainer to include them"
  echo
  if [ "$overall_fail" -eq 0 ]; then
    echo "Summary: all colleague checks passed."
  else
    echo "Summary: one or more colleague checks FAILED — see above."
  fi
  exit "$overall_fail"
fi

# repo self-checks — run from repo root, only if the corresponding file exists
if [ -f scripts/check-ceiling.sh ]; then
  if out="$(bash scripts/check-ceiling.sh 2>&1)"; then
    pass "scripts/check-ceiling.sh"
  else
    fail "scripts/check-ceiling.sh" "run 'bash scripts/check-ceiling.sh' directly and read its ERROR line"
    printf '%s\n' "$out" | sed 's/^/    /'
  fi
else
  info "scripts/check-ceiling.sh not found — skipped"
fi

if [ -f scripts/check-provenance.sh ]; then
  if out="$(bash scripts/check-provenance.sh 2>&1)"; then
    pass "scripts/check-provenance.sh"
  else
    fail "scripts/check-provenance.sh" "run 'bash scripts/check-provenance.sh' directly and read its ERROR/FAILED line"
    printf '%s\n' "$out" | sed 's/^/    /'
  fi
else
  info "scripts/check-provenance.sh not found — skipped"
fi

if out="$(claude plugin validate . 2>&1)"; then
  pass "claude plugin validate . (marketplace manifest)"
else
  fail "claude plugin validate ." "run 'claude plugin validate .' directly and read its error"
  printf '%s\n' "$out" | sed 's/^/    /'
fi

if [ -f scripts/generate_inventory.py ]; then
  if grep -q -- '--check' scripts/generate_inventory.py; then
    if out="$(python3 scripts/generate_inventory.py --check 2>&1)"; then
      pass "INVENTORY.md up to date"
    else
      fail "INVENTORY.md out of date" "run: python3 scripts/generate_inventory.py"
      printf '%s\n' "$out" | sed 's/^/    /'
    fi
  else
    info "scripts/generate_inventory.py has no --check mode — skipped"
  fi
else
  info "scripts/generate_inventory.py not found — skipped"
fi

if [ -f evals/run-evals.sh ]; then
  if out="$(bash evals/run-evals.sh 2>&1)"; then
    pass "evals/run-evals.sh (tier-1 hook evals)"
  else
    fail "evals/run-evals.sh" "run 'bash evals/run-evals.sh' directly and read the failing case"
    printf '%s\n' "$out" | sed 's/^/    /'
  fi
else
  info "evals/run-evals.sh not found — skipped"
fi

echo
if [ "$overall_fail" -eq 0 ]; then
  echo "Summary: all checks passed (colleague + maintainer)."
else
  echo "Summary: one or more checks FAILED — see above."
fi
exit "$overall_fail"
