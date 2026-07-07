#!/usr/bin/env bash
# desc: PreToolUse(Edit|Write|MultiEdit) — bloqueia (exit 2, add-only) smells de correctness em Dart: DI direto, BuildContext vazando, print em produção.
# smell-checker.sh — PreToolUse Edit|Write|MultiEdit hook (exit 2 = blocks)
#
# Mechanical enforcement for a small set of statically-detectable Flutter/MobX
# smells:
#   DI001   — DI container resolved (get_it-style `GetIt.I<T>()`) inside a
#             *_store.dart / *_controller.dart file
#   ARCH001 — BuildContext/Navigator/GoRouter/dialog APIs inside a store/controller
#   LOG001  — print()/debugPrint() in production code (under lib/)
#
# ADD-ONLY logic: blocks only when the pattern is being ADDED (present in the
# new text, absent from the old text / existing file). Editing a legacy file
# without introducing a NEW violation still passes — this hook is a forward
# guard, not a full-repo lint. That's what makes it safe to turn on in a repo
# that already has legacy instances of these smells.
#
# Every block also appends one line to ${CLAUDE_PLUGIN_DATA}/smell-log.txt
# (date|code|file) — a side-effect for later rule tuning, never required for
# the hook itself to function.
#
# Config-free by design: DI001/ARCH001 assume the get_it + MobX (`_store.dart`
# / `_controller.dart`) stack this plugin's `mobx` skill documents. If your
# project uses a different DI container or naming convention, adjust the
# regex/suffixes below.

set -uo pipefail

if ! command -v python3 &>/dev/null; then
    echo '{}'
    exit 0
fi

INPUT_JSON=$(cat)
export INPUT_JSON

# Persistent state — never a workspace path, never ${HOME}/.claude directly.
SMELL_LOG="${CLAUDE_PLUGIN_DATA:-${TMPDIR:-/tmp}/agent-kit-mobile}/smell-log.txt"
export SMELL_LOG

python3 << 'PYEOF'
import json, os, re, sys, datetime

try:
    data = json.loads(os.environ.get("INPUT_JSON", "{}"))
except Exception:
    print("{}"); sys.exit(0)

tool_input = data.get("tool_input", {}) or {}
file_path = tool_input.get("file_path", "")
if not file_path or not file_path.endswith(".dart"):
    print("{}"); sys.exit(0)

GENERATED = (".g.dart", ".freezed.dart", ".config.dart", ".mocks.dart")
if file_path.endswith(GENERATED) or "/test/" in file_path or file_path.endswith("_test.dart"):
    print("{}"); sys.exit(0)

is_store = file_path.endswith("_store.dart") or file_path.endswith("_controller.dart")
in_lib = "/lib/" in file_path or file_path.startswith("lib/")

# (code, regex, message)
CHECKS = []
if is_store:
    CHECKS.append((
        "DI001",
        re.compile(r"GetIt\.(I\b|instance)"),
        "DI001: DI container resolved inside a store/controller. Dependencies should "
        "arrive via the constructor (e.g. @injectable/@lazySingleton). See the `mobx` "
        "skill's REFERENCE.md.",
    ))
    CHECKS.append((
        "ARCH001",
        re.compile(r"\bBuildContext\b|Navigator\.of\(|GoRouter\.of\(|ScaffoldMessenger\.of\(|showDialog\(|showModalBottomSheet\(|context\.(push|pop|go)\b"),
        "ARCH001: BuildContext/navigation/UI call inside a store/controller. Expose "
        "@observable state; the Page observes it and navigates. See the `mobx` skill's "
        "REFERENCE.md.",
    ))
if in_lib:
    CHECKS.append((
        "LOG001",
        re.compile(r"(?<![\w.])(print|debugPrint)\s*\("),
        "LOG001: print()/debugPrint() in production code. Use dart:developer log(). "
        "See the `mobx` skill's REFERENCE.md.",
    ))

if not CHECKS:
    print("{}"); sys.exit(0)

# (old_text, new_text) pairs per tool shape
pairs = []
if "edits" in tool_input:  # MultiEdit
    for e in tool_input.get("edits", []) or []:
        pairs.append((e.get("old_string", ""), e.get("new_string", "")))
elif "new_string" in tool_input:  # Edit
    pairs.append((tool_input.get("old_string", ""), tool_input.get("new_string", "")))
elif "content" in tool_input:  # Write
    old = ""
    try:
        if os.path.isfile(file_path):
            with open(file_path, encoding="utf-8", errors="replace") as f:
                old = f.read()
    except Exception:
        old = ""
    pairs.append((old, tool_input.get("content", "")))

def log_smell(code, fp):
    try:
        log_path = os.environ.get("SMELL_LOG", "")
        if not log_path:
            return
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        with open(log_path, "a") as f:
            f.write(f"{datetime.date.today().isoformat()}|{code}|{fp}\n")
    except Exception:
        pass  # logging never blocks or fails the hook

for code, pattern, msg in CHECKS:
    for old, new in pairs:
        # add-only: block only if the pattern is newly ADDED in this edit
        if pattern.search(new) and not pattern.search(old):
            log_smell(code, file_path)
            print(msg, file=sys.stderr)
            sys.exit(2)

print("{}")
sys.exit(0)
PYEOF

exit $?
