#!/usr/bin/env python3
# desc: Generates the plugin-table and badges fragments in README.md from plugins/*/.claude-plugin/plugin.json.
"""generate_readme_fragments.py — regenerates two marker-delimited fragments in
README.md from plugins/*/.claude-plugin/plugin.json:

  - <!-- generated:plugin-table:begin/end --> — the "What's included" table
    (Plugin | What it is | Install when).
  - <!-- generated:badges:begin/end -->       — one line of shields.io version
    badges (core, council, team, mobile), palette-matched to the routing
    diagram's ink tones. No status badge — versions only.

Pure stdlib (no PyYAML, no requests). Mirrors scripts/generate_inventory.py's
conventions:

  - Determinism: plugin order is a fixed curated tuple (PLUGIN_ORDER), not
    alphabetical — it matches the table's existing product framing (`mobile`
    the flagship, first). Every plugin actually found on disk (sorted()
    directory scan) must appear in PLUGIN_ORDER and vice versa — a mismatch
    (new plugin added, one removed) fails loudly rather than silently
    dropping a row.
  - No timestamp ever enters the output; writes always use '\\n' and utf-8.
  - The "What it is" / "Install when" table cells are curated copy, not
    plugin.json's `description` field verbatim — plugin.json's description is
    a one-line manifest summary, shorter than what the table needs to stay as
    informative as a hand-written README. The cells are kept as data in
    PLUGIN_TABLE_COPY, keyed by plugin name; only the version badges are read
    live from plugin.json.

Usage:
  python3 scripts/generate_readme_fragments.py            # rewrites README.md
  python3 scripts/generate_readme_fragments.py --check     # exit 0 if the file
                                                            # already matches;
                                                            # exit 1 with a
                                                            # unified diff if not.
"""

import difflib
import json
import os
import re
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
README_PATH = os.path.join(REPO_ROOT, "README.md")
PLUGINS_DIR = os.path.join(REPO_ROOT, "plugins")

# Curated display order — deliberately not alphabetical. Matches the existing
# "What's included" table: `mobile` (the flagship vertical) leads, `core` (the
# foundation under it) second, then `council`, then `team`.
PLUGIN_ORDER = ("mobile", "core", "council", "team")

TABLE_BEGIN = "<!-- generated:plugin-table:begin -->"
TABLE_END = "<!-- generated:plugin-table:end -->"
BADGES_BEGIN = "<!-- generated:badges:begin -->"
BADGES_END = "<!-- generated:badges:end -->"

# Badge palette: the routing diagram's ink/brown tones (its cream field,
# #fefdfa, is too light to read as a badge background). One consistent hex,
# no green/red semantics — these are version labels, not pass/fail signals.
BADGE_COLOR = "8a8378"

# "What it is" / "Install when" cells — curated prose, not plugin.json's
# `description` verbatim (see module docstring). Keep in sync by hand if the
# README's product framing changes; a plugin.json description change alone
# does NOT need to touch this table.
PLUGIN_TABLE_COPY = {
    "mobile": {
        "label": "`mobile` — **flagship**",
        "what": (
            "Flutter/Dart toolkit: review rules, scaffolding, four deterministic "
            "verifiers (one blocking smell-checker + three advisory hooks)"
        ),
        "when": "Flutter/Dart project on (or near) the assumed stack — note below",
    },
    "core": {
        "label": "`core`",
        "what": (
            "Deterministic mechanism: read-ledger and citation gate, the "
            "always-on discipline rules, `core:grill-me`'s checkpoints "
            "(`pre-plan`/`post-plan`/`pre-done`), the repo gates"
        ),
        "when": "Always — the foundation for the rest",
    },
    "council": {
        "label": "`council`",
        "what": "Epistemic lenses (reasoning postures) for high-cost-to-reverse decisions",
        "when": "Recommended with `core`",
    },
    "team": {
        "label": "`team`",
        "what": "Copilot for agile ceremonies — refinement with the PO, squad communication",
        "when": "You run refinement or write to a squad",
    },
}


class FragmentError(Exception):
    """Raised on any structural problem — always fatal, never silent."""


def rel(path):
    return os.path.relpath(path, REPO_ROOT).replace(os.sep, "/")


def esc(cell):
    if cell is None:
        cell = ""
    return cell.replace("\n", " ").replace("|", "\\|")


def discover_plugins():
    """sorted() scan of plugins/*/.claude-plugin/plugin.json, cross-checked
    against PLUGIN_ORDER in both directions."""
    if not os.path.isdir(PLUGINS_DIR):
        raise FragmentError(f"{rel(PLUGINS_DIR)}: directory does not exist")
    found = []
    for name in sorted(os.listdir(PLUGINS_DIR)):
        manifest = os.path.join(PLUGINS_DIR, name, ".claude-plugin", "plugin.json")
        if os.path.isfile(manifest):
            found.append(name)

    missing_from_order = [p for p in found if p not in PLUGIN_ORDER]
    if missing_from_order:
        raise FragmentError(
            "plugin(s) found on disk but not in PLUGIN_ORDER: "
            f"{missing_from_order} — add curated table copy and an order slot"
        )
    missing_on_disk = [p for p in PLUGIN_ORDER if p not in found]
    if missing_on_disk:
        raise FragmentError(
            f"PLUGIN_ORDER names plugin(s) not found on disk: {missing_on_disk}"
        )
    return found


