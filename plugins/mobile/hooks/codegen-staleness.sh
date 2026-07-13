#!/usr/bin/env bash
# desc: PostToolUse(Edit|Write|MultiEdit) — advisory: edited Dart source declares a codegen part ('.g.dart'/'.freezed.dart'/'.config.dart') whose generated file is missing or older than the source; suggests build_runner, once per file per session.
#
# Promotes the build_runner-staleness prose (mobx skill / code-review-mobile
# COOKBOOK / methodology §build_runner) to a mechanism. Advisory by design:
# PostToolUse exit 2 feeds stderr back to the model, it never blocks the edit.
# Failure mode: if mtimes lie (e.g. checkout normalizes them), the hook can
# stay silent — it fails QUIET, never noisy-wrong; the once-per-session marker
# caps noise at one warning per file.

set -uo pipefail

if ! command -v python3 &>/dev/null; then
    exit 0
fi

INPUT_JSON=$(cat)
export INPUT_JSON

MARKER_DIR="${CLAUDE_PLUGIN_DATA:-${TMPDIR:-/tmp}/agent-kit-mobile}/codegen-staleness"
export MARKER_DIR

python3 << 'PYEOF'
import hashlib, json, os, re, sys

try:
    data = json.loads(os.environ.get("INPUT_JSON", "{}"))
except Exception:
    sys.exit(0)

tool_input = data.get("tool_input", {}) or {}
file_path = tool_input.get("file_path", "")
GENERATED = (".g.dart", ".freezed.dart", ".config.dart", ".mocks.dart")
if (not file_path or not file_path.endswith(".dart")
        or file_path.endswith(GENERATED)
        or "/test/" in file_path or file_path.endswith("_test.dart")):
    sys.exit(0)

try:
    with open(file_path, encoding="utf-8", errors="replace") as f:
        source = f.read()
except Exception:
    sys.exit(0)

parts = re.findall(r"part\s+'([^']+\.(?:g|freezed|config|mocks)\.dart)'", source)
if not parts:
    sys.exit(0)

marker_dir = os.environ.get("MARKER_DIR", "")
marker = os.path.join(marker_dir, hashlib.sha1(file_path.encode()).hexdigest())
if marker_dir and os.path.exists(marker):
    sys.exit(0)

src_dir = os.path.dirname(file_path)
try:
    src_mtime = os.path.getmtime(file_path)
except OSError:
    sys.exit(0)

stale = []
for p in parts:
    gen = os.path.join(src_dir, p)
    try:
        if not os.path.exists(gen) or os.path.getmtime(gen) < src_mtime:
            stale.append(p)
    except OSError:
        continue

if not stale:
    sys.exit(0)

if marker_dir:
    try:
        os.makedirs(marker_dir, exist_ok=True)
        open(marker, "w").close()
    except Exception:
        pass  # marker failure never blocks the warning itself

print(
    "STALE CODEGEN: " + ", ".join(stale) +
    " older than (or missing for) the source you just edited. Generated state "
    "no longer matches the source - conclusions read from it are stale. Run: "
    "dart run build_runner build --delete-conflicting-outputs (once per file "
    "per session, this warning will not repeat).",
    file=sys.stderr,
)
sys.exit(2)
PYEOF

exit $?
