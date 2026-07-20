#!/usr/bin/env python3
# desc: harvests cheap static facts — BuildConfig, network security config, DI modules, crash keys, design tokens (spec §5 [5])
"""extract_harvest.py — "block #5" cheap static harvest for apk-archaeology.

Five independent, mechanically-cheap categories, each best-effort over a
decompiled tree (jadx sources dir) and/or an apktool resource tree:

  1. build_config    — BuildConfig.java `public static final` fields (base
                        URLs, API keys, feature flags, VERSION_*). Every
                        String-literal value is redacted if it LOOKS like a
                        secret (reuses extract_endpoints.looks_like_secret —
                        single source of truth for the redaction rule, not a
                        forked copy). Independently, a field whose NAME
                        matches a secret-naming convention (API_KEY, TOKEN,
                        SECRET, ...) is ALSO redacted and flagged, even when
                        the value itself is too short/low-entropy to trip the
                        generic heuristic. This second signal is not
                        redundant: verified against a real corpus, hex-encoded
                        app keys (e.g. a field literally named `*_APPKEY`)
                        measured ~3.2 bits/char shannon entropy — under the
                        >=4.0 threshold — so the value-only heuristic alone
                        would have let them through unredacted.
  2. network_security_config — res/xml/network_security_config.xml: trusted
                        domains (+ includeSubdomains), cleartextTrafficPermitted
                        (root and per domain-config), and pin-sets.
  3. di_modules       — classes annotated `@Module` / `@Component`
                        (Dagger/Hilt) and the bindings they provide (methods
                        annotated `@Binds` / `@Provides`) — a module-boundary
                        signal, not a full DI graph.
  4. crash_keys       — `setCustomKey("literal", ...)` call sites where the
                        key name is a string literal in the source. Honest
                        null when an app only ever calls the batch form
                        (`setCustomKeys(map)`) with a runtime-built map — the
                        key names are not statically visible, and this script
                        does not attempt dataflow to recover them.
  5. design_tokens    — res/values/colors.xml + res/values/dimens.xml
                        name -> value tokens.

All five are best-effort, line-anchored (file + line), heuristic extraction
— not a compiler/AST pass. Each has a documented scope limit (see the
docstring of its extractor function below) in the same spirit as
classify_packages.py / extract_endpoints.py: a named, accepted fragility,
not chased with more machinery.

Pure stdlib. Deterministic: same trees = same output.

Usage:
  python3 extract_harvest.py <jadx_sources_dir> <apktool_dir> [--out <path>]
  Default --out is data/harvest.json (written, not printed) — pass --out ""
  to print to stdout instead.
"""
import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from extract_endpoints import looks_like_secret  # noqa: E402 — reuse the redaction rule, not a fork

# ---------------------------------------------------------------------------
# 1. BuildConfig
# ---------------------------------------------------------------------------

# One field per physical line — verified against ~30 real BuildConfig.java
# files (jadx always emits one `public static final` declaration per line,
# even for array literals like `{A, B, C}`). A field whose initializer
# legitimately spans multiple lines (arbitrary Java, not jadx output) is
# silently skipped — documented limitation, not chased.
BUILD_CONFIG_FIELD_RE = re.compile(
    r'^\s*public\s+static\s+final\s+([\w.\[\]<>]+)\s+(\w+)\s*=\s*(.+);\s*$'
)
STRING_LITERAL_FULL_RE = re.compile(r'^"((?:[^"\\]|\\.)*)"$')

# Name-based secret signal — independent of the value heuristic (see module
# docstring: this is what catches low-entropy/short secrets the value check
# structurally cannot, e.g. hex-encoded keys under 20 chars or entropy <4.0).
SECRET_NAME_RE = re.compile(
    r"(API[_]?KEY|APP[_]?KEY|SECRET|TOKEN|PASSWORD|PASSWD|PWD|CREDENTIAL|"
    r"PRIVATE[_]?KEY|ACCESS[_]?KEY|CLIENT[_]?SECRET)",
    re.IGNORECASE,
)


def find_build_config_files(jadx_sources_dir):
    for root, _dirs, files in os.walk(jadx_sources_dir):
        for fname in files:
            if fname == "BuildConfig.java":
                yield os.path.join(root, fname)


