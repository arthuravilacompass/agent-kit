#!/usr/bin/env python3
# desc: buckets each partition's subpackage tree into presentation/domain/data/platform logical layers
"""extract_layers.py — per-partition logical-layer composition for apk-archaeology.

For each partition in partitions.json, walks its subpackage tree under
jadx_sources_dir/<prefix>/ and buckets subpackage-name tokens (directory
basenames) into 4 logical layers via a fixed keyword table:

  P  (presentation) : ui, view, viewmodel, presenter, renderer, databinding
  D  (domain)       : domain, usecase(s), model(s), validator(s), exception(s)
  Da (data)         : data, storage, api, repository(ies), datasource(s),
                       client(s), network
  Pl (platform/DI)  : adapter(s), ioc, generated, system, di

Two things this script gets right that a naive recursive walk would not:

1. PARTITION-BOUNDARY PRUNING. Partitions are not always independent,
   disjoint feature trees — an "aggregator" partition's own class_count can
   be just the loose files sitting directly in that package, with every
   actual subdirectory carved out as its OWN separate partition entry
   elsewhere in partitions.json. Walking the aggregator's subtree naively
   would vacuum up every descendant partition's subpackages as if they
   belonged to the aggregator, producing meaningless noise (and
   double-counting layer signal that actually belongs to the child). So:
   when walking partition X, recursion stops (does not descend, does not
   record a token) at any directory whose full path matches a DIFFERENT
   listed partition's prefix — that subtree belongs to that other
   partition, not to X. `summary.aggregators_pruned` counts how many
   partitions actually hit this rule at least once.
2. OWN-NAME AS TOKEN. A partition's own trailing path segment is also
   treated as one of its subpackage-name tokens, independent of pruning.
   This matters for a partition that is itself named after a layer (a side
   effect of the aggregator split above, e.g. a partition literally rooted
   at ".../ui") — without this, such a partition would show every layer
   false despite being exactly that layer. For an ordinary whole-feature
   partition, the trailing segment is never itself a keyword, so this is a
   no-op there.

A "5th shape" case is also handled: a bridge/handler-dispatch-style
partition (subpackages like `messagehandlers`, `sheet` rather than the
4-layer clean-arch shape) gets a distinct `note` rather than being reported
as "no layers present" — which would misleadingly read as a failure/gap
instead of a different-but-valid architecture.

Documented limitations:
  - The keyword table is a fixed, English-naming-convention vocabulary. A
    codebase that names its layers in another language, or with an
    unlisted synonym (e.g. `interactor` for domain, `mapper` for data), is
    invisible to this heuristic — a false negative, not chased with a
    larger dictionary.
  - Bucketing is presence/absence per layer (a boolean), not a count or a
    depth signal — a partition with one `ui/` file and a partition with
    fifty read the same (P: true). Layer WEIGHT is a deliberate non-goal
    here; only layer PRESENCE feeds the per-feature loop's architecture read.
  - The pruning rule matches on EXACT partition-prefix equality, not
    substring — a directory that merely starts with another partition's
    name (e.g. `.../uikit` vs. a partition rooted at `.../ui`) is correctly
    NOT pruned, but a genuine partition boundary typo in partitions.json
    (a prefix that doesn't exactly match the real directory casing/path)
    would silently fail to prune and leak into the parent's evidence.
  - The bridge-handler marker set (`messagehandlers`, `sheet`) is a fixed,
    small vocabulary observed on one real corpus — a different bridge
    implementation using other subpackage names reports as a genuine
    "no layers present" case instead of the 5th-shape note, a false
    negative accepted rather than guessed at. The note requires ALL markers
    present (a superset match), not just one: verified against a real
    corpus, a single-marker (any-overlap) match false-positived on an
    unrelated design-system/UI-library partition that happens to ship its
    own generic `sheet/` (bottom-sheet widget) subpackage — a coincidence
    of common English UI vocabulary, not a bridge-dispatch pattern. The
    superset requirement is deliberately still coarse (2 fixed tokens are
    not a strong classifier) but resolved that specific false positive
    without introducing a false negative on the corpus's own bridge
    partition, which carries both markers.

Pure stdlib. Deterministic: same jadx_sources_dir/partitions.json = same output.

Usage:
  python3 extract_layers.py <jadx_sources_dir> <partitions_json> --out <path>
  Default --out is data/layers.json.
"""
import argparse
import json
import os

