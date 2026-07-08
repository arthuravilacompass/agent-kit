#!/usr/bin/env bash
# desc: PostToolUse(Edit|Write) — background pub get for an edited pubspec.yaml; test reminder for an edited _test.dart, once per session.
# package-feedback.sh — PostToolUse Edit|Write|MultiEdit hook
# Fast rungs of the feedback ladder for a couple of file kinds a Flutter/Dart
# multi-package workspace touches often:
#   1. pubspec.yaml edited → fires `flutter pub get` in the BACKGROUND for the
#      touched package (never blocks the turn) and reports via additionalContext.
#   2. *_test.dart edited → injects a reminder to run that file's test (once per
#      file per session). Running the test inside the hook itself would blow the
#      hook timeout (~30-60s).
# Full `flutter analyze` does NOT run here — infeasible inside a hook's timeout;
# it belongs in a pre-commit hook or a review skill's precondition instead.

set -uo pipefail

if ! command -v python3 &>/dev/null; then
    echo '{}'
    exit 0
fi

INPUT_JSON=$(cat)
export INPUT_JSON

# Persistent state — never a workspace path, never ${HOME}/.claude directly.
STATE_DIR="${CLAUDE_PLUGIN_DATA:-${TMPDIR:-/tmp}/agent-kit-mobile}/state"
export STATE_DIR

RESULT=$(python3 << 'PYEOF'
import hashlib, json, os, sys

try:
    data = json.loads(os.environ.get("INPUT_JSON", "{}"))
except Exception:
    print("NOOP"); sys.exit(0)

tool_input = data.get("tool_input", {}) or {}
file_path = tool_input.get("file_path", "")
session_id = data.get("session_id", "unknown")

if not file_path:
    print("NOOP"); sys.exit(0)

# pubspec.yaml (ignore .lock and backups)
if os.path.basename(file_path) == "pubspec.yaml" and ".backup" not in file_path:
    print(f"PUBGET|{os.path.dirname(file_path)}")
    sys.exit(0)

# *_test.dart — reminder once per file per session
if file_path.endswith("_test.dart"):
    state_dir = os.environ.get("STATE_DIR", "")
    try:
        os.makedirs(state_dir, exist_ok=True)
    except Exception:
        print("NOOP"); sys.exit(0)
    key = f"testfile-{hashlib.md5(file_path.encode()).hexdigest()[:10]}-{session_id}"
    marker = os.path.join(state_dir, key)
    if not os.path.exists(marker):
        try:
            open(marker, "w").close()
        except Exception:
            pass
        print(f"TESTHINT|{file_path}")
        sys.exit(0)

print("NOOP")
PYEOF
)

case "$RESULT" in
    PUBGET\|*)
        PKG_DIR="${RESULT#PUBGET|}"
        if command -v flutter &>/dev/null && [[ -d "$PKG_DIR" ]]; then
            (cd "$PKG_DIR" && nohup flutter pub get >/dev/null 2>&1 &) || true
            python3 -c "import json,sys; print(json.dumps({'additionalContext': '[package-feedback] pubspec.yaml changed — flutter pub get fired in background in ' + sys.argv[1] + '. If this is a local path swap for cross-package dev, remember to revert it before committing.'}))" "$PKG_DIR"
        else
            echo '{}'
        fi
        ;;
    TESTHINT\|*)
        TEST_FILE="${RESULT#TESTHINT|}"
        python3 -c "import json,sys; print(json.dumps({'additionalContext': '[package-feedback] Test file edited — validate it now: flutter test ' + sys.argv[1] + ' (cheaper than discovering it at commit time).'}))" "$TEST_FILE"
        ;;
    *)
        echo '{}'
        ;;
esac

exit 0
