#!/usr/bin/env bash
# desc: PostToolUse(Write) — when THE KIT'S OWN findings artifact is written (a file named findings.json or *.findings.json whose parent directory is agent-kit-findings, the namespace core:review-local's step 5 and core:grill-me's pre-done step 4 both write into), calls validate_citations.py --gate against the session's read-ledger; on an unverified citation it exits 2 with the validator's report on stderr, the channel Claude Code feeds back to the model on a blocking exit. A findings.json belonging to some other tool, anywhere outside that directory, is declined silently — this hook ships at user scope and fires on every Write in every project. Fires after the write (PostToolUse cannot prevent the write itself), interrupting a review from proceeding as if a fabricated citation were confirmed. Fails open, never silently, when it cannot check at all — that notice rides hookSpecificOutput.additionalContext, because exit-0 stderr never reaches the model.
# retire-review: this gate's subject is a model behavior — a review asserting a file:line
# citation that overlaps nothing the session actually read. Its premise is evidenced, not
# assumed: validate_citations.py's --gate mode had zero callers before this hook, so the
# blocking path had never run. Re-verify its necessity at each major model generation, and
# retire it if it stops firing in real sessions across one.
#
# Failure modes, documented (same fail-open discipline as this plugin's other hooks —
# see model-routing.sh, no-silent-removal.sh):
#   (1) no python3 -> exit 0 (bash guard, before stdin is even read).
#   (2) the raw payload cannot contain a path inside the kit's findings directory -> exit 0
#       (bash guard, before a python3 interpreter is paid for; see the guard's own comment
#       for why it cannot disagree with the authoritative path test below).
#   (3) malformed JSON on stdin, or valid JSON that isn't a JSON object (a bare string,
#       array, or number) -> exit 0 (explicit isinstance(data, dict) check).
#   (4) tool_input absent or not a dict, or file_path missing/non-string -> exit 0
#       (explicit isinstance checks — a TRUTHY non-dict has the same crash risk as a
#       falsy one; `.get(..., {}) or {}` alone does not catch it).
#   (5) the write is not THE KIT'S findings artifact -> exit 0, SILENT. Three ways to
#       fail that: the parent directory isn't `agent-kit-findings`, the basename isn't
#       findings.json / *.findings.json, or the file doesn't exist on disk. The directory
#       test is the one that keeps this hook out of other people's business: it ships at
#       user scope and fires on EVERY Write in EVERY project, and `findings.json` is a
#       generic name for an unrelated schema. One case is in this repo — the kit's own
#       apk-archaeology emitter writes <work_dir>/findings.json (plugins/mobile/skills/
#       apk-archaeology/SKILL.md:297) — and any analyzer told to write its JSON report
#       under that name produces another. Matching the basename alone claimed all of
#       them, and reproducing four shapes at the watched name showed the damage is not
#       uniform: an eslint-shaped top-level array reached --gate and was BLOCKED at
#       exit 2 as fabrication (a JSON array parses as a findings list, and an element
#       with no evidence scores as unverified), while the object-shaped ones injected
#       "treat every citation as unconfirmed" into sessions that had no citations.
#       Silence is the correct output for a file that was never ours.
#   (6) no session_id in the event, a session_id that isn't a string, or a session_id
#       whose read-ledger is missing/empty/unusable -> exit 0 WITH a MODEL-VISIBLE note
#       (never silent): auto-discovery across concurrent sessions is unsafe (see the
#       comment at the ledger check below), so an absent session or ledger is treated as
#       "nothing to verify against", never as "everything is fabricated".
#   (7) the validator itself errors (wrong-shaped findings JSON, unreadable file, a
#       crash) -> exit 0 WITH a model-visible note, never swallowed. That note is a plain
#       sentence about what to do, not the validator's raw output pasted in: the file
#       matched our directory and our name but is not a findings array, so there were no
#       citations to check and "treat every one as unconfirmed" would be advice about a
#       set that is empty. One trimmed line of the validator's own text rides along,
#       because "input must be an array of findings" is the actionable part.
#
# WHY (6) AND (7) DO NOT USE stderr. An exit-0 hook's stderr does not reach the model —
# only the transcript. Verified live rather than reasoned about: a `claude -p --settings
# <probe> --output-format stream-json --verbose` run against a session with no ledger
# fired this hook (payload logged), the hook wrote the notice to stderr and exited 0, the
# notice text appeared ZERO times in the raw stream JSONL, and the model answered
# NO_HOOK_FEEDBACK. Six shipped sentences had asserted that notice was visible, and
# review-local's step 5 told the model to treat every citation as unconfirmed on a signal
# it could never receive — so a cold ledger read as a PASSED gate, a false clear. Both
# notices now ride hookSpecificOutput.additionalContext (exit 0), the same mechanism
# model-routing.sh's advisory uses in this plugin, re-verified live on the same probe harness.
# Exit 2 keeps its report on stderr: that path IS fed back to the model, observed
# separately, and additionalContext is not read on a blocking exit.
#
# Anchored on validate_citations.py's own --gate exit code (0 clean, 2 gated, 1 error),
# not on a substring match against its prose report: a passthrough finding whose CLAIM
# TEXT happens to contain the word "UNVERIFIED" must not trip the gate, and did under an
# earlier version of this hook that string-matched the report instead of reading the
# validator's own verdict.
set -uo pipefail

