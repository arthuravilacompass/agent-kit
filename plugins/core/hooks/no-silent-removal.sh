#!/usr/bin/env bash
# desc: PreToolUse(Edit|MultiEdit) — blocks (exit 2) an edit whose old_string carries a DI or observability annotation that new_string drops, unless the edit carries an "agent-kit: removal intentional — <why>" marker. Partial mechanization of the always-on rule "No silent removal of annotations/imports": imports and the override family are out of v1, and Write is out of scope (no old_string to compare).
# retire-review: this gate's subject is a model behavior — an edit dropping a DI or
# observability annotation from old_string without declaring the removal. Re-verify its
# necessity at each major model generation, and retire it if it stops firing in real
# sessions across one.
#
# Failure modes, documented (fails toward silence in every case, same contract as this
# plugin's other hooks — see model-routing.sh):
#   (1) no python3 -> exit 0 (bash guard, before stdin is even read).
#   (2) malformed JSON on stdin, or valid JSON that isn't a JSON object (a bare string,
#       array, or number) -> exit 0 (top-level try/except plus an explicit isinstance
#       check — `.get()` on a non-dict raises, which would exit 1, not 0).
#   (3) tool_input absent, not a dict (explicit isinstance check — a TRUTHY non-dict
#       value has the same crash-not-silence risk as (2), not just a falsy one), or
#       file_path missing/non-string/off the source-extension allowlist (matched
#       case-insensitively — `.DART` counts) -> exit 0 (this hook only judges source
#       files it recognizes; see the file-type gate below).
#   (4) an individual old_string/new_string pair that's missing, non-string, or an empty
#       old_string -> that pair is skipped, never blocks (other pairs in the same
#       MultiEdit are still checked).
#
# Known, accepted gap in the escape valve (declared, not fixed): the marker is matched
# as TEXT, with no notion of comment vs. string-literal vs. arbitrary code. A line like
# `final s = "agent-kit: removal intentional"; foo();` opens the valve — the remainder
# after the marker is `"; foo();`, which contains 3+ word characters ("foo") and clears
# the reason threshold even though nothing was actually written as a justification. This
# is inherent to a text-matching valve, not something the occurrence-selection or
# reason-shape fixes above can close, and it is not being fixed here — named alongside
# the Write and imports gaps so it's a declared limit, not a future surprise.
#
# Two more declared limits, neither fixed here, both pre-existing since v1:
#   (5) A region that already carries a reasoned marker does not re-open for a SECOND,
#       different removal in the same span — `has_reason` is per-side boolean, so a
#       fresh, well-formed reason next to an already-justified old_string still blocks.
#       The way through is a separate edit, or Write. The block message (below) states
#       this explicitly when it applies, instead of suggesting a marker that won't help.
#   (6) The annotation counter (`old.count(a) > new.count(a)`) is RAW TEXT, not a parse
#       — it counts the token anywhere in the string, comments and string literals
#       included. `old_string: "@injectable\nclass B {}"`, `new_string: "// B is no
#       longer @injectable, the factory builds it\nclass B {}"` genuinely removes the
#       annotation from the code and STILL EXITS 0, because the token still appears
#       once in each string (now inside a comment) — `old.count == new.count`. No
#       marker required: this is a CHEAPER bypass than the escape valve, reachable by
#       accident — the most natural justification comment a developer would write
#       ("`// @injectable removed, parent constructs it`") defeats the counter without
#       the author ever knowing this hook exists. Declared, not fixed: closing it needs
#       an actual comment/string-literal-aware scan, out of scope for a v1 text valve.
set -uo pipefail

if ! command -v python3 &>/dev/null; then exit 0; fi

INPUT_JSON=$(cat)
export INPUT_JSON

python3 << 'PYEOF'
import json, os, re, sys

try:
    data = json.loads(os.environ.get("INPUT_JSON", "{}"))
except Exception:
    sys.exit(0)

# Top-level payload must be a JSON OBJECT. Valid JSON that isn't one (a bare string,
# a bare array/number) parses without raising, but `.get(...)` on it raises
# AttributeError — that would exit 1 (a traceback), neither open nor closed. Guard it
# explicitly rather than let a surprise payload shape crash instead of pass through.
if not isinstance(data, dict):
    sys.exit(0)

if data.get("tool_name") not in ("Edit", "MultiEdit"):
    sys.exit(0)

ti = data.get("tool_input", {})
# `or {}` only rescues FALSY non-dict values (`None`, `""`, `[]`) — a TRUTHY non-dict
# ("nope", [1]) sailed through unchanged and crashed the first `ti.get(...)` below with
# the same AttributeError/exit-1 problem as the top-level check above. Explicit
# isinstance check closes both holes with the same fix shape.
if not isinstance(ti, dict):
    ti = {}

