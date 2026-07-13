#!/usr/bin/env bash
# desc: PostToolUse(Edit|Write|MultiEdit) — advisory: an edit ADDS a disposable resource (ReactionDisposer/TextEditingController/AnimationController/StreamSubscription/Timer) to a store/controller that has no dispose() anywhere; suggests naming the discard point.
#
# Add-only and advisory: fires only when THIS edit introduces the resource, and
# only if neither the added text nor the current file contains `dispose(`.
# Failure mode: a dispose living in another file (base class) is invisible ->
# possible false positive; the message says "confirm", never "you are wrong".

set -uo pipefail

if ! command -v python3 &>/dev/null; then
    exit 0
fi

INPUT_JSON=$(cat)
export INPUT_JSON

python3 << 'PYEOF'
import json, os, re, sys

try:
    data = json.loads(os.environ.get("INPUT_JSON", "{}"))
except Exception:
    sys.exit(0)

tool_input = data.get("tool_input", {}) or {}
file_path = tool_input.get("file_path", "")
if not (file_path.endswith("_store.dart") or file_path.endswith("_controller.dart")):
    sys.exit(0)
if "/test/" in file_path or file_path.endswith("_test.dart"):
    sys.exit(0)

RESOURCE = re.compile(
    r"\b(ReactionDisposer|TextEditingController|AnimationController|StreamSubscription|Timer)\b"
)

pairs = []
if "edits" in tool_input:  # MultiEdit
    for e in tool_input.get("edits", []) or []:
        pairs.append((e.get("old_string", ""), e.get("new_string", "")))
elif "new_string" in tool_input:  # Edit
    pairs.append((tool_input.get("old_string", ""), tool_input.get("new_string", "")))
elif "content" in tool_input:  # Write
    pairs.append(("", tool_input.get("content", "")))

added = [n for o, n in pairs if RESOURCE.search(n) and not RESOURCE.search(o)]
if not added:
    sys.exit(0)

if any("dispose(" in n for n in added):
    sys.exit(0)

try:
    with open(file_path, encoding="utf-8", errors="replace") as f:
        if "dispose(" in f.read():
            sys.exit(0)
except Exception:
    sys.exit(0)  # unreadable file -> stay quiet, never noisy-wrong

hits = sorted({m for n in added for m in RESOURCE.findall(n)})
print(
    "LIFECYCLE: this edit adds " + ", ".join(hits) + " to a store/controller "
    "with no dispose() in the file. State that survives needs a named discard "
    "point - confirm where this resource is released (a base-class dispose "
    "also counts; if so, ignore this).",
    file=sys.stderr,
)
sys.exit(2)
PYEOF

exit $?
