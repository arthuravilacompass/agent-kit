#!/usr/bin/env bash
# Hygiene gate: no content from the origin domain/company in the kit.
# Scans ONLY git-tracked files — gitignored and untracked paths (e.g. .claude/settings.local.json,
# docs/superpowers/, .worktrees/) never reach a commit, so flagging them is a false positive.
# Exit: 0 = clean · 1 = provenance content found · >=2 = grep aborted (indeterminate).
set -uo pipefail
cd "$(dirname "$0")/.." || exit 1

# --- Denylist composition: two tiers, on purpose ------------------------------------
# 1. STRUCTURAL patterns below are ticket/branch/package NAMING FORMATS, not names — a
#    format like "TF-123" or "release_26" identifies nobody, so it's safe to ship in a
#    public repo.
# 2. LITERAL patterns are actual proper nouns (a client name, an internal domain, a
#    squad name, a personal handle) tied to one engagement. Those cannot live in this
#    script, because this repo is public: a denylist that ships its own literals
#    publishes the very thing it exists to hide. They live in .provenance-deny — local,
#    gitignored, read at runtime below — with .provenance-deny.example (tracked, no real
#    names) as the shipped template and instructions.
#
# One discriminator from that local file is worth documenting here, generically, since
# the doctrine behind it is reusable even though the literal it protects isn't shippable:
# a literal proper noun can happen to spell an ordinary word of the kit's own working
# language, capitalized. Matching it case-insensitively, or without a word boundary,
# would false-positive on the kit's own legitimate lowercase vocabulary that shares those
# same letters. The fix is a case-sensitive, word-bounded match — narrow on purpose, not
# an oversight left in by accident.
DENY_STRUCTURAL='TF-[0-9]{3,}|TF-\\d|BM-[0-9]+|ID-[0-9]{6}|release_26|snapshot/26|tf-[a-z]+-mobile'

# --- Local literal tier: optional by necessity, never silent about it ---------------
# scripts/ isn't part of any plugin manifest — this gate doesn't ship to plugin
# installers. It runs in exactly two places: the maintainer's local pre-commit gate
# (docs/OPERATIONS.md §4), and .github/workflows/ci.yml on every push/PR to this public
# repo. CI's checkout NEVER has .provenance-deny — it's gitignored, so it's never pushed
# — which makes "clone without the file" the gate's own normal, guaranteed-to-recur
# state, not a hypothetical edge case. Hard-failing on absence would turn the
# maintainer's own CI permanently red on every run; that's worse than the risk it
# would guard against.
# So: absence is not failure. What must not happen is SILENT absence — the maintainer
# runs this gate before every commit, so the OK/FAILED line at the bottom always states
# whether a local file was loaded and how many patterns it contributed. Losing the file
# shows up as "0 local literal pattern(s)" on the very next run, not as nothing at all.
# A file that EXISTS but yields zero usable lines (all blank/comment) is a different,
# worse case — indistinguishable from truncation or a bad merge — and is treated as
# indeterminate (exit 2), the same doctrine already applied below to an empty tracked-
# file set: absence of content where content is expected is not read as "nothing to hide".
LOCAL_DENY_FILE=".provenance-deny"
literal_patterns=()
if [ -f "$LOCAL_DENY_FILE" ]; then
  while IFS= read -r line || [ -n "$line" ]; do
    trimmed="${line#"${line%%[![:space:]]*}"}"
    trimmed="${trimmed%"${trimmed##*[![:space:]]}"}"
    [ -z "$trimmed" ] && continue
    case "$trimmed" in
      \#*) continue ;;
    esac
    literal_patterns+=("$trimmed")
  done < "$LOCAL_DENY_FILE"

  if [ "${#literal_patterns[@]}" -eq 0 ]; then
    echo "ERROR: $LOCAL_DENY_FILE exists but has zero usable patterns (all blank/comment) —" >&2
    echo "  indeterminate: this looks like truncation or a bad merge, not an intentionally" >&2
    echo "  empty denylist (or a freshly copied .provenance-deny.example not yet populated" >&2
    echo "  with real values). Delete the file if you truly have nothing local to add." >&2
    exit 2
  fi

  DENY="$DENY_STRUCTURAL"
  for p in "${literal_patterns[@]}"; do
    DENY="$DENY|$p"
  done
  literal_status="${#literal_patterns[@]} local literal pattern(s) loaded from $LOCAL_DENY_FILE"
else
  DENY="$DENY_STRUCTURAL"
  literal_status="0 local literal pattern(s) — $LOCAL_DENY_FILE not found (expected in CI and in any clone with no client literals to hide; copy $LOCAL_DENY_FILE.example to populate your own)"
fi

# Fail CLOSED if git can't enumerate the tree: a broken/absent git must be indeterminate,
# never reported clean — the original grep-based gate kept that contract (">=2 = indeterminate").
# The guard is a separate preflight (not the exit code of a NUL-producing command substitution,
# which bash mangles): $(git ls-files -z) strips NUL bytes and is unreliable on bash 3.2.
if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "ERROR: not a git work tree (git absent/broken) — indeterminate, do NOT treat as clean" >&2
  exit 2
fi

# Enumerate tracked files, NUL-safe, excluding this gate itself (it holds the DENY patterns).
# Process substitution (not $()) so NUL delimiters survive; read -d '' loop for bash 3.2.
files=()
while IFS= read -r -d '' f; do files+=("$f"); done \
  < <(git ls-files -z ':!:scripts/check-provenance.sh')

if [ "${#files[@]}" -eq 0 ]; then
  # An empty tracked-file set in this repo is itself suspect (broken checkout) — not clean.
  echo "ERROR: no tracked files found — indeterminate, do NOT treat as clean" >&2
  exit 2
fi

grep -InE "$DENY" "${files[@]}"
rc=$?
if [ "$rc" -eq 0 ]; then
  echo "FAILED: provenance content found (above) ($literal_status)"
  exit 1
elif [ "$rc" -ge 2 ]; then
  echo "ERROR: grep aborted (exit $rc) — indeterminate result, do NOT treat as clean"
  exit "$rc"
fi
echo "OK: zero provenance content ($literal_status)"
