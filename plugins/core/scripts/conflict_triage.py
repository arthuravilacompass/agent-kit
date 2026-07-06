#!/usr/bin/env python3
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
        print(f"   ! git merge-tree erro: {err.strip().splitlines()[0]}", file=sys.stderr)
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
                low.append((path, "lado da base é só import — provável troca de path"))
            else:
                decision.append((ctype, path, "conteúdo com lógica dos dois lados — reconciliar"))
        elif ctype == "modify/delete":
            only = edit_is_import_only(repo, pre, base, path)
            if only:
                decision.append((ctype, path, "DELEÇÃO SEGURA — a base só mexeu import; aceitar o delete da branch"))
            else:
                decision.append((ctype, path, "NÃO apague cego — a base tem mudança real; carregue ou perde silenciosamente"))
        elif ctype == "rename/delete":
            decision.append((ctype, path, "MANTÉM o move da base — arquivo realocado e ainda usado; confirme que a branch não tem substituto"))
        else:  # file location, rename/rename, ...
            decision.append((ctype, path, "decisão estrutural — os dois relocaram para lugares diferentes"))

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
                              "MANTÉM o move da base — movido de um diretório compartilhado; a 'deleção' da "
                              "branch é do path antigo, já resolvido pelo move. Cheque se mudou só o lugar ou "
                              "também lógica: git log --follow -- <path>"))
        elif rename:
            collapsed.append(("rename/delete", path, rename[1]))
        else:
            ctype, note = entries[0]
            collapsed.append((ctype, path, note))

    return source, generated, low, collapsed


def main():
    ap = argparse.ArgumentParser(description="Triagem de conflitos de merge entre uma mudança base e branches.")
    ap.add_argument("branches", nargs="+", help="branches a triar (ex.: origin/feature/my-branch)")
    ap.add_argument("--repo", required=True, help="path do repo a inspecionar")
    ap.add_argument("--base", required=True, help="ref pós-mudança-base (conteúdo já mergeado)")
    ap.add_argument("--pre", required=True, help="ref pré-mudança-base")
    args = ap.parse_args()

    for ref in (args.base, args.pre):
        if not ref_exists(args.repo, ref):
            sys.exit(f"ref não encontrada: {ref} (repo {args.repo}). Rode `git -C {args.repo} fetch origin` primeiro.")

    print(f"pós-mudança-base: {args.base}   |   pré-mudança-base: {args.pre}   |   repo: {args.repo}")
    print("Lembrete: `git -C <repo> fetch origin` antes — refs stale dão resultado errado.\n")

    for branch in args.branches:
        header = f"── {branch} "
        print(header + "─" * max(4, 64 - len(header)))
        if not ref_exists(args.repo, branch):
            print("   ! branch não existe localmente — fetch ou nome errado\n")
            continue
        source, generated, low, decision = triage_branch(args.repo, args.base, args.pre, branch)
        print(f"   conflitos fonte: {len(source)}   (gerados ignorados: {generated})")
        if low:
            print(f"   BAIXO ESFORÇO ({len(low)}):")
            for path, note in low:
                print(f"     · {path}  ({note})")
        if decision:
            print(f"   DECISÃO POR ARQUIVO ({len(decision)}):")
            for ctype, path, note in decision:
                print(f"     · [{ctype}] {path}")
                print(f"         → {note}")
        if not source:
            print("   (sem conflito de fonte — merge limpo; ainda pode quebrar no compile se houver arquivo novo com import velho)")
        print()


if __name__ == "__main__":
    main()
