#!/usr/bin/env bash
set -euo pipefail
python3 - "${CLAUDE_PLUGIN_ROOT}/skills/using-agent-kit/SKILL.md" <<'PY'
import json, sys
body = open(sys.argv[1], encoding="utf-8").read()
print(json.dumps({"hookSpecificOutput": {
    "hookEventName": "SessionStart",
    "additionalContext": "<agent-kit-core>\n" + body + "\n</agent-kit-core>"}}))
PY