if ! command -v python3 &>/dev/null; then exit 0; fi

INPUT_JSON=$(cat)

# Cheap bash pre-filter — this hook is registered on EVERY Write in EVERY project where
# core is enabled, and almost none of them are the kit's findings artifacts. Without this,
# each one forks a python3 interpreter just to run a path test that was always going to fail.
#
# The authoritative test stays the python path check below; this guard only declines
# payloads that CANNOT reach it, and it is built so it cannot disagree. Python accepts a
# file_path only when a literal `agent-kit-findings` survives normalization as its parent
# directory component, so every path python accepts contains that literal substring in the
# raw payload. JSON's non-\u escapes (\" \\ \/ \b \f \n \r \t) each decode to a character
# that appears nowhere in `agent-kit-findings` (lowercase letters and a hyphen), so the
# only way a conforming payload can hide the substring from a raw-text match is a \uXXXX
# escape — which is why any input carrying one falls through to python instead of being
# declined here.
#
# The guard is deliberately the LOOSER of the two, and only in the safe direction: a path
# like /a/agent-kit-findings/../b/x.findings.json carries the substring, clears this guard,
# and is then declined by python because normalization moves it out of the directory. The
# reverse — python accepting what this guard declined — is what must never happen.
case "$INPUT_JSON" in
    *agent-kit-findings*) ;;  # may be the kit's findings artifact — python decides
    *'\u'*) ;;                # a \u escape could encode the substring — python decides
    *) exit 0 ;;              # neither — no decoded file_path here can satisfy the test
esac

export INPUT_JSON
SCRIPT_DIR="$(cd "$(dirname "$0")/../scripts" && pwd)"
export SCRIPT_DIR

python3 << 'PYEOF'
import json, os, subprocess, sys


def notice(msg):
    """Fail-open note on the ONE channel an exit-0 hook can reach the model through.

    stdout, as a hookSpecificOutput envelope — mirrors model-routing.sh's advisory. Bare
    text on stdout is NOT equivalent: without the envelope Claude Code shows it in the
    transcript and never injects it, which is the same invisibility as exit-0 stderr.
    """
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PostToolUse",
            "additionalContext": "[citation-check] " + msg,
        }
    }))


try:
    data = json.loads(os.environ.get("INPUT_JSON", "{}"))
except Exception:
    sys.exit(0)
if not isinstance(data, dict):
    sys.exit(0)

if data.get("tool_name") != "Write":
    sys.exit(0)

ti = data.get("tool_input")
if not isinstance(ti, dict):
    sys.exit(0)

fp = ti.get("file_path", "")
if not isinstance(fp, str) or not fp:
    sys.exit(0)

# THE AUTHORITATIVE TEST. Two conditions, both required, and the DIRECTORY is the one
# that keeps this hook off files that were never ours. Both producers write to
# ${TMPDIR:-/tmp}/agent-kit-findings/<session-id>.findings.json, so that directory is
# already the kit's namespace; matching it removes the entire foreign-file surface that
# a basename-only test claimed.
#
# The test is on the PARENT DIRECTORY'S NAME, not on a ${TMPDIR}/agent-kit-findings path
# prefix, for two reasons. The hook runs in the consumer session's environment, whose
# TMPDIR is not guaranteed to be the one the producer resolved when it built the path —
# a prefix comparison would be a second cross-process coupling that can silently stop
# matching. And a name test is testable from a fixture that lives in a repo.
#
# normpath FIRST, so the comparison is against a canonical path rather than whatever
# text the producer happened to render. Measured, not assumed — `python3 -c` over the
# forms below, all four of them:
#   /var/T//agent-kit-findings/x.findings.json      -> agent-kit-findings  (both ways)
#   /a/agent-kit-findings//x.findings.json          -> agent-kit-findings  (both ways)
#   /a/agent-kit-findings/./x.findings.json         -> '.' RAW, agent-kit-findings normed
#   /a/agent-kit-findings/                          -> declined either way
# So the macOS double slash — TMPDIR ends in `/`, which is why the producers' path
# renders as /var/folders/.../T//agent-kit-findings/<id>.findings.json — is NOT what
# normpath is buying: os.path.dirname strips the redundant separators on its own. What
# normpath buys is the `.` segment, where the raw parent is literally "." and the kit's
# own artifact would be declined. It also collapses `..`, which is what makes a path
# that merely passes THROUGH this directory on its way elsewhere resolve to where it
# actually lands and be declined there.
norm = os.path.normpath(fp)

