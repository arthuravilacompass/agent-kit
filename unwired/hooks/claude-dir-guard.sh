#!/usr/bin/env bash
# desc: PreToolUse(Bash) — blocks rm commands that touch .claude/.
# claude-dir-guard.sh — PreToolUse(Bash) hook
# Blocks `rm` commands whose command string also touches a `.claude` path segment —
# extracted from an inline PreToolUse command into its own script. Protects .claude/
# (project or user level) from accidental/agentic deletion; the developer can still
# run the command directly from a terminal if genuinely intentional.
#
# Fail-open on any parse error (never blocks by mistake — this hook only ever emits
# exit 0 or a deny with exit 2, never a false "allow").

set -uo pipefail

INPUT_JSON=$(cat)
export INPUT_JSON

python3 <<'PY'
import json, os, re, sys

try:
    data = json.loads(os.environ.get("INPUT_JSON", "{}"))
    cmd = (data.get("tool_input", {}) or {}).get("command", "") or ""
except Exception:
    cmd = ""

if re.search(r"\brm\b", cmd) and re.search(r"\.claude", cmd):
    print("BLOCK: rm + .claude detected — run from terminal directly if intentional", file=sys.stderr)
    sys.exit(2)
sys.exit(0)
PY
