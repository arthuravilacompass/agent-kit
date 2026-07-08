#!/usr/bin/env bash
# desc: PreToolUse(Bash) — auto-approves commands recognized as safe reads; writes, network, and dep mutation defer.
# PreToolUse(Bash) — fallback auto-approve for read-only commands.
#
# v2 (compound-aware): decomposes compound commands instead of refusing on any metacharacter.
# Approves ONLY if EVERY segment (and every command inside $()/backticks) is read-only.
# Safety invariant: any ambiguity (unbalanced quotes, unknown command,
# redirect to a file, nested substitution, background `&`) -> DEFERS.
# Parse failure = defer, NEVER approve.
#
# NEVER blocks (never exit 2 / deny) — only emits `allow` or defers (`{}`).
# Known limits (defer -> fall through to the normal prompt):
#   - redirect to a FILE (`> f`, `>> f`, `2> f`): can write. Only fd-dup (`2>&1`)
#     and `/dev/null` are approved.
#   - `sed`/`awk`/`xargs`/`find`/`mkdir`/`cp`/`mv`/`rm`/`tee`: write or execute.
#   - `for`/`while`/`if` (shell keywords as 1st token) -> unknown -> defer.
#   - NESTED command substitution ($() inside $()) -> defer.
# The primary prompt-reduction mechanism remains the sandbox; this hook only
# helps when the sandbox is inactive or the command falls outside it.

INPUT_JSON=$(cat)
export INPUT_JSON

python3 <<'PY'
import json, os, shlex, sys

def defer():
    print("{}")
    sys.exit(0)

def allow(reason):
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "allow",
            "permissionDecisionReason": reason,
        }
    }))
    sys.exit(0)

try:
    data = json.loads(os.environ.get("INPUT_JSON", "{}"))
    cmd = (data.get("tool_input", {}) or {}).get("command", "")
except Exception:
    defer()

if not cmd or not cmd.strip():
    defer()

# `cd` is safe (changes directory, doesn't write). `:`/`true` are no-ops.
READ_ONLY = {
    "cd", ":", "true",
    "ls", "cat", "head", "tail", "wc", "echo", "grep", "egrep", "fgrep", "rg",
    "which", "file", "stat", "diff", "uniq", "cut", "tr", "nl", "basename",
    "dirname", "realpath", "tree", "pwd", "printf", "column", "comm", "sort",
}
# Deliberately OUT: find, xargs, sed, awk, mkdir, cp, mv, rm, tee, dd (write/execute).

# `fetch` deliberately OUT: hits the network and changes local remote refs — not a read.
GIT_RO = {
    "status", "log", "diff", "show", "blame", "ls-files", "ls-tree", "grep",
    "rev-parse", "merge-base", "describe", "reflog", "for-each-ref", "cat-file",
    "shortlog", "rev-list", "name-rev", "verify-pack", "count-objects",
}


def cmd_readonly(tokens):
    """tokens = a single already-tokenized segment (no operators). True if read-only."""
    if not tokens:
        return True  # only env assignments remain; substitutions validated separately
    cmd0, rest = tokens[0], tokens[1:]

    if cmd0 in READ_ONLY:
        if cmd0 == "sort":  # `-o`/`--output` writes a file
            for a in rest:
                if a in ("-o", "--output") or a.startswith("--output="):
                    return False
        return True

    if cmd0 == "git":
        g = list(rest)
        while g and g[0].startswith("-"):
            if g[0] == "-C" and len(g) >= 2:  # only `-C <path>`; `-c`/others -> refuse
                g = g[2:]
                continue
            return False
        if not g:
            return False
        sub, args = g[0], g[1:]
        if sub == "config":
            return bool(args and args[0] in ("--get", "--get-all", "--list", "-l"))
        # branch/tag/remote: ALLOWLIST fail-closed — a deny-list fails OPEN whenever git
        # gains a new write flag/subcommand (e.g. `--set-upstream-to=x` in a single token
        # escaped exact-match; `remote set-branches` wrote config and slipped through).
        if sub == "branch":
            # bare `git branch` lists (read-only); a positional with no query flag CREATES.
            BRANCH_QUERY = {
                "--list", "-l", "--show-current", "--contains", "--no-contains",
                "--points-at", "--merged", "--no-merged", "--sort", "--format",
                "-v", "-vv", "--verbose", "-a", "--all", "-r", "--remotes",
                "--color", "--no-color", "--column", "--no-column", "--abbrev", "--no-abbrev",
            }
            if not args:
                return True
            flags = [a for a in args if a.startswith("-")]
            if any(a.split("=", 1)[0] not in BRANCH_QUERY for a in flags):
                return False
            # a positional (pattern/commit) is only safe alongside a query flag
            return bool(flags) or all(a.startswith("-") for a in args)
        if sub == "tag":
            # bare `git tag` lists; `git tag <name>` CREATES.
            TAG_QUERY = {
                "-l", "--list", "--contains", "--no-contains", "--points-at",
                "--merged", "--no-merged", "--sort", "--format", "--column", "--no-column",
            }
            if not args:
                return True
            flags = [a for a in args if a.startswith("-")]
            if any(a.split("=", 1)[0] not in TAG_QUERY for a in flags):
                return False
            return bool(flags)
        if sub == "remote":
            # `remote show` without -n hits the network — out. Only bare/-v/get-url.
            if not args:
                return True
            if args[0] in ("-v", "--verbose"):
                return True
            return args[0] == "get-url"
        return sub in GIT_RO

    # `pub get` (mutates lockfile/cache) and `test` (executes arbitrary repo code)
    # deliberately OUT — not reads; fall through to the normal prompt/sandbox.
    if cmd0 == "flutter":
        if rest[:1] in (["analyze"], ["doctor"]):
            return True
        return rest[:2] == ["pub", "deps"]

    if cmd0 == "dart":
        if rest[:1] == ["analyze"]:
            return True
        if rest[:2] == ["pub", "deps"]:
            return True
        if rest[:1] == ["format"]:
            return "--output=none" in rest or ("-o" in rest and "none" in rest)
        return False

    return False


