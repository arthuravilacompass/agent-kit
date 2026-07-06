#!/usr/bin/env bash
# dart-analyze-file.sh — PostToolUse hook (Edit|Write|MultiEdit)
# Runs `dart analyze` scoped to the SINGLE edited .dart file and feeds any
# errors/warnings/lints back to Claude as advisory context. Never blocks the edit.
#
# Fills the gap between two other hooks in this plugin:
#   - dart-auto-format.sh — formats, never analyzes.
#   - smell-checker.sh     — regex BLOCKER enforcement; can't see type/flow errors.
# Full `flutter analyze` stays out of hooks by design (too slow for a per-edit
# hook); this is the per-file version — fast enough for a turn, scoped to what
# just changed.
#
# Scope note: the `dart analyze` CLI runs the analyzer's built-in diagnostics + the
# `linter:` rules from analysis_options.yaml. It does NOT execute IDE-only analyzer
# plugins (e.g. dart_code_metrics), so those findings are intentionally out of scope
# here.
#
# Always advisory: emits additionalContext + exit 0. Analyze failures are swallowed.

set -uo pipefail

if ! command -v python3 &>/dev/null || ! command -v dart &>/dev/null; then
    echo '{}'
    exit 0
fi

INPUT_JSON=$(cat)

# Extract file_path from tool_input via stdin (safe from shell injection).
FILE_PATH=$(python3 -c "
import json, sys
try:
    data = json.loads(sys.stdin.read())
    inp = data.get('tool_input', {})
    fp = inp.get('file_path', '') if isinstance(inp, dict) else ''
    print(fp)
except Exception:
    print('')
" <<< "$INPUT_JSON" 2>/dev/null || echo "")

# Only act on .dart files.
if [[ -z "$FILE_PATH" || "$FILE_PATH" != *.dart ]]; then
    echo '{}'
    exit 0
fi

# Skip code-gen outputs — they aren't hand-maintained.
case "$FILE_PATH" in
    *.g.dart|*.freezed.dart|*.config.dart|*.mocks.dart)
        echo '{}'
        exit 0
        ;;
esac

if [[ ! -f "$FILE_PATH" ]]; then
    echo '{}'
    exit 0
fi

# Resolve the nearest package root (dir with pubspec.yaml) so analysis_options is picked up.
PKG_DIR=$(dirname "$FILE_PATH")
while [[ "$PKG_DIR" != "/" && ! -f "$PKG_DIR/pubspec.yaml" ]]; do
    PKG_DIR=$(dirname "$PKG_DIR")
done
if [[ ! -f "$PKG_DIR/pubspec.yaml" ]]; then
    echo '{}'
    exit 0
fi

# Single-file analyze, machine-readable. This hook's `timeout` in hooks.json caps wall time
# (a cold analysis server can be slow; the cap keeps a bad run from eating a whole turn).
ANALYZE_OUT=$(cd "$PKG_DIR" && dart analyze --format=machine "$FILE_PATH" 2>/dev/null || true)
export ANALYZE_OUT

if [[ -z "$ANALYZE_OUT" ]]; then
    echo '{}'
    exit 0
fi

# Format machine output into concise advisory context.
# Machine line shape: SEVERITY|TYPE|CODE|FILE|LINE|COL|LENGTH|MESSAGE
python3 << 'PYEOF'
import json, os, sys

raw = os.environ.get("ANALYZE_OUT", "")
RANK = {"ERROR": 0, "WARNING": 1, "INFO": 2}
MAX = 15

findings = []
for line in raw.splitlines():
    parts = line.split("|")
    if len(parts) < 8:
        continue
    severity, _type, code = parts[0], parts[1], parts[2]
    lineno, col = parts[4], parts[5]
    message = parts[7].replace("\\|", "|")
    findings.append((RANK.get(severity, 3), severity, code, lineno, col, message))

if not findings:
    print("{}"); sys.exit(0)

findings.sort(key=lambda f: (f[0], int(f[3]) if f[3].isdigit() else 0))
total = len(findings)
shown = findings[:MAX]

lines = [f"`dart analyze` on the edited file — {total} issue(s):"]
for _rank, severity, code, lineno, col, message in shown:
    lines.append(f"  {severity} {lineno}:{col} [{code}] {message}")
if total > MAX:
    lines.append(f"  …and {total - MAX} more.")

print(json.dumps({
    "hookSpecificOutput": {
        "hookEventName": "PostToolUse",
        "additionalContext": "\n".join(lines),
    }
}))
PYEOF

exit 0