def extract_build_config(jadx_sources_dir):
    """Returns (fields, files_scanned, secrets_redacted, secret_names_flagged)."""
    fields = []
    files_scanned = 0
    secrets_redacted = 0
    secret_names_flagged = 0

    for full in sorted(find_build_config_files(jadx_sources_dir)):
        rel = os.path.relpath(full, jadx_sources_dir)
        files_scanned += 1
        with open(full, encoding="utf-8", errors="replace") as f:
            for lineno, line in enumerate(f, start=1):
                m = BUILD_CONFIG_FIELD_RE.match(line)
                if not m:
                    continue
                type_, name, raw_value = m.group(1), m.group(2), m.group(3).strip()
                name_flag = bool(SECRET_NAME_RE.search(name))
                if name_flag:
                    secret_names_flagged += 1

                lit = STRING_LITERAL_FULL_RE.match(raw_value)
                if lit:
                    literal = lit.group(1)
                    redacted = name_flag or looks_like_secret(literal)
                    value = "[REDACTED]" if redacted else literal
                    if redacted:
                        secrets_redacted += 1
                else:
                    # Non-string literal (boolean/int/array/enum/class ref) —
                    # nothing to leak, kept verbatim as-is.
                    value = raw_value
                    redacted = False

                fields.append(
                    {
                        "file": rel,
                        "line": lineno,
                        "field": name,
                        "type": type_,
                        "value": value,
                        "secret_name_flag": name_flag,
                        "value_redacted": redacted,
                    }
                )

    return fields, files_scanned, secrets_redacted, secret_names_flagged


# ---------------------------------------------------------------------------
# 2. network_security_config.xml
# ---------------------------------------------------------------------------

# Line-anchored, not a full XML parser (consistent with this script family's
# style — see extract_endpoints.py's per-line regex approach). Assumes
# apktool's default pretty-print: one tag per physical line, verified against
# a real network_security_config.xml. A hand-minified file with multiple
# elements packed on one line would under-anchor — documented, not chased.
ROOT_OPEN_RE = re.compile(r"<network-security-config([^>]*)>")
BASE_CONFIG_OPEN_RE = re.compile(r"<base-config([^>]*)>")
DOMAIN_CONFIG_OPEN_RE = re.compile(r"<domain-config([^>]*)>")
DOMAIN_CONFIG_CLOSE_RE = re.compile(r"</domain-config>")
DOMAIN_RE = re.compile(r'<domain(?:\s+includeSubdomains="(true|false)")?\s*>([^<]*)</domain>')
PIN_SET_OPEN_RE = re.compile(r'<pin-set(?:\s+expiration="([^"]*)")?\s*>')
PIN_RE = re.compile(r'<pin\s+digest="([^"]*)"\s*>([^<]*)</pin>')
CLEARTEXT_ATTR_RE = re.compile(r'cleartextTrafficPermitted="(true|false)"')


def _cleartext_from_attrs(attrs):
    m = CLEARTEXT_ATTR_RE.search(attrs or "")
    return (m.group(1) == "true") if m else None


def extract_network_security_config(apktool_dir):
    full = os.path.join(apktool_dir, "res", "xml", "network_security_config.xml")
    if not os.path.isfile(full):
        return {
            "found": False,
            "file": None,
            "base_cleartext_traffic_permitted": None,
            "domain_configs": [],
        }

    rel = os.path.relpath(full, apktool_dir)
    base_cleartext = None
    domain_configs = []
    current = None

    with open(full, encoding="utf-8", errors="replace") as f:
        for lineno, line in enumerate(f, start=1):
            root_m = ROOT_OPEN_RE.search(line)
            if root_m:
                c = _cleartext_from_attrs(root_m.group(1))
                if c is not None:
                    base_cleartext = c
                continue

            base_m = BASE_CONFIG_OPEN_RE.search(line)
            if base_m:
                c = _cleartext_from_attrs(base_m.group(1))
                if c is not None:
                    base_cleartext = c
                continue

            dc_open = DOMAIN_CONFIG_OPEN_RE.search(line)
            if dc_open:
                current = {
                    "line": lineno,
                    "cleartext_traffic_permitted": _cleartext_from_attrs(dc_open.group(1)),
                    "domains": [],
                    "pin_set": None,
                }
                continue

            if DOMAIN_CONFIG_CLOSE_RE.search(line):
                if current is not None:
                    domain_configs.append(current)
                    current = None
                continue

            if current is not None:
                dom_m = DOMAIN_RE.search(line)
                if dom_m:
                    current["domains"].append(
                        {
                            "domain": dom_m.group(2).strip(),
                            "include_subdomains": dom_m.group(1) == "true",
                            "line": lineno,
                        }
                    )
                    continue

                ps_open = PIN_SET_OPEN_RE.search(line)
                if ps_open:
                    current["pin_set"] = {"expiration": ps_open.group(1), "pins": []}
                    continue

                if current["pin_set"] is not None:
                    pin_m = PIN_RE.search(line)
                    if pin_m:
                        current["pin_set"]["pins"].append(
                            {
                                "digest": pin_m.group(1),
                                "value": pin_m.group(2).strip(),
                                "line": lineno,
                            }
                        )
                        continue

    return {
        "found": True,
        "file": rel,
        "base_cleartext_traffic_permitted": base_cleartext,
        "domain_configs": domain_configs,
    }


