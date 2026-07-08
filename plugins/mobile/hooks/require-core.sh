#!/usr/bin/env bash
# desc: SessionStart — warns if core@agent-kit is not registered as installed among the plugins (checks installation, not per-session enablement; fails open on any anomaly).
set -uo pipefail
command -v python3 >/dev/null 2>&1 || exit 0
REG="${CLAUDE_CONFIG_DIR:-$HOME/.claude}/plugins/installed_plugins.json"
[ -f "$REG" ] || exit 0
python3 - "$REG" "${CLAUDE_PLUGIN_ROOT:-}" <<'PY'
import json, sys

# Documented limitation: the registry says what's INSTALLED (any scope),
# not what's enabled in this session. A project-scoped entry from another
# project counts as present (accepted false-silence; a false warning is worse —
# see the advisory-nudge meta-principle in docs/GOVERNANCE.md). Registry format is
# an internal Claude Code contract ("version": 2 today) — any unexpected shape = silence.
try:
    with open(sys.argv[1], encoding="utf-8") as f:
        entries = json.load(f).get("plugins", {}).get("core@agent-kit") or []
except Exception:
    sys.exit(0)
if entries:
    sys.exit(0)

plugin = "this plugin"
try:
    with open(sys.argv[2] + "/.claude-plugin/plugin.json", encoding="utf-8") as f:
        plugin = json.load(f).get("name", plugin)
except Exception:
    pass

print(json.dumps({"hookSpecificOutput": {"hookEventName": "SessionStart",
    "additionalContext": (
        f"[require-core] Plugin '{plugin}' assumes the always-on rules and the "
        "core@agent-kit pipeline, which is not registered as installed. Install with: "
        "claude plugin install core@agent-kit"
    )}}))
PY
