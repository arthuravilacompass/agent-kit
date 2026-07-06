#!/usr/bin/env python3
"""Swap pubspec.yaml git-ref dependencies for local path dependencies, and back.

Generic for any multi-repo Flutter/Dart workspace where a subset of packages is
pinned via `git:` blocks (typically your own private/monorepo packages — public
deps go through pub.dev, not a git ref) and you want to point them at sibling
local checkouts during cross-package development.

Usage:
  swap_pubspec.py local  <pubspec_path> <workspace_dir> --packages pkg1=dir1,pkg2=dir2
  swap_pubspec.py remote <pubspec_path> --ref <ref> --url-base <base> --packages pkg1=dir1,pkg2=dir2

--packages is a comma-separated list of `pubspec_package_name=sibling_dir_name`
pairs. Example (placeholder names — use your own): --packages
my_shared_ui=my-shared-ui,my_sdk_client=my-sdk-client

In `remote` mode, each package's git url is reconstructed as
`<url-base>/<dir_name>.git` — pass the same --url-base you swapped away from
(there's no way to recover the exact original url once the git: block has been
replaced, so this is a best-effort reconstruction, not a byte-exact revert).
"""

import argparse
import sys
from pathlib import Path


def parse_packages(spec: str) -> dict[str, str]:
    pairs = {}
    for item in spec.split(','):
        item = item.strip()
        if not item:
            continue
        if '=' not in item:
            print(f'Error: --packages entry "{item}" is not in pkg=dir form', file=sys.stderr)
            sys.exit(1)
        pkg, dir_name = item.split('=', 1)
        pairs[pkg.strip()] = dir_name.strip()
    if not pairs:
        print('Error: --packages must list at least one pkg=dir pair', file=sys.stderr)
        sys.exit(1)
    return pairs


def _is_git_block(lines: list[str], i: int, pkg: str) -> bool:
    return (
        i + 3 < len(lines)
        and lines[i].rstrip() == f'  {pkg}:'
        and lines[i + 1].rstrip() == '    git:'
        and lines[i + 2].rstrip().startswith('      url:')
        and lines[i + 3].rstrip().startswith('      ref:')
    )


def _is_local_block(lines: list[str], i: int, pkg: str) -> bool:
    return (
        i + 1 < len(lines)
        and lines[i].rstrip() == f'  {pkg}:'
        and lines[i + 1].rstrip().startswith('    path:')
    )


def swap_to_local(pubspec_path: Path, workspace_dir: Path, packages: dict[str, str]) -> None:
    lines = pubspec_path.read_text().splitlines(keepends=True)
    result = []
    i = 0
    changed = False

    while i < len(lines):
        matched_pkg = next(
            (pkg for pkg in packages if _is_git_block(lines, i, pkg)), None
        )
        if matched_pkg:
            dir_name = packages[matched_pkg]
            path_value = workspace_dir / dir_name
            result.append(f'  {matched_pkg}:\n')
            result.append(f'    path: {path_value}\n')
            i += 4  # consume: pkg line + git: + url: + ref:
            changed = True
        else:
            result.append(lines[i])
            i += 1

    if not changed:
        print('swap_pubspec: already using local paths or pattern not matched — no change.')
        return

    pubspec_path.write_text(''.join(result))
    print(f'swap_pubspec: swapped to local paths ({workspace_dir})')


def swap_to_remote(pubspec_path: Path, ref: str, url_base: str, packages: dict[str, str]) -> None:
    lines = pubspec_path.read_text().splitlines(keepends=True)
    result = []
    i = 0
    changed = False

    while i < len(lines):
        matched_pkg = next(
            (pkg for pkg in packages if _is_local_block(lines, i, pkg)), None
        )
        if matched_pkg:
            dir_name = packages[matched_pkg]
            url = f'{url_base}/{dir_name}.git'
            result.append(f'  {matched_pkg}:\n')
            result.append(f'    git:\n')
            result.append(f'      url: {url}\n')
            result.append(f'      ref: {ref}\n')
            i += 2  # consume: pkg line + path: line
            changed = True
        else:
            result.append(lines[i])
            i += 1

    if not changed:
        print('swap_pubspec: already using git refs or pattern not matched — no change.')
        return

    pubspec_path.write_text(''.join(result))
    print(f'swap_pubspec: swapped to git refs (ref={ref})')


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('mode', choices=['local', 'remote'])
    parser.add_argument('pubspec', type=Path, help='Path to pubspec.yaml')
    parser.add_argument('workspace', nargs='?', type=Path,
                        help='Workspace directory (required for mode=local)')
    parser.add_argument('--ref', help='Git ref to restore (required for mode=remote)')
    parser.add_argument('--url-base', help='Git host + org/workspace base url (required for mode=remote)')
    parser.add_argument('--packages', required=True,
                        help='Comma-separated pkg=dir pairs, e.g. my_sdk=my-sdk,my_ui=my-ui')
    args = parser.parse_args()

    packages = parse_packages(args.packages)

    pubspec = args.pubspec.resolve()
    if not pubspec.exists():
        print(f'Error: {pubspec} not found', file=sys.stderr)
        sys.exit(1)

    if args.mode == 'local':
        if not args.workspace:
            print('Error: workspace directory is required for mode=local', file=sys.stderr)
            sys.exit(1)
        swap_to_local(pubspec, args.workspace.resolve(), packages)
    else:
        if not args.ref:
            print('Error: --ref is required for mode=remote', file=sys.stderr)
            sys.exit(1)
        if not args.url_base:
            print('Error: --url-base is required for mode=remote', file=sys.stderr)
            sys.exit(1)
        swap_to_remote(pubspec, args.ref, args.url_base, packages)


if __name__ == '__main__':
    main()
