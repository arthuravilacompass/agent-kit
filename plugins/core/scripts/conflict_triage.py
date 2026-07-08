#!/usr/bin/env python3
# desc: Triages merge conflicts between a base branch and feature/team branches.
"""conflict_triage.py — triage merge conflicts between a base branch's landed change and a
set of feature/team branches.

For each branch given, simulate the merge against a base ref and classify every conflicting
*source* file:
  - LOW EFFORT : content conflict whose base-side change is import/path only
  - DECISION   : modify/delete, rename/delete, file-location, or content with real logic

The point of this tool: for modify/delete files (a branch deleted a file the base branch
also modified) it inspects WHAT the base changed in that file. If the base's edit was
import-only, accepting the branch's deletion is safe. If the base's edit carried a real
code change, deleting drops it silently (compiles clean, no merge conflict) — so the file
is flagged "do not delete blind".

It also distinguishes rename/delete (a file the base branch moved — keep the move) from
modify/delete (a file a branch is replacing outright — deletion usually wins).

Usage:
  git -C <repo> fetch origin                              # refresh refs FIRST — stale refs lie
  python3 conflict_triage.py --repo <repo> --base <post-change-ref> --pre <pre-change-ref> <branches...>

Tracking a team by author name only CONFIRMS an official branch list — it does not replace
it (a name finds who touched the area, not what conflicts).
"""
import argparse
import re
import subprocess
import sys

GENERATED = re.compile(r"\.(g|freezed|config|mocks)\.dart$")
SOURCE_EXT = re.compile(r"\.dart$")
FILE_TOKEN = re.compile(r"[\w./-]+\.\w+")
IMPORT_LINE = re.compile(r"^[+-]\s*(import|export)\s+['\"]")
CONFLICT_RE = re.compile(r"CONFLICT \(([^)]+)\):")


def git(repo, *args):
    """Run a git command; return stdout. merge-tree exits 1 on conflict — that is expected."""
    res = subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True)
    return res.stdout, res.stderr, res.returncode


def ref_exists(repo, ref):
    _, _, code = git(repo, "rev-parse", "--verify", "--quiet", ref)
    return code == 0


def find_conflicts(repo, base, branch):
    """Parse merge-tree CONFLICT lines into (conflict_type, path, raw_line) tuples."""
    out, err, _ = git(repo, "merge-tree", "--write-tree", base, branch)
    if err.strip() and not out.strip():
        print(f"   ! git merge-tree error: {err.strip().splitlines()[0]}", file=sys.stderr)
    rows = []
    for line in out.splitlines():
        if not line.startswith("CONFLICT"):
            continue
        m = CONFLICT_RE.match(line)
        ctype = m.group(1) if m else "unknown"
        # File-like tokens on the line; branch names have no extension so they drop out.
        tokens = [t for t in FILE_TOKEN.findall(line) if SOURCE_EXT.search(t) or t.endswith(".lock")]
        if not tokens:
            continue
        # modify/delete -> the (single) affected path is first; rename/file-location -> the destination is last.
        path = tokens[-1] if ("rename" in ctype or "location" in ctype) else tokens[0]
        rows.append((ctype, path, line.strip()))
    return rows


def edit_is_import_only(repo, pre, post, path):
    """Was the base's change to `path` (pre..post) import/export only?

    Returns True (mechanical), False (has real changes), or None (the base didn't touch this
    path, e.g. it created/renamed it — no verdict). Errs toward False: any non-import changed
    line -> False.
    """
    out, _, _ = git(repo, "diff", "--unified=0", f"{pre}..{post}", "--", path)
    if not out.strip():
        return None
    for line in out.splitlines():
        if line.startswith(("+++", "---", "@@", "diff ", "index ", "rename ", "similarity ", "new file", "deleted file")):
            continue
        if not line.startswith(("+", "-")):
            continue
        if line[1:].strip() == "":  # blank line change
            continue
        if IMPORT_LINE.match(line):
            continue
        return False
    return True


