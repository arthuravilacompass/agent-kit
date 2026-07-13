#!/usr/bin/env bash
# desc: PostToolUse(Edit|Write|MultiEdit) — advisory: an edit ADDS an injectable annotation to a class that is absent from the project's injection.config.dart; suggests regenerating DI wiring (build_runner).
#
# Add-only and advisory. Failure modes, documented: (1) no injection.config.dart
# found -> silent (project may not use injectable's generated config);
# (2) same-named class in another module -> possible false negative;
# (3) monorepo: when CLAUDE_PROJECT_DIR is set the walk-up is skipped and only
# <root>/lib/** is searched, so a package at packages/*/lib is not found -> silent;
# (4) when the annotated span carries no `class` keyword, the class name is read
# from the whole on-disk file, which can flag unrelated classes -> possible
# false positive (hedged by the advisory posture). The check is a drift
# detector, not a completeness proof.

set -uo pipefail

if ! command -v python3 &>/dev/null; then
    exit 0
fi

INPUT_JSON=$(cat)
export INPUT_JSON

python3 << 'PYEOF'
import glob, json, os, re, sys

try:
    data = json.loads(os.environ.get("INPUT_JSON", "{}"))
except Exception:
    sys.exit(0)

tool_input = data.get("tool_input", {}) or {}
file_path = tool_input.get("file_path", "")
if not file_path.endswith(".dart") or file_path.endswith(".config.dart"):
    sys.exit(0)
if "/test/" in file_path or file_path.endswith("_test.dart"):
    sys.exit(0)

ANNOT = re.compile(r"@(injectable|lazySingleton|singleton|Injectable\(|LazySingleton\(|Singleton\()")

pairs = []
if "edits" in tool_input:
    for e in tool_input.get("edits", []) or []:
        pairs.append((e.get("old_string", ""), e.get("new_string", "")))
elif "new_string" in tool_input:
    pairs.append((tool_input.get("old_string", ""), tool_input.get("new_string", "")))
elif "content" in tool_input:
    pairs.append(("", tool_input.get("content", "")))

# Count-based add-only (see lifecycle-check): compare annotation counts so a new
# injectable class added next to an already-annotated one isn't silently dropped.
added = [n for o, n in pairs if len(ANNOT.findall(n)) > len(ANNOT.findall(o))]
if not added:
    sys.exit(0)

# class name: from the added text, else from the file on disk
classes = set()
for n in added:
    classes.update(re.findall(r"\bclass\s+(\w+)", n))
if not classes:
    try:
        with open(file_path, encoding="utf-8", errors="replace") as f:
            classes.update(re.findall(r"\bclass\s+(\w+)", f.read()))
    except Exception:
        sys.exit(0)
if not classes:
    sys.exit(0)

root = os.environ.get("CLAUDE_PROJECT_DIR", "")
if not root:
    root = os.path.dirname(file_path)
    for _ in range(6):  # walk up looking for a lib/ sibling
        if os.path.isdir(os.path.join(root, "lib")):
            break
        root = os.path.dirname(root)

configs = glob.glob(os.path.join(root, "lib", "**", "injection.config.dart"), recursive=True)
if not configs:
    sys.exit(0)  # project doesn't use injectable's generated config -> silent

registered = ""
for c in configs:
    try:
        with open(c, encoding="utf-8", errors="replace") as f:
            registered += f.read()
    except Exception:
        continue

# Word-boundary match, not raw substring: a bare `c not in registered` yields a
# false negative when the class name is a prefix of a registered one
# (e.g. `Auth` "in" `AuthService`). \b anchors both ends of the identifier.
missing = sorted(c for c in classes if not re.search(r"\b" + re.escape(c) + r"\b", registered))
if not missing:
    sys.exit(0)

print(
    "DI MISMATCH: " + ", ".join(missing) + " annotated as injectable but "
    "absent from injection.config.dart - the container will not resolve it "
    "until you run: dart run build_runner build --delete-conflicting-outputs.",
    file=sys.stderr,
)
sys.exit(2)
PYEOF

exit $?