# ---------------------------------------------------------------------------
# 3. DI modules (@Module / @Component)
# ---------------------------------------------------------------------------

# `(?!\.)` excludes `@Component.Builder` (a nested marker annotation, not a
# module boundary itself) while still matching `@Component(modules = {...})`
# and a bare `@Module`.
MODULE_ANNOTATION_RE = re.compile(r"^\s*@(Module|Component)\b(?!\.)")
CLASS_DECL_RE = re.compile(r"\b(?:class|interface)\s+(\w+)")
# `\b` after Binds/Provides excludes `@BindsInstance` (a Dagger builder-arg
# marker, not a provided binding).
BINDING_MARKER_RE = re.compile(r"^\s*@(Binds|Provides)\b")
METHOD_NAME_RE = re.compile(r"(\w+)\(")
ANNOTATION_LOOKAHEAD_LINES = 20
METHOD_NAME_LOOKAHEAD_LINES = 5


def extract_di_modules(jadx_sources_dir):
    """Returns a list of {file, line, class, annotation, provides}.

    Two-pass per file: (1) find every `@Module`/`@Component` declaration,
    independent of nesting depth — this is what makes a nested `@Module`
    (e.g. a Dagger `MainModule` declared inside its own `@Component`) show up
    as its OWN entry rather than being swallowed by the enclosing one.
    (2) for each declaration, scan for `@Binds`/`@Provides` bindings in the
    window bounded by whichever comes first: its own matching closing brace,
    or the START of the next declaration found in pass 1. That second bound
    is what keeps an outer `@Component`'s "provides" list from double-
    counting a nested `@Module`'s bindings — verified against a real
    Component-wraps-Module file (6 `@BindsInstance` builder methods + 8
    `@Binds` methods on the nested module: the outer Component correctly
    gets 0 provides, the nested Module gets all 8).
    """
    modules = []

    for root, _dirs, files in os.walk(jadx_sources_dir):
        for fname in files:
            if not fname.endswith(".java"):
                continue
            full = os.path.join(root, fname)
            rel = os.path.relpath(full, jadx_sources_dir)
            with open(full, encoding="utf-8", errors="replace") as f:
                lines = f.readlines()
            n = len(lines)

            # Pass 1: every module/component declaration in this file.
            decls = []
            i = 0
            while i < n:
                m = MODULE_ANNOTATION_RE.match(lines[i])
                if m:
                    class_name = None
                    decl_idx = None
                    limit = min(n, i + 1 + ANNOTATION_LOOKAHEAD_LINES)
                    for j in range(i + 1, limit):
                        cm = CLASS_DECL_RE.search(lines[j])
                        if cm:
                            class_name = cm.group(1)
                            decl_idx = j
                            break
                    if class_name is not None:
                        decls.append(
                            {
                                "ann_idx": i,
                                "decl_idx": decl_idx,
                                "class": class_name,
                                "annotation": "@" + m.group(1),
                            }
                        )
                i += 1

            # Pass 2: provides-window per declaration.
            for idx, d in enumerate(decls):
                start = d["decl_idx"]

                depth = 0
                started = False
                own_end = n
                for k in range(start, n):
                    line = lines[k]
                    depth += line.count("{") - line.count("}")
                    if "{" in line:
                        started = True
                    if started and depth <= 0:
                        own_end = k
                        break

                next_start = decls[idx + 1]["ann_idx"] if idx + 1 < len(decls) else n
                window_end = min(own_end, next_start)

                provides = []
                k = start
                while k < window_end:
                    if BINDING_MARKER_RE.match(lines[k]):
                        name_limit = min(window_end, n, k + METHOD_NAME_LOOKAHEAD_LINES)
                        for p in range(k, name_limit):
                            pm = METHOD_NAME_RE.search(lines[p])
                            if pm:
                                provides.append(pm.group(1))
                                break
                    k += 1

                modules.append(
                    {
                        "file": rel,
                        "line": d["ann_idx"] + 1,
                        "class": d["class"],
                        "annotation": d["annotation"],
                        "provides": provides,
                    }
                )

    return modules