def load_manifest(plugin):
    manifest_path = os.path.join(PLUGINS_DIR, plugin, ".claude-plugin", "plugin.json")
    try:
        with open(manifest_path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        raise FragmentError(f"{rel(manifest_path)}: could not read/parse manifest ({e})")
    for field in ("name", "description", "version"):
        if field not in data:
            raise FragmentError(f"{rel(manifest_path)}: missing required field '{field}'")
    if data["name"] != plugin:
        raise FragmentError(
            f"{rel(manifest_path)}: manifest name '{data['name']}' differs from "
            f"directory '{plugin}'"
        )
    return data


def render_table_fragment():
    plugins = discover_plugins()
    lines = [TABLE_BEGIN]
    lines.append("| Plugin | What it is | Install when |")
    lines.append("|---|---|---|")
    for plugin in PLUGIN_ORDER:
        if plugin not in PLUGIN_TABLE_COPY:
            raise FragmentError(f"no PLUGIN_TABLE_COPY entry for plugin '{plugin}'")
        copy = PLUGIN_TABLE_COPY[plugin]
        load_manifest(plugin)  # fails loud if the manifest itself is broken
        lines.append(
            "| " + " | ".join(esc(c) for c in (copy["label"], copy["what"], copy["when"])) + " |"
        )
    lines.append(TABLE_END)
    return lines, plugins


def render_badges_fragment():
    badges = []
    for plugin in PLUGIN_ORDER:
        manifest = load_manifest(plugin)
        version = manifest["version"]
        # shields.io treats literal '-' as a field separator and '_' as a space
        # escape, so both must be doubled in the plugin/version segments before
        # interpolation — underscores first, so a doubled '__' from an
        # underscore escape is never re-escaped as a hyphen pair.
        badge_plugin = plugin.replace("_", "__").replace("-", "--")
        badge_version = version.replace("_", "__").replace("-", "--")
        url = f"https://img.shields.io/badge/{badge_plugin}-{badge_version}-{BADGE_COLOR}"
        badges.append(f"![{plugin} {version}]({url})")
    return [BADGES_BEGIN, " ".join(badges), BADGES_END]


def splice(readme_lines, begin_marker, end_marker, fragment_lines):
    """Replace the inclusive span [begin_marker, end_marker] with fragment_lines.
    Fails loud if a marker is missing, duplicated, or unbalanced (end before
    begin, or nested)."""
    begin_idxs = [i for i, l in enumerate(readme_lines) if l.strip() == begin_marker]
    end_idxs = [i for i, l in enumerate(readme_lines) if l.strip() == end_marker]

    if not begin_idxs:
        raise FragmentError(f"marker missing from README.md: {begin_marker!r}")
    if not end_idxs:
        raise FragmentError(f"marker missing from README.md: {end_marker!r}")
    if len(begin_idxs) > 1:
        raise FragmentError(f"marker appears more than once in README.md: {begin_marker!r}")
    if len(end_idxs) > 1:
        raise FragmentError(f"marker appears more than once in README.md: {end_marker!r}")

    begin_idx, end_idx = begin_idxs[0], end_idxs[0]
    if end_idx < begin_idx:
        raise FragmentError(
            f"markers unbalanced in README.md: {end_marker!r} appears before {begin_marker!r}"
        )

    return readme_lines[:begin_idx] + fragment_lines + readme_lines[end_idx + 1:]


def generate():
    if not os.path.isfile(README_PATH):
        raise FragmentError(f"{rel(README_PATH)}: does not exist")
    with open(README_PATH, encoding="utf-8") as f:
        original = f.read()
    had_trailing_newline = original.endswith("\n")
    readme_lines = original.split("\n")
    if had_trailing_newline:
        readme_lines = readme_lines[:-1]

    table_fragment, _ = render_table_fragment()
    readme_lines = splice(readme_lines, TABLE_BEGIN, TABLE_END, table_fragment)

    badges_fragment = render_badges_fragment()
    readme_lines = splice(readme_lines, BADGES_BEGIN, BADGES_END, badges_fragment)

    return "\n".join(readme_lines) + ("\n" if had_trailing_newline else "")


def main():
    check_mode = "--check" in sys.argv[1:]
    try:
        content = generate()
    except FragmentError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1

    if check_mode:
        with open(README_PATH, encoding="utf-8") as f:
            disk_content = f.read()
        if disk_content == content:
            print("OK: README.md generated fragments are up to date.")
            return 0
        diff = difflib.unified_diff(
            disk_content.splitlines(keepends=True),
            content.splitlines(keepends=True),
            fromfile="README.md (disk)",
            tofile="README.md (generated)",
        )
        diff_text = "".join(diff)
        max_chars = 4000
        if len(diff_text) > max_chars:
            diff_text = diff_text[:max_chars] + "\n... (diff truncated)"
        print("FAILED: README.md generated fragments are out of date.\n", file=sys.stderr)
        print(diff_text, file=sys.stderr)
        return 1

    with open(README_PATH, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)
    print(f"OK: {rel(README_PATH)} fragments regenerated.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