def triage_branch(repo, base, pre, branch):
    rows = find_conflicts(repo, base, branch)
    source = [(t, p, raw) for (t, p, raw) in rows if not GENERATED.search(p) and not p.endswith(".lock")]
    generated = len(rows) - len(source)

    low, decision = [], []
    for ctype, path, _ in source:
        if ctype == "content":
            only = edit_is_import_only(repo, pre, base, path)
            if only:
                low.append((path, "base's side is import-only — likely a path swap"))
            else:
                decision.append((ctype, path, "content with logic on both sides — reconcile"))
        elif ctype == "modify/delete":
            only = edit_is_import_only(repo, pre, base, path)
            if only:
                decision.append((ctype, path, "SAFE DELETE — the base only touched imports; accept the branch's delete"))
            else:
                decision.append((ctype, path, "do NOT delete blind — the base has a real change; carry it over or lose it silently"))
        elif ctype == "rename/delete":
            decision.append((ctype, path, "KEEP the base's move — file relocated and still used; confirm the branch has no replacement"))
        else:  # file location, rename/rename, ...
            decision.append((ctype, path, "structural decision — both sides relocated it to different places"))

    # A file the base *renamed* into a new path shows up twice: once as rename/delete and once
    # as modify/delete (the new path looks "fully new" to a path-scoped diff, so the import-only
    # check can't see it as a pure move). Collapse to a single accurate entry — the move is the
    # real story, not "logic changed".
    grouped = {}
    for ctype, path, note in decision:
        grouped.setdefault(path, []).append((ctype, note))
    collapsed = []
    for path, entries in grouped.items():
        rename = next((e for e in entries if "rename" in e[0]), None)
        if rename and len(entries) > 1:
            collapsed.append(("moved by base", path,
                              "KEEP the base's move — moved out of a shared directory; the branch's "
                              "'delete' targets the old path, already resolved by the move. Check whether "
                              "only the location changed or logic too: git log --follow -- <path>"))
        elif rename:
            collapsed.append(("rename/delete", path, rename[1]))
        else:
            ctype, note = entries[0]
            collapsed.append((ctype, path, note))

    return source, generated, low, collapsed


def main():
    ap = argparse.ArgumentParser(description="Triages merge conflicts between a base change and branches.")
    ap.add_argument("branches", nargs="+", help="branches to triage (e.g. origin/feature/my-branch)")
    ap.add_argument("--repo", required=True, help="path of the repo to inspect")
    ap.add_argument("--base", required=True, help="post-base-change ref (content already merged)")
    ap.add_argument("--pre", required=True, help="pre-base-change ref")
    args = ap.parse_args()

    for ref in (args.base, args.pre):
        if not ref_exists(args.repo, ref):
            sys.exit(f"ref not found: {ref} (repo {args.repo}). Run `git -C {args.repo} fetch origin` first.")

    print(f"post-base-change: {args.base}   |   pre-base-change: {args.pre}   |   repo: {args.repo}")
    print("Reminder: `git -C <repo> fetch origin` first — stale refs give wrong results.\n")

    for branch in args.branches:
        header = f"── {branch} "
        print(header + "─" * max(4, 64 - len(header)))
        if not ref_exists(args.repo, branch):
            print("   ! branch doesn't exist locally — fetch or wrong name\n")
            continue
        source, generated, low, decision = triage_branch(args.repo, args.base, args.pre, branch)
        print(f"   source conflicts: {len(source)}   (generated ignored: {generated})")
        if low:
            print(f"   LOW EFFORT ({len(low)}):")
            for path, note in low:
                print(f"     · {path}  ({note})")
        if decision:
            print(f"   PER-FILE DECISION ({len(decision)}):")
            for ctype, path, note in decision:
                print(f"     · [{ctype}] {path}")
                print(f"         → {note}")
        if not source:
            print("   (no source conflict — clean merge; can still break at compile time if a new file has a stale import)")
        print()


if __name__ == "__main__":
    main()