# ---------------------------------------------------------------------------
# 4. Crash keys
# ---------------------------------------------------------------------------

# Only matches a LITERAL first argument — `setCustomKey("name", value)`.
# A call site that passes a variable (`setCustomKey(k, v)`) or the batch form
# (`setCustomKeys(map)`, plural — deliberately NOT matched: no `\s*\(`
# directly after `setCustomKey` when an `s` sits in between) is invisible to
# this heuristic; recovering those key names needs dataflow, out of scope.
CRASH_KEY_RE = re.compile(r'setCustomKey\s*\(\s*"((?:[^"\\]|\\.)*)"')


def extract_crash_keys(jadx_sources_dir):
    keys = []
    for root, _dirs, files in os.walk(jadx_sources_dir):
        for fname in files:
            if not fname.endswith(".java"):
                continue
            full = os.path.join(root, fname)
            rel = os.path.relpath(full, jadx_sources_dir)
            with open(full, encoding="utf-8", errors="replace") as f:
                for lineno, line in enumerate(f, start=1):
                    m = CRASH_KEY_RE.search(line)
                    if m:
                        keys.append({"file": rel, "line": lineno, "key": m.group(1)})
    return keys


# ---------------------------------------------------------------------------
# 5. Design tokens (res/values/colors.xml, res/values/dimens.xml)
# ---------------------------------------------------------------------------

# Only the base res/values/ variant, not values-night/values-v31/etc — matches
# the explicit scope this script was built against. Scanning every locale/
# density/theme variant is a documented non-goal, not a bug.
COLOR_RE = re.compile(r'<color\s+name="([^"]*)"\s*>([^<]*)</color>')
DIMEN_RE = re.compile(r'<dimen\s+name="([^"]*)"\s*>([^<]*)</dimen>')


def _extract_tag_values(apktool_dir, fname, pattern):
    full = os.path.join(apktool_dir, "res", "values", fname)
    if not os.path.isfile(full):
        return []
    rel = os.path.relpath(full, apktool_dir)
    out = []
    with open(full, encoding="utf-8", errors="replace") as f:
        for lineno, line in enumerate(f, start=1):
            m = pattern.search(line)
            if m:
                out.append(
                    {"name": m.group(1), "value": m.group(2).strip(), "file": rel, "line": lineno}
                )
    return out


def extract_design_tokens(apktool_dir):
    return {
        "colors": _extract_tag_values(apktool_dir, "colors.xml", COLOR_RE),
        "dimens": _extract_tag_values(apktool_dir, "dimens.xml", DIMEN_RE),
    }


# ---------------------------------------------------------------------------
# Aggregate
# ---------------------------------------------------------------------------


def harvest(jadx_sources_dir, apktool_dir):
    fields, bc_files, bc_secrets, bc_names = extract_build_config(jadx_sources_dir)
    nsc = extract_network_security_config(apktool_dir)
    modules = extract_di_modules(jadx_sources_dir)
    crash_keys = extract_crash_keys(jadx_sources_dir)
    tokens = extract_design_tokens(apktool_dir)

    domains_total = sum(len(dc["domains"]) for dc in nsc["domain_configs"])
    pins_total = sum(
        len(dc["pin_set"]["pins"]) for dc in nsc["domain_configs"] if dc["pin_set"] is not None
    )
    di_bindings_total = sum(len(m["provides"]) for m in modules)

    return {
        "summary": {
            "build_config_files_scanned": bc_files,
            "build_config_fields_total": len(fields),
            "build_config_secrets_redacted": bc_secrets,
            "build_config_secret_names_flagged": bc_names,
            "network_security_config_found": nsc["found"],
            "network_security_config_domain_configs_total": len(nsc["domain_configs"]),
            "network_security_config_domains_total": domains_total,
            "network_security_config_pins_total": pins_total,
            "di_modules_total": len(modules),
            "di_bindings_total": di_bindings_total,
            "crash_keys_total": len(crash_keys),
            "design_tokens_colors_total": len(tokens["colors"]),
            "design_tokens_dimens_total": len(tokens["dimens"]),
        },
        "build_config": fields,
        "network_security_config": nsc,
        "di_modules": modules,
        "crash_keys": crash_keys,
        "design_tokens": tokens,
    }


def main():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("jadx_sources_dir")
    parser.add_argument("apktool_dir")
    parser.add_argument(
        "--out",
        default="data/harvest.json",
        help='Output path (default data/harvest.json). Pass "" to print to stdout instead.',
    )
    args = parser.parse_args()

    result = harvest(args.jadx_sources_dir, args.apktool_dir)
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
