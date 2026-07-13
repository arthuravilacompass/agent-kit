#!/usr/bin/env bash
# desc: PostToolUse(Edit|Write|MultiEdit) — runs dart format on the edited file.
# dart-auto-format.sh — PostToolUse hook (Edit|Write|MultiEdit)
# Runs `dart format --line-length 120 <file>` on .dart files after every edit.
# Silent on non-Dart files. Skips generated outputs (.g.dart, .freezed.dart, .config.dart).
# Failures never block the original tool — output is always `{}`.

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

# Skip code-gen outputs — formatting them re-triggers build_runner diffs.
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

dart format --line-length 120 "$FILE_PATH" >/dev/null 2>&1 || true

echo '{}'
exit 0