def strip_env_assignments(tokens):
    i = 0
    while i < len(tokens):
        t = tokens[i]
        if "=" in t and not t.startswith("-") and t.split("=", 1)[0].isidentifier():
            i += 1
            continue
        break
    return tokens[i:]


def extract_substitutions(s):
    """Strips $(...) and `...`, returns (text_without_subst, [inners]). None if nested/unbalanced."""
    subs, out, i, n = [], [], 0, len(s)
    while i < n:
        c = s[i]
        if c == "`":
            j = s.find("`", i + 1)
            if j == -1:
                return None, None
            subs.append(s[i + 1:j])
            out.append("__SUBST__")  # no spaces: preserves `VAR=$(...)` as 1 token
            i = j + 1
            continue
        if c == "$" and i + 1 < n and s[i + 1] == "(":
            depth, j = 1, i + 2
            while j < n and depth:
                if s[j] == "(":
                    depth += 1
                elif s[j] == ")":
                    depth -= 1
                j += 1
            if depth:
                return None, None
            inner = s[i + 2:j - 1]
            if "$(" in inner or "`" in inner:
                return None, None  # nested -> too complex -> defer
            subs.append(inner)
            out.append("__SUBST__")  # no spaces: preserves `VAR=$(...)` as 1 token
            i = j
            continue
        out.append(c)
        i += 1
    return "".join(out), subs


SEP_OPS = {"|", "||", "&&", ";", "|&"}


def command_is_readonly(text, _depth=0):
    if _depth > 2:
        return False
    # Newlines separate statements; shlex(whitespace_split) swallows them. Normalize to `;`
    # BEFORE tokenizing, otherwise `echo hi\nrm -rf x` would become ONE segment whose cmd0 (echo)
    # looks read-only -> approving the `rm`. Inside quotes the `;` stays literal (safe).
    text = text.replace("\r\n", "\n").replace("\r", "\n").replace("\n", ";")
    stripped, subs = extract_substitutions(text)
    if stripped is None:
        return False
    for sub in subs:  # every substitution must be read-only
        if not command_is_readonly(sub, _depth + 1):
            return False

    # Tokenize respecting quotes; operators (| & ; < >) become their own tokens.
    try:
        lex = shlex.shlex(stripped, posix=True, punctuation_chars=True)
        lex.whitespace_split = True
        tokens = list(lex)
    except ValueError:
        return False  # unbalanced quotes etc.

    segments, cur, i = [], [], 0
    while i < len(tokens):
        t = tokens[i]
        if t in SEP_OPS:
            segments.append(cur)
            cur = []
            i += 1
            continue
        if t == "&":  # background -> unverifiable -> defer
            return False
        # A redirect/grouping operator is a token made ENTIRELY of punctuation (<>&()).
        # Do NOT use substring (`">" in t`): an arg like "a -> b" contains `>` and is not a redirect.
        if t and all(c in "<>&()" for c in t):
            if "(" in t or ")" in t:  # subshell / process substitution -> unverifiable
                return False
            if cur and cur[-1].isdigit():  # fd prefix (e.g. the `2` in `2>&1`)
                cur.pop()
            nxt = tokens[i + 1] if i + 1 < len(tokens) else None
            if t in (">&", "<&"):  # fd duplication: target is a number or `-`
                if nxt is not None and (nxt.isdigit() or nxt == "-"):
                    i += 2
                    continue
                return False
            # other redirects (`>`,`>>`,`<`,`&>`,...): only /dev/null is safe
            if nxt == "/dev/null":
                i += 2
                continue
            return False
        cur.append(t)
        i += 1
    segments.append(cur)

    for seg in segments:
        seg = strip_env_assignments(seg)
        if not cmd_readonly(seg):
            return False
    return True


try:
    ok = command_is_readonly(cmd)
except Exception:
    defer()  # any parse error -> defer (fail-safe, never approve by mistake)
if ok:
    allow("compound read-only command (every segment + substitution verified)")
defer()
PY
