#!/usr/bin/env python3
# desc: renders OVERVIEW.md's deterministic sections from findings.json + template (design §3)
"""render_overview.py — deterministic render layer for apk-archaeology (design §3).

Fills ONLY the {{ dotted.path }} placeholders in overview.template.md from
the values in findings.json, and expands {{# map }}...{{/ map }} loop blocks
over open-map fields (e.g. manifest, one row per key). Sections wrapped in
<!-- AGENT:START name --> ... <!-- AGENT:END name --> are agent-synthesized
prose (the BLUF, the verdict narrative) and are copied through byte-for-byte,
untouched -- this script never authors or overwrites them (honest-scope
rule: the render layer owns only the deterministic slice derivable from
findings.json).

Fails loud (non-zero exit) if a referenced deterministic path is null or
missing in findings.json -- it never silently emits "None".

Pure stdlib. Deterministic: same (findings.json, template) -> byte-identical
output every time.

Usage:
  python3 render_overview.py <findings.json> <template> --out <file>
"""
import argparse
import json
import re
import sys

AGENT_BLOCK_RE = re.compile(
    r"<!--\s*AGENT:START\s+(\S+)\s*-->.*?<!--\s*AGENT:END\s+\1\b\s*-->",
    re.DOTALL,
)
LOOP_BLOCK_RE = re.compile(
    r"\{\{#\s*([\w.]+)\s*\}\}(.*?)\{\{/\s*\1\s*\}\}",
    re.DOTALL,
)
PLACEHOLDER_RE = re.compile(r"\{\{\s*([\w.]+)\s*\}\}")

# Allowed resolved-value types for a {{ }} placeholder. bool is deliberately
# excluded even though it is a subclass of int in Python.
SCALAR_TYPES = (str, int, float)


class RenderError(Exception):
    """Raised when a {{ }} placeholder references a null/missing path, a
    non-scalar value, or the rendered output still carries a residual/
    malformed template token -- fail loud."""


def resolve_path(findings, dotted):
    cur = findings
    for part in dotted.split("."):
        if not isinstance(cur, dict) or part not in cur:
            raise RenderError(f"placeholder path not found in findings.json: {dotted!r}")
        cur = cur[part]
    if cur is None:
        raise RenderError(f"placeholder path is null in findings.json: {dotted!r}")
    return cur


def substitute_scalars(text, lookup):
    def repl(m):
        val = lookup(m.group(1))
        if isinstance(val, bool) or not isinstance(val, SCALAR_TYPES):
            raise RenderError(
                f"placeholder {m.group(1)!r} resolved to a non-scalar value "
                f"({type(val).__name__}) -- only str/int/float are renderable"
            )
        return str(val)

    return PLACEHOLDER_RE.sub(repl, text)


def expand_loops(text, findings, stash):
    """Expand {{# path }}...{{/ path }} loop blocks. Each expanded row is
    fully substituted here (against the loop item, falling back to the
    top-level findings) and then stashed behind a sentinel token via
    `stash` -- an agent-authored value that happens to contain literal
    "{{ ... }}" text (e.g. a manifest `role` quoting a placeholder) must
    render byte-for-byte, not be re-scanned/re-substituted by the later
    top-level scalar pass."""

    def repl(m):
        path, body = m.group(1), m.group(2)
        collection = resolve_path(findings, path)
        if not isinstance(collection, dict):
            raise RenderError(f"loop path is not a map: {path!r}")

        rows = []
        for key, item in collection.items():
            if not isinstance(item, dict):
                raise RenderError(f"loop item at {path}.{key} is not an object")

            def item_lookup(field, _key=key, _item=item):
                if field == "key":
                    return _key
                if field in _item:
                    val = _item[field]
                    if val is None:
                        raise RenderError(f"loop field is null: {path}.{_key}.{field}")
                    return val
                return resolve_path(findings, field)

            row = substitute_scalars(body, item_lookup)
            rows.append(stash(row))
        return "".join(rows)

    return LOOP_BLOCK_RE.sub(repl, text)


def render(findings, template_text):
    """Render template_text against findings. Pure function, no I/O."""
    # Protect agent-authored sections and already-expanded loop rows behind
    # sentinel tokens -- neither is ever re-scanned by the top-level scalar
    # pass, even if their content happens to contain "{{" (defensive, not
    # just by luck; this is also what makes an agent-authored value like
    # "see {{ run.id }} here" render literally instead of being rewritten).
    sentinels = {}

    def stash(content):
        token = f"\x00SENTINEL_{len(sentinels)}\x00"
        sentinels[token] = content
        return token

    protected = AGENT_BLOCK_RE.sub(lambda m: stash(m.group(0)), template_text)

    expanded = expand_loops(protected, findings, stash)
    rendered = substitute_scalars(expanded, lambda path: resolve_path(findings, path))

    # Residual-token scan: at this point every AGENT block and every
    # expanded loop row is hidden behind an opaque sentinel token, so any
    # "{{" still visible in `rendered` can only be genuine unexpanded/
    # malformed template markup (an unclosed {{# loop }}, a placeholder
    # name the regex doesn't match, etc.) -- never agent-authored data.
    # Fail loud instead of letting it leak into the deliverable.
    if "{{" in rendered:
        raise RenderError(
            "residual '{{' found in rendered output -- malformed or unclosed "
            "template token (outside AGENT blocks and loop rows)"
        )

    for token, original in sentinels.items():
        rendered = rendered.replace(token, original)

    return rendered


def main():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("findings_json")
    parser.add_argument("template")
    parser.add_argument("--out", default=None)
    args = parser.parse_args()

    with open(args.findings_json, encoding="utf-8") as f:
        findings = json.load(f)
    with open(args.template, encoding="utf-8") as f:
        template_text = f.read()

    try:
        output = render(findings, template_text)
    except RenderError as e:
        print(f"render_overview.py: error: {e}", file=sys.stderr)
        sys.exit(1)

    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(output)
    else:
        print(output, end="")


if __name__ == "__main__":
    main()
