#!/usr/bin/env bash
# desc: SessionStart — injects the body of using-agent-kit as always-on context and persists the session model for model-routing.sh.
#
# Two independent concerns share this hook because SessionStart is the only event that
# sees both cleanly. (1) The skill-body injection below MUST fail loud if the SKILL.md is
# missing — a broken always-on tier is worse silent than noisy — so `set -e` plus the
# unguarded `open()` in the final python block is intentional and unchanged from before
# this hook grew the second concern below. (2) The session-model state write is a
# best-effort addition and must NEVER cause (1) to fail: absent stdin, malformed JSON, or
# a state-dir write failure each degrade to silence, never an error.
#
# Session-model state: SessionStart's stdin JSON may carry `model`/`session_id` (both
# optional — absent on older Claude Code builds, or when the field names drift). Written
# to STATE_DIR/session-model-<session_id> (mirrors read-ledger.sh's state-dir convention)
# for model-routing.sh (PreToolUse) to read later. Missing either field, malformed JSON,
# or a write failure -> skip silently, never touch the exit code.

set -euo pipefail

# Guarded read: this hook never used to touch stdin. `cat` on a closed/empty stdin exits
# 0 with empty output (fine under -e); the `|| true` is defense in depth so a stdin read
# can never be the thing that breaks the context injection below.
INPUT_JSON="$(cat 2>/dev/null || true)"
export INPUT_JSON

STATE_DIR="${CLAUDE_PLUGIN_DATA:-${TMPDIR:-/tmp}/agent-kit-core}/state"
export STATE_DIR

# Best-effort session-model persistence for model-routing.sh. Self-contained: every path
# through the python below ends in an explicit sys.exit(0) or a caught exception, so it
# cannot propagate a failure into this script's `set -e`; the trailing `|| true` is belt
# and suspenders against anything unforeseen (e.g. python3 vanishing mid-run).
if command -v python3 &>/dev/null; then
    python3 << 'PYEOF' || true
import json, os, sys

try:
    data = json.loads(os.environ.get("INPUT_JSON", "") or "{}")
except Exception:
    sys.exit(0)

if not isinstance(data, dict):
    sys.exit(0)

model = data.get("model")
session_id = data.get("session_id")
if not isinstance(model, str) or not model or not isinstance(session_id, str) or not session_id:
    sys.exit(0)

state_dir = os.environ.get("STATE_DIR", "")
try:
    os.makedirs(state_dir, exist_ok=True)
    with open(os.path.join(state_dir, f"session-model-{session_id}"), "w", encoding="utf-8") as f:
        f.write(model)
except Exception:
    pass  # a write failure here never blocks the context injection below
sys.exit(0)
PYEOF
fi

python3 - "${CLAUDE_PLUGIN_ROOT}/skills/using-agent-kit/SKILL.md" << 'PY'
import json, sys

body = open(sys.argv[1], encoding="utf-8").read()

print(json.dumps({"hookSpecificOutput": {
    "hookEventName": "SessionStart",
    "additionalContext": "<agent-kit-core>\n" + body + "\n</agent-kit-core>\n"}}))
PY