# File-type gate. Without this, the vocabulary below matches as bare substrings over
# RAW TEXT with no regard for what kind of file it's in — since `core` is enabled at
# user scope, that means every Edit to every file in every repo: a README sentence
# mentioning "@module", a CHANGELOG line listing "@injectable", a commented-out
# "// @injectable // TODO re-enable" being deleted, even this hook's own ANNOTATIONS
# list locking its own vocabulary (narrowing it would first require writing an escape
# marker into the very file the hook is blocking). Restrict to source extensions where
# these tokens are actually code, not prose — .md/.json/.jsonl/.sh (this repo's own
# CHANGELOG.md, hook-cases.jsonl, and hook sources) all fall outside it.
SOURCE_EXTS = (
    ".dart", ".ts", ".tsx", ".js", ".jsx", ".py", ".kt", ".java", ".swift", ".go",
    ".rb", ".cs",
)
file_path = ti.get("file_path", "")
if not isinstance(file_path, str) or not file_path.lower().endswith(SOURCE_EXTS):
    sys.exit(0)

# MultiEdit carries a list of pairs; Edit a single pair. Write is not matched at all:
# it has no old_string, so a whole-file rewrite that drops an annotation is invisible
# here. Known gap, stated rather than papered over with a matcher that can't deliver.
pairs = []
if isinstance(ti.get("edits"), list):
    for e in ti["edits"]:
        if isinstance(e, dict):
            pairs.append((e.get("old_string", ""), e.get("new_string", "")))
else:
    pairs.append((ti.get("old_string", ""), ti.get("new_string", "")))

# v1 vocabulary, deliberately narrow. The override family (@override, @protected,
# @visibleForTesting, @mustCallSuper) is EXCLUDED: this hook ships in `core`, which is
# enabled at user scope, so it fires in every project including client Flutter work —
# and @override is removed legitimately during ordinary refactors. Blocking that would
# make the gate noisy, and a noisy gate gets disabled, which is worse than no gate.
# Widen only on evidence of a real miss.
ANNOTATIONS = [
    "@injectable", "@Injectable", "@singleton", "@Singleton", "@lazySingleton",
    "@LazySingleton", "@factoryMethod", "@module", "@Module", "@Provides",
    "@observable", "@action", "@computed",
]
# v1 does NOT cover imports. The obvious implementation (regex the import lines, diff
# the sets) inverts its own coverage: a prefix-only pattern collapses every `import 'x';`
# to the token "import", so dropping one of two imports passes silently while an honest
# single removal always blocks. Imports return in v2 with whole-line comparison and evals
# for both failure directions. Stated here rather than shipped broken.

# The escape valve. The rule this mechanizes says removal requires "explicit
# justification" — so the mechanism makes the justification a syntactic precondition
# instead of forbidding removal outright. Without this, there is NO legitimate removal
# path through Edit: a dedicated removal edit trips the same check, and the only way out
# is Write, which this hook cannot see. A gate whose only exit is its own blind spot
# trains the agent to route around it.
#
# The reason bar is on the REST OF THE LINE AS A WHOLE, not on its first token. An
# earlier version required 3+ CONSECUTIVE alnum characters starting immediately after
# the separator — that passed "not injected anymore" (first word "not" = 3 chars) but
# BLOCKED "DI moved up to the parent widget", "no longer needed", "2 callers left, both
# manual", "(parent builds it)", and "órfão agora": six legitimate reasons whose first
# token is short, numeric, punctuation-led, or non-ASCII, rejected by the same message
# that told the actor a reason was needed — which reads as a marker-syntax problem, not
# a word-count problem on the wrong token, so the actor varies spacing/dashes and never
# fixes it. Fix: capture everything after the marker on the SAME LINE ONLY (`[^\n]*` —
# this must stay line-scoped: an earlier draft used `\s` as the separator, which crosses
# newlines and reads the NEXT LINE'S CODE as the "reason"; caught by the eval suite,
# not assumed fixed) and count `\w` characters (Unicode-aware — matches "órfão") ANYWHERE
# in that remainder, not just its first run. A bare marker or punctuation-only remainder
# still has zero word characters and still blocks.
ESCAPE_ANCHOR_RE = re.compile(r"agent-kit:\s*removal intentional\b([^\n]*)")
MIN_REASON_CHARS = 3


