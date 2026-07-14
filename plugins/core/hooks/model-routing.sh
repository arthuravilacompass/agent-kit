#!/usr/bin/env bash
# desc: PreToolUse(Edit|Write|MultiEdit) — advisory: the session model (persisted by session-start.sh) is a synthesis-tier model (e.g. Fable) writing a code artifact directly; house model strategy routes code/fix/eval work to a Sonnet subagent; non-blocking (exit 0 + additionalContext), once per session.
#
# Self-enforcement for the operator's model strategy (his CLAUDE.md: Fable is the session
# default for synthesis/decisions, Sonnet/Opus SUBAGENTS execute code). Observed failure
# mode: the session model writes hooks/evals/code inline instead of delegating. PreToolUse
# exit 2 would BLOCK the edit — too strong for a strategy preference, not a correctness
# gate — so this hook always exits 0 and, when it has something to say, rides
# hookSpecificOutput.additionalContext instead (advisory, never blocks the edit).
#
# Failure modes, documented (fails toward silence in every case):
#   (1) no python3 -> exit 0.
#   (2) no persisted session-model state file (session started before this shipped, the
#       model field was absent from SessionStart's stdin, or session_id is absent from
#       this hook's own payload) -> silent.
#   (3) malformed JSON, on either this hook's stdin or a corrupted state file -> silent.
#   (4) marker-dir write failure never suppresses the advisory itself (same contract as
#       posture-signal / codegen-staleness).

set -uo pipefail

if ! command -v python3 &>/dev/null; then
    exit 0
fi

INPUT_JSON=$(cat)
export INPUT_JSON

STATE_DIR="${CLAUDE_PLUGIN_DATA:-${TMPDIR:-/tmp}/agent-kit-core}/state"
export STATE_DIR

MARKER_DIR="${CLAUDE_PLUGIN_DATA:-${TMPDIR:-/tmp}/agent-kit-core}/model-routing"
export MARKER_DIR

python3 << 'PYEOF'
import hashlib, json, os, sys


def main(data):
    tool_input = data.get("tool_input", {}) or {}
    file_path = tool_input.get("file_path", "")
    if not isinstance(file_path, str) or not file_path:
        return

    # Code-artifact filter: extensions the house strategy treats as "code, not prose" —
    # .md, /memory/, /docs/ are explicitly excluded (synthesis writing docs/memory isn't
    # the failure mode this hook polices).
    CODE_EXTS = (".sh", ".py", ".dart", ".js", ".ts", ".json", ".jsonl", ".yaml", ".yml")
    if "/memory/" in file_path or "/docs/" in file_path:
        return
    if not any(file_path.endswith(ext) for ext in CODE_EXTS):
        return

    session_id = data.get("session_id")
    if not isinstance(session_id, str) or not session_id:
        return

    state_dir = os.environ.get("STATE_DIR", "")
    try:
        with open(os.path.join(state_dir, f"session-model-{session_id}"), encoding="utf-8") as f:
            model = f.read().strip()
    except Exception:
        return
    if not model:
        return

    # Synthesis-tier model-name fragments (house strategy: Fable is the session default
    # for synthesis/decisions; code execution belongs to a Sonnet/Opus subagent) — extend
    # this tuple as the tier list grows.
    SYNTHESIS_TIER_MARKERS = ("fable",)
    if not any(marker in model.lower() for marker in SYNTHESIS_TIER_MARKERS):
        return

    # Once per session — marker keyed by session_id only (one advisory message, not one
    # per file), mirroring posture-signal's session-keyed marker mechanics.
    marker_dir = os.environ.get("MARKER_DIR", "")
    marker = os.path.join(marker_dir, hashlib.sha1(session_id.encode()).hexdigest())
    if marker_dir and os.path.exists(marker):
        return
    if marker_dir:
        try:
            os.makedirs(marker_dir, exist_ok=True)
            open(marker, "w").close()
        except Exception:
            pass  # marker failure never suppresses the advisory itself

    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "additionalContext": (
                "[model-routing] session model is a synthesis-tier model writing a "
                "code artifact directly - house model strategy routes code/fix/eval "
                "work to a Sonnet subagent. Advisory, once per session."
            ),
        }
    }))


# Broad exception guard: fails toward silence, never a noisy exit-1 traceback on every
# Edit/Write/MultiEdit (mirrors posture-signal's top-level guard).
try:
    data = json.loads(os.environ.get("INPUT_JSON", "{}"))
    if isinstance(data, dict):
        main(data)
except Exception:
    pass

sys.exit(0)
PYEOF

# Always exit 0 regardless of the subshell's own exit code — PreToolUse exit 2 would
# BLOCK the edit, which this hook must never do (advisory-only contract).
exit 0