if os.path.basename(os.path.dirname(norm)) != "agent-kit-findings":
    sys.exit(0)

base = os.path.basename(norm)
if base != "findings.json" and not base.endswith(".findings.json"):
    sys.exit(0)

script = os.path.join(os.environ.get("SCRIPT_DIR", ""), "validate_citations.py")
if not os.path.isfile(script) or not os.path.isfile(fp):
    sys.exit(0)

session = data.get("session_id", "")
if not isinstance(session, str):
    session = ""

# Mirrors validate_citations.py's own state-dir convention (default_state_dir()) and the
# read-ledger.sh filename convention -- a second place that has to stay in sync with those
# if either changes; kept to the minimum needed ("is there at least one usable record?"),
# not the full range-overlap logic, to bound the duplication.
state_dir = os.path.join(
    os.environ.get("CLAUDE_PLUGIN_DATA")
    or os.path.join(os.environ.get("TMPDIR", "/tmp"), "agent-kit-core"),
    "state",
)


def ledger_has_entries(path):
    if not path or not os.path.isfile(path):
        return False
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    e = json.loads(line)
                except Exception:
                    continue
                if isinstance(e, dict) and e.get("file"):
                    return True
    except Exception:
        return False
    return False


# A missing session_id is not evidence of fabrication -- it means auto-discovery would
# have to guess which ledger to use, and auto-discovery is unsafe under concurrent
# sessions (validate_citations.py warns about this itself). Skip rather than validate
# against a possibly-unrelated session's ledger and risk a false block on a real citation.
if not session:
    notice(
        "on " + fp + ": no session_id in this event -- cannot safely pin a read-ledger "
        "(auto-discovery is unsafe under concurrent sessions), so the citations in this "
        "artifact were NOT checked. Treat every one as unconfirmed: the mechanism did "
        "not run, so nothing passed it."
    )
    sys.exit(0)

ledger_path = os.path.join(state_dir, "read-ledger-" + session + ".jsonl")
if not ledger_has_entries(ledger_path):
    notice(
        "on " + fp + ": no usable read-ledger for session " + session + " (missing, "
        "empty, or unreadable), so the citations in this artifact were NOT checked -- "
        "and nothing here is flagged as fabricated either. Treat every citation as "
        "unconfirmed: the mechanism did not run, so nothing passed it."
    )
    sys.exit(0)

cmd = ["python3", script, "--findings", fp, "--gate", "--session", session]

try:
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
except Exception:
    sys.exit(0)

out = (r.stdout or "") + (r.stderr or "")

# Exit 2 is the one path where stderr IS fed back to the model, so the gate report goes
# there -- additionalContext is not read on a blocking exit.
if r.returncode == 2:
    print("Citation check on " + fp + ":\n" + out, file=sys.stderr)
    sys.exit(2)

if r.returncode not in (0, 2):
    # A clean sentence, not the validator's raw output. This file matched the kit's
    # directory and the kit's filename but is not a findings array, so the citation set
    # is EMPTY -- "treat every citation as unconfirmed" would be an instruction about
    # nothing, and it is the wrong thing to tell a reader whose real problem is the shape
    # of a file. The validator's own last line rides along, trimmed: on the common case
    # it reads "error reading findings: input must be an array of findings or
    # {"findings": [...]}", which is the actionable half. Last non-empty line, not the
    # first, so an unreadable-file traceback surfaces its exception rather than the word
    # "Traceback".
    detail = ""
    for _line in reversed(out.splitlines()):
        if _line.strip():
            detail = _line.strip()[:200]
            break
    notice(
        "on " + fp + ": this file is in the kit's findings directory and matches the "
        "findings filename, but validate_citations.py could not read it as a findings "
        "artifact (exit " + str(r.returncode) + "), so no citation was checked -- and "
        "there may well be none to check. If this IS a review artifact, it has to be a "
        "JSON array of findings (or {\"findings\": [...]}), each entry carrying a claim "
        "and an evidence {file, lineStart, lineEnd}; rewrite it in that shape and the "
        "check runs on the next write. If it is not a review artifact, it only collided "
        "with the kit's naming -- move it out of this directory and nothing here needs "
        "your attention."
        + (" Validator said: " + detail if detail else "")
    )

sys.exit(0)
PYEOF
rc=$?
exit "$rc"