# Occurrence selection: ANY marker occurrence satisfying the threshold counts, not just
# the first one found. `.search()` (used through round 2) inspects only the first match
# in the text — with a single marker per string that's indistinguishable from "any", but
# a string can carry more than one, and round 2 never tested that dimension. Two failure
# modes, both real, both new versus round 1 (which used a single `.search()` over the
# WHOLE combined pattern — accidentally "any occurrence satisfies" by construction — so
# both of these are round-2-only regressions, not round-1 carryovers):
#   FAIL-OPEN: old_string = bare marker, THEN a reasoned marker from an earlier justified
#   removal, THEN the annotation being dropped now. `has_reason(old)` under first-match
#   only inspects the BARE one (no reason) -> False, even though a valid reasoned marker
#   exists later in the same string -> the "not has_reason(old)" half wrongly reads as
#   "old had no justification" -> the round-0 stale-marker rule (this edit must INTRODUCE
#   the justification, not inherit one) is defeated, because a stale reasoned marker
#   further down old_string is invisible to a first-match check.
#   FAIL-CLOSED: new_string = bare marker (e.g. a leftover from an earlier abandoned
#   attempt, or one sitting in a trailing comment/string literal) THEN a genuine reasoned
#   marker for THIS drop. First-match only inspects the bare one -> False -> a real,
#   present justification is ignored and the edit blocks anyway. This manufactures the
#   fail-open case above: an actor blocked by this reads "put the justification in the
#   edit", writes a bare marker first (still blocks), adds the reason below it (still
#   blocks, first match still bare) — the bare marker is now durable file content sitting
#   above a reasoned one, which is exactly the shape that defeats the stale-marker rule
#   on the NEXT wide-span edit that touches this region.
# Fix: `finditer` over every occurrence: True if ANY of them clears the threshold.
def has_reason(text):
    for m in ESCAPE_ANCHOR_RE.finditer(text):
        if len(re.findall(r"\w", m.group(1), re.UNICODE)) >= MIN_REASON_CHARS:
            return True
    return False


dropped = []
# Tracks whether ANY blocked pair had this shape: old_string already carries a VALID
# reasoned marker, so the block is not "no justification was ever offered" but "a
# justification already exists for this region, and the escape valve does not re-open
# for a second, different removal in the same span." The message below depends on
# which shape actually happened — see the block message note.
region_already_justified = False
for old, new in pairs:
    if not isinstance(old, str) or not isinstance(new, str) or not old:
        continue
    # The marker only counts when THIS edit introduces it: present (with a real reason)
    # in new_string AND absent from old_string. Without the "absent from old" half, a
    # wide-span edit whose replaced region happens to already contain a marker+reason
    # left by an earlier, unrelated justified removal silently waives every annotation
    # drop in the SAME edit — the marker is durable file content, not edit metadata, so
    # re-checking it against old_string is what makes "this edit carries a
    # justification" true instead of "this file region once did."
    if has_reason(new) and not has_reason(old):
        continue
    pair_dropped = [a for a in ANNOTATIONS if old.count(a) > new.count(a)]
    if pair_dropped:
        dropped.extend(pair_dropped)
        if has_reason(old):
            region_already_justified = True

if dropped:
    uniq = sorted(set(dropped))
    if region_already_justified:
        # Block message, case 2: `has_reason` is a boolean per side, so it cannot tell
        # "old_string had no justification" apart from "old_string already had one, and
        # this is a SECOND removal in the same span." The generic message below
        # ("put the justification in the edit itself") is round 1's failure verbatim
        # when this is the actual shape: it names a syntax problem ("no marker yet")
        # when the real constraint is elsewhere (a marker already exists and the valve
        # doesn't reopen) — an actor who adds a fresh, well-formed reason here still
        # gets exit 2, reads that as "I must have written the marker wrong," and varies
        # it forever instead of doing the one thing that actually works: a separate
        # edit, or Write. This message states the real constraint instead.
        print(
            "BLOCKED — this edit removes: " + ", ".join(uniq) + "\n"
            "This region already carries a removal-intentional marker WITH a reason. "
            "The escape valve does not re-open for a second removal in the same span — "
            "adding another marker here will not clear this gate, no matter how well "
            "formed the new reason is. To proceed: make this drop part of a SEPARATE "
            "edit (a fresh region, its own justification), or use Write if that is "
            "genuinely what the work needs (this hook does not see Write).",
            file=sys.stderr,
        )
    else:
        print(
            "BLOCKED — this edit removes: " + ", ".join(uniq) + "\n"
            "Removing a dependency-injection or observability annotation requires explicit "
            "justification. To proceed, put the justification in the edit itself:\n"
            "  // agent-kit: removal intentional — <why>\n"
            "The marker needs a reason after it; the marker alone does not pass.",
            file=sys.stderr,
        )
    sys.exit(2)

sys.exit(0)
PYEOF
