#!/usr/bin/env python3
"""selftest_extract_layers.py — synthetic fake jadx_sources_dir tree + a
matching partitions.json under a neutral `com.example` root, deliberately
not modeled on any real APK. Exercises: a clean 4-layer partition, an
"aggregator" partition whose child is separately listed in partitions.json
(pruning must not leak the child's subpackages into the parent, and the
child must still pick up its own trailing-segment layer), a
bridge-handler-shaped partition that must get the 5th-shape note instead of
reading as a 0-layer gap, and a partition carrying only ONE of the two
bridge markers (`sheet/` with no `messagehandlers/`) — the boundary case
that motivated requiring BOTH markers (a superset match), pinning that a
single generic-UI-vocabulary subpackage does not false-positive as the
bridge-handler shape."""
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(__file__))
from extract_layers import extract_layers  # noqa: E402

CLEAN = "com/example/clean"
AGGREGATOR = "com/example/app"
CHILD = "com/example/app/ui"
BRIDGE = "com/example/bridge"
ONE_MARKER = "com/example/designsystem"

PARTITIONS = [
    {"prefix": CLEAN, "class_count": 10, "kind": "feature"},
    {"prefix": AGGREGATOR, "class_count": 1, "kind": "infra"},
    {"prefix": CHILD, "class_count": 3, "kind": "feature"},
    {"prefix": BRIDGE, "class_count": 5, "kind": "feature"},
    {"prefix": ONE_MARKER, "class_count": 4, "kind": "feature"},
]


def write(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def make_fixture(tmp):
    sources = os.path.join(tmp, "sources")

    # (a) clean partition: one subdir per layer.
    write(os.path.join(sources, CLEAN, "ui", "MainActivity.java"), "package x;\nclass MainActivity {}\n")
    write(os.path.join(sources, CLEAN, "domain", "GetUser.java"), "package x;\nclass GetUser {}\n")
    write(os.path.join(sources, CLEAN, "data", "UserRepo.java"), "package x;\nclass UserRepo {}\n")
    write(os.path.join(sources, CLEAN, "adapter", "UserAdapter.java"), "package x;\nclass UserAdapter {}\n")

    # (b) aggregator: a loose file directly in its own root package, PLUS a
    # child partition (com/example/app/ui) separately listed in partitions.json.
    write(os.path.join(sources, AGGREGATOR, "AppShell.java"), "package x;\nclass AppShell {}\n")
    write(os.path.join(sources, CHILD, "MainScreen.java"), "package x;\nclass MainScreen {}\n")

    # (c) bridge-handler-shaped partition: no ui/domain/data/adapter subdirs.
    write(
        os.path.join(sources, BRIDGE, "messagehandlers", "PingHandler.java"),
        "package x;\nclass PingHandler {}\n",
    )
    write(os.path.join(sources, BRIDGE, "sheet", "ConfirmSheet.java"), "package x;\nclass ConfirmSheet {}\n")

    # (d) one-marker boundary case: a design-system/UI-library partition
    # that ships its own generic `sheet/` (bottom-sheet widget) subpackage
    # but no `messagehandlers/` -- must NOT read as the bridge-handler 5th
    # shape (superset match requires BOTH markers).
    write(
        os.path.join(sources, ONE_MARKER, "sheet", "BottomSheetWidget.java"),
        "package x;\nclass BottomSheetWidget {}\n",
    )

    return sources


def main():
    with tempfile.TemporaryDirectory() as tmp:
        sources = make_fixture(tmp)
        partitions_path = os.path.join(tmp, "partitions.json")
        write(partitions_path, json.dumps(PARTITIONS))
        with open(partitions_path, encoding="utf-8") as f:
            partitions = json.load(f)

        result = extract_layers(sources, partitions)
        by_prefix = result["partitions"]

        # (a) clean partition: all 4 layers present.
        clean = by_prefix[CLEAN]
        assert clean["P"] is True, clean
        assert clean["D"] is True, clean
        assert clean["Da"] is True, clean
        assert clean["Pl"] is True, clean
        assert clean["note"] is None, clean

        # (b) aggregator: pruned at the child's boundary -- no layer leaks in
        # from com/example/app/ui, so the parent shows every layer absent
        # despite its child genuinely being a `ui` partition.
        aggregator = by_prefix[AGGREGATOR]
        assert aggregator["P"] is False, aggregator
        assert aggregator["D"] is False, aggregator
        assert aggregator["Da"] is False, aggregator
        assert aggregator["Pl"] is False, aggregator
        assert "ui" not in aggregator["evidence"], aggregator

        # the child correctly picks up P from its OWN trailing segment name,
        # not from a subdirectory walk (it has no further subdirs at all).
        child = by_prefix[CHILD]
        assert child["P"] is True, child
        assert child["D"] is False, child
        assert child["Da"] is False, child
        assert child["Pl"] is False, child

        # (c) bridge-handler partition: distinguished from a genuine 0-layer
        # gap by its note, not silently reported as "nothing found".
        bridge = by_prefix[BRIDGE]
        assert bridge["P"] is False, bridge
        assert bridge["D"] is False, bridge
        assert bridge["Da"] is False, bridge
        assert bridge["Pl"] is False, bridge
        assert bridge["note"] == (
            "bridge-handler pattern — a distinct 5th shape, not a clean-arch layer split"
        ), bridge

        # (d) one-marker boundary: only `sheet/` present, no
        # `messagehandlers/` -- the superset requirement must reject this,
        # not misread it as the bridge-handler shape.
        one_marker = by_prefix[ONE_MARKER]
        assert one_marker["note"] is None, one_marker
        assert one_marker["P"] is False, one_marker
        assert one_marker["D"] is False, one_marker
        assert one_marker["Da"] is False, one_marker
        assert one_marker["Pl"] is False, one_marker

        # summary counts.
        assert result["summary"]["partitions_total"] == 5, result["summary"]
        assert result["summary"]["partitions_with_2plus_layers"] == 1, result["summary"]  # only CLEAN
        assert result["summary"]["aggregators_pruned"] == 1, result["summary"]  # only AGGREGATOR

    print(
        "OK: clean 4-layer partition, aggregator correctly pruned at child "
        "boundary (child still picks up its own-name layer), bridge-handler "
        "5th-shape note distinguished from a genuine 0-layer gap, and a "
        "single-marker (`sheet/`-only) partition correctly does NOT get the "
        "bridge-handler note"
    )


if __name__ == "__main__":
    main()
