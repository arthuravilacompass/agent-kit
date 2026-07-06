#!/usr/bin/env python3
"""Check internal Dart import resolution inside a git TREE object (no checkout).

Finds the failure mode that `git merge-tree` hides: after a rename-heavy
refactor merges cleanly at the text level, code that still points to the OLD
path of a moved file breaks at COMPILE time. We resolve every internal import
against the set of files that actually exist in the merged tree.

Usage: check_merged_imports.py <repo> <tree-oid> <pkg-name>
"""
import subprocess, sys, os, posixpath, re

repo, tree, pkg = sys.argv[1], sys.argv[2], sys.argv[3]

def git(*args):
    return subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True).stdout

# 1) every path present in the merged tree
paths = set(l for l in git("ls-tree", "-r", "--name-only", tree).splitlines() if l)
dart_paths = set(p for p in paths if p.endswith(".dart"))

# 2) every import/export line, with its containing file (git grep on the tree)
#    output: <tree>:<path>:<lineno>:<content>
raw = git("grep", "-nE", r"^[[:space:]]*(import|export)[[:space:]]", tree, "--", "*.dart")
prefix = tree + ":"
quote = re.compile(r"'([^']+)'")

unresolved = []   # (file, lineno, import, resolved_target)
checked = 0
for line in raw.splitlines():
    if not line.startswith(prefix):
        continue
    rest = line[len(prefix):]
    try:
        path, lineno, content = rest.split(":", 2)
    except ValueError:
        continue
    m = quote.search(content)
    if not m:
        continue
    imp = m.group(1)

    if imp.startswith(f"package:{pkg}/"):
        target = "lib/" + imp[len(f"package:{pkg}/"):]
    elif imp.startswith("package:") or imp.startswith("dart:"):
        continue  # external package — out of scope
    else:
        # relative import, resolve against the file's directory
        base = posixpath.dirname(path)
        target = posixpath.normpath(posixpath.join(base, imp))

    if not target.endswith(".dart"):
        continue
    if not target.startswith("lib/"):
        continue  # only judging app-internal targets
    checked += 1
    if target not in dart_paths:
        unresolved.append((path, lineno, imp, target))

print(f"tree={tree}  dart_files={len(dart_paths)}  internal_imports_checked={checked}")
print(f"UNRESOLVED (target file absent in merged tree) = {len(unresolved)}\n")
for path, lineno, imp, target in sorted(unresolved):
    print(f"  {path}:{lineno}")
    print(f"      import : {imp}")
    print(f"      target : {target}   <-- MISSING")
