#!/usr/bin/env bash
# desc: PostToolUse(Bash) — warns when the session transcript grows past a threshold.
# context-monitor.sh — PostToolUse hook
# Monitors transcript size as proxy for context window usage.
# Warns once per threshold level per session (debounced via state file).
# No native API for context % exists — transcript file size is the best proxy.

set -euo pipefail

if ! command -v python3 &>/dev/null; then
    echo '{}'
    exit 0
fi

INPUT_JSON=$(cat)

SESSION_ID=$(python3 -c "
import json, sys
try:
    data = json.loads(sys.stdin.read())
    print(data.get('session_id', 'unknown'))
except Exception:
    print('unknown')
" <<< "$INPUT_JSON" 2>/dev/null || echo "unknown")

TRANSCRIPT_PATH=$(python3 -c "
import json, sys
try:
    data = json.loads(sys.stdin.read())
    print(data.get('transcript_path', ''))
except Exception:
    print('')
" <<< "$INPUT_JSON" 2>/dev/null || echo "")

if [ -z "$TRANSCRIPT_PATH" ] || [ ! -f "$TRANSCRIPT_PATH" ]; then
    echo '{}'
    exit 0
fi

# Hook's persistent state — never a workspace path, never ${HOME}/.claude directly.
# CLAUDE_PLUGIN_DATA survives plugin updates; the fallback is only for standalone invocation
# (outside Claude Code's hook process, e.g. a manual smoke test).
STATE_DIR="${CLAUDE_PLUGIN_DATA:-${TMPDIR:-/tmp}/agent-kit-core}/state"
mkdir -p "$STATE_DIR"

export TRANSCRIPT_PATH
export SESSION_ID
export STATE_DIR

python3 << 'PYEOF'
import json, os, sys

transcript = os.environ.get("TRANSCRIPT_PATH", "")
session_id = os.environ.get("SESSION_ID", "unknown")
state_dir  = os.environ.get("STATE_DIR", "")

if not transcript or not os.path.isfile(transcript):
    print("{}")
    sys.exit(0)

size_bytes = os.path.getsize(transcript)

# Thresholds — calibrate based on observed session sizes
LEVELS = [
    (1_200_000, "critical", "[context-monitor] CRITICAL: transcript at {kb}KB. WRITE a handoff NOW to docs/superpowers/handoffs/<YYYY-MM-DD>-<task>.md (current task, decisions made, next steps, files touched), then run /compact — plan-autoload resurfaces this handoff next session."),
    (  800_000, "alert",    "[context-monitor] WARNING: transcript at {kb}KB. Before /compact, write a handoff to docs/superpowers/handoffs/<YYYY-MM-DD>-<task>.md (current state + next steps + files touched) — plan-autoload reads it next session."),
    (  500_000, "warn",     "[context-monitor] Context growing ({kb}KB). Plan a /compact soon."),
]

matched_level = None
matched_msg   = None

for threshold, level, template in LEVELS:
    if size_bytes >= threshold:
        matched_level = level
        matched_msg   = template.format(kb=size_bytes // 1000)
        break

if not matched_level:
    print("{}")
    sys.exit(0)

# Debounce: only warn once per level per session
marker = os.path.join(state_dir, f"ctx-warned-{session_id}-{matched_level}")
if os.path.exists(marker):
    print("{}")
    sys.exit(0)

# Write marker so this level won't fire again this session
try:
    with open(marker, "w") as f:
        f.write(matched_level)
except Exception:
    pass  # Never block on state write failure

print(json.dumps({"additionalContext": matched_msg}))
PYEOF

exit 0