LAYER_KEYWORDS = {
    "P": {"ui", "view", "viewmodel", "presenter", "renderer", "databinding"},
    "D": {
        "domain", "usecase", "usecases", "model", "models",
        "validator", "validators", "exception", "exceptions",
    },
    "Da": {
        "data", "storage", "api", "repository", "repositories",
        "datasource", "datasources", "client", "clients", "network",
    },
    "Pl": {"adapter", "adapters", "ioc", "generated", "system", "di"},
}

# A bridge/handler-dispatch partition exposes a distinct 5th shape -- a
# message-handler + bottom-sheet dispatch pattern -- not a clean-arch layer
# split. Flag it explicitly rather than reporting "no layers".
BRIDGE_MARKERS = {"messagehandlers", "sheet"}


def collect_tokens(jadx_sources_dir, prefix, all_prefixes):
    """Collect subpackage-name tokens (lowercased dir basenames) for
    `prefix`, including its own trailing segment, walked recursively under
    jadx_sources_dir/<prefix>/ but pruned at any directory that is the root
    of a DIFFERENT listed partition (see module docstring, point 1).

    Returns (tokens, pruned_count) — pruned_count is how many times this
    partition's walk hit a different partition's boundary and stopped."""
    root = os.path.join(jadx_sources_dir, *prefix.split("/"))
    tokens = {prefix.rsplit("/", 1)[-1].lower()}  # own-name token (point 2)
    pruned = 0
    if not os.path.isdir(root):
        return tokens, pruned

    stack = [root]
    while stack:
        current = stack.pop()
        try:
            children = [e for e in os.scandir(current) if e.is_dir()]
        except OSError:
            continue
        for child in children:
            rel = os.path.relpath(child.path, jadx_sources_dir).replace(os.sep, "/")
            if rel != prefix and rel in all_prefixes:
                # Boundary of a different partition -- its subtree is not
                # evidence for `prefix`. Do not descend, do not record.
                pruned += 1
                continue
            tokens.add(child.name.lower())
            stack.append(child.path)
    return tokens, pruned


def classify(tokens):
    return {layer: bool(tokens & keywords) for layer, keywords in LAYER_KEYWORDS.items()}


def build_note(tokens):
    if BRIDGE_MARKERS <= tokens:
        return "bridge-handler pattern — a distinct 5th shape, not a clean-arch layer split"
    return None


def extract_layers(jadx_sources_dir, partitions):
    all_prefixes = {p["prefix"] for p in partitions}
    result = {}
    aggregators_pruned = 0

    for p in partitions:
        prefix = p["prefix"]
        tokens, pruned = collect_tokens(jadx_sources_dir, prefix, all_prefixes)
        if pruned > 0:
            aggregators_pruned += 1
        layers = classify(tokens)
        result[prefix] = {
            "P": layers["P"],
            "D": layers["D"],
            "Da": layers["Da"],
            "Pl": layers["Pl"],
            "evidence": sorted(tokens),
            "note": build_note(tokens),
        }

    partitions_with_2plus_layers = sum(
        1
        for v in result.values()
        if sum([v["P"], v["D"], v["Da"], v["Pl"]]) >= 2
    )

    return {
        "summary": {
            "partitions_total": len(partitions),
            "partitions_with_2plus_layers": partitions_with_2plus_layers,
            "aggregators_pruned": aggregators_pruned,
        },
        "partitions": result,
    }


def main():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("jadx_sources_dir")
    parser.add_argument("partitions_json")
    parser.add_argument("--out", default="data/layers.json")
    args = parser.parse_args()

    with open(args.partitions_json, encoding="utf-8") as f:
        partitions = json.load(f)

    result = extract_layers(args.jadx_sources_dir, partitions)
    output = json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False)

    if args.out:
        out_dir = os.path.dirname(args.out)
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(output + "\n")
    else:
        print(output)


if __name__ == "__main__":
    main()
