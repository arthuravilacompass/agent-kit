#!/usr/bin/env python3
# desc: Reads an import graph (dot) and reports layering violations against the project's config.
"""arch_violations.py — reads a lakos .dot import graph and reports layering-
direction violations against a project-supplied config.

No layering rule is baked into this script — every consuming project defines
its own layers, composition-root exceptions, and allowed/forbidden edge
directions in a small JSON config. That's the point: the previous version of
this script hardcoded one project's exact folder names (core/shared/modules)
and one exempted module name, which made it unusable — and unreadable as
an example — outside that project.

Usage: python3 arch_violations.py <arch.dot> [date] [--config <path>]

Default config location: <arch.dot's parent's parent>/arch-graph.config.json
(i.e. project-root/arch-graph.config.json when arch.dot lives in
project-root/build/arch.dot, following arch_graph.sh's own layout).

Config schema (JSON):
{
  "layers": [
    {"name": "core",   "match": "/lib/core/"},
    {"name": "shared", "match": "/lib/shared/"},
    {"name": "l10n",   "match": "/lib/l10n/", "exclude": true}
  ],
  "module_pattern": "/lib/modules/([^/]+)/",
  "module_exceptions": ["<module name exempt from the module-to-module rule>"],
  "composition_root_patterns": ["di_module", "app_router"],
  "direction_rules": [
    {"label": "core -> shared",   "from": "core",   "to": "shared"},
    {"label": "core -> modules",  "from": "core",   "to": "module:*"},
    {"label": "shared -> modules","from": "shared", "to": "module:*"},
    {"label": "module -> module", "from": "module:*", "to": "module:*", "cross_only": true}
  ]
}

- `layers`: ordered list of substring matchers; first match wins. Entries with
  `"exclude": true` (e.g. l10n/generated code) are dropped from every edge
  they touch, source or target.
- `module_pattern`: regex with one capture group — the module id — applied
  after the fixed layers fail to match. Files that match neither become
  layer "other" (never flagged).
- `module_exceptions`: module ids excluded from the "module -> module"
  cross-module count (e.g. a shared/kernel-like module every other module is
  allowed to import).
- `composition_root_patterns`: case-insensitive substrings; a source file
  matching any of them (DI wiring, router config, etc.) is exempt from every
  rule — composition roots are expected to import "the wrong way".
- `direction_rules`: each rule either checks a plain `from -> to` layer pair,
  or (`"cross_only": true`) counts edges between two DIFFERENT instances of a
  wildcarded layer (`module:*` -> `module:*`, excluding same-module edges and
  `module_exceptions` targets) — this is the "any module importing any other
  module" shape.

Without a config file, this script prints setup instructions and exits 1. It's
report-only by design (never fails a build) — an absent config is a setup gap,
not a graph problem.
"""
import argparse
import collections
import json
import re
import sys
from pathlib import Path


def load_config(path: Path) -> dict:
    if not path.is_file():
        print(f"No arch config found at {path}", file=sys.stderr)
        print(
            "Create an arch-graph.config.json describing YOUR project's layers "
            "(see this script's module docstring for the schema) — this script "
            "assumes no folder structure of its own.",
            file=sys.stderr,
        )
        sys.exit(1)
    return json.loads(path.read_text(encoding="utf-8"))


def build_layer_fn(config: dict):
    layers = config.get("layers", [])
    module_pattern = re.compile(config["module_pattern"]) if config.get("module_pattern") else None

    def layer(p: str) -> str:
        for entry in layers:
            if entry["match"] in p:
                return entry["name"]
        if module_pattern:
            m = module_pattern.search(p)
            if m:
                return "module:" + m.group(1)
        return "other"

    excluded = {e["name"] for e in layers if e.get("exclude")}
    return layer, excluded


def build_exception_fn(config: dict):
    patterns = [p.lower() for p in config.get("composition_root_patterns", [])]

    def is_exception(src: str) -> bool:
        b = src.lower()
        return any(p in b for p in patterns)

    return is_exception


def side_matches(layer_value: str, rule_side: str) -> bool:
    if rule_side.endswith(":*"):
        return layer_value.startswith(rule_side[:-1])
    return layer_value == rule_side


def parse_dot(dot_path: Path):
    edges = []
    acyclic = None
    for line in dot_path.read_text(encoding="utf-8").splitlines():
        m = re.match(r'\s*"([^"]+)"\s*->\s*"([^"]+)"', line)
        if m:
            edges.append((m.group(1), m.group(2)))
        if "isAcyclic" in line:
            acyclic = "true" in line.split("isAcyclic:")[1].split("\\l")[0].lower()
    return edges, acyclic


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("dot_path", type=Path)
    parser.add_argument("date", nargs="?", default="?")
    parser.add_argument("--config", type=Path, default=None)
    args = parser.parse_args()

    config_path = args.config or (args.dot_path.parent.parent / "arch-graph.config.json")
    config = load_config(config_path)

    layer, excluded_layers = build_layer_fn(config)
    is_exception = build_exception_fn(config)
    module_exceptions = set(config.get("module_exceptions", []))
    rules = config.get("direction_rules", [])
    cross_rule = next((r for r in rules if r.get("cross_only")), None)
    plain_rules = [r for r in rules if not r.get("cross_only")]

    edges, acyclic = parse_dot(args.dot_path)

    counts = collections.Counter()
    src_counter = collections.Counter()
    tgt_counter = collections.Counter()
    pairs = set()

    for s, d in edges:
        ls, ld = layer(s), layer(d)
        if is_exception(s) or ls in excluded_layers or ld in excluded_layers:
            continue

        if cross_rule and side_matches(ls, cross_rule["from"]) and side_matches(ld, cross_rule["to"]):
            module_id = ld.split(":", 1)[-1] if ":" in ld else ld
            if ls != ld and module_id not in module_exceptions:
                counts[cross_rule["label"]] += 1
                src_counter[ls.split(":", 1)[-1] if ":" in ls else ls] += 1
                tgt_counter[module_id] += 1
                pairs.add((ls, ld))

        for rule in plain_rules:
            if side_matches(ls, rule["from"]) and side_matches(ld, rule["to"]):
                counts[rule["label"]] += 1

    top_src = ", ".join(m for m, _ in src_counter.most_common(2))
    top_tgt = ", ".join(m for m, _ in tgt_counter.most_common(5))
    dag = "no (isAcyclic: false)" if acyclic is False else ("yes" if acyclic else "?")

    print(f"Direction violations (lakos, {args.date}):")
    if cross_rule:
        print(
            f"- {cross_rule['label']}: {counts[cross_rule['label']]} across {len(pairs)} pair(s)"
            f"  · worst sources: {top_src} · worst targets: {top_tgt}"
        )
    if plain_rules:
        print("- " + "   ·  ".join(f"{r['label']}: {counts[r['label']]}" for r in plain_rules))
    print(f"- acyclic graph (DAG)? {dag}")


if __name__ == "__main__":
    main()
