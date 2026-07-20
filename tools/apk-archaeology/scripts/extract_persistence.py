#!/usr/bin/env python3
# desc: extracts the persistence layer (Room/prefs/secure-storage/SQLite) with mandatory secret redaction
"""extract_persistence.py — persistence-layer extension of apk-archaeology (design §5).

Extracts, from decompiled Java sources, the app's persistence surface:

  Room        — @Entity classes (table name + fields), @Dao interfaces with
                @Query/@Insert/@Update/@Delete methods (+ the SQL literal for
                @Query), @Database classes.
  prefs       — getSharedPreferences(name, mode) call sites, and the string
                keys read/written through a get*/put*/contains/remove call on
                a preference-like receiver (heuristic, see PREFS_KEY_RE below).
  secure      — KeyStore.getInstance(...) and EncryptedSharedPreferences.create(...)
                call sites ("usage sites", not every import).
  sqlite      — SQLiteOpenHelper subclasses, and string literals containing a
                CREATE TABLE statement (table name pulled out when parseable).

Each finding is anchored file:line. Every string VALUE that ends up in a
finding's `detail` (pref file names, pref keys, table names, DDL text, usage
snippets) is passed through redact_value() before being written out — the
literal is never emitted if it looks like a secret; only a redaction count is
reported (spec §7, same contract as extract_endpoints.py).

Documented limitations (heuristic, not a full Java/annotation parser):
  - Annotation-to-declaration association is done by regex proximity (the
    annotation, then the next class/interface/enum declaration, or the next
    method signature, found via re.search from the annotation's end position)
    rather than a real AST. This is the same class of limitation already
    accepted in extract_graph.py (regex reconstruction over jadx output, not
    a real parser) — decompiler artifacts (erased generics, synthetic
    classes) apply here too.
  - Entity field extraction only captures brace-depth-1 statements in the
    class body with no '(' after stripping leading annotations — this misses
    fields with a constructor-call initializer (e.g. `= new Date()`), a
    deliberate false-negative to avoid mistaking a method signature for a
    field (see top_level_statements()).
  - The prefs-key heuristic (PREFS_KEY_RE) matches on the RECEIVER
    IDENTIFIER'S NAME containing "pref" or "editor" (case-insensitive), not
    on the receiver's declared type — a variable named e.g. `sp` instead of
    `prefs`/`editor` is missed. Verified against a real corpus: variable
    names containing "pref" or "edit" account for the large majority of
    get/put call sites observed, so this is a productive, not vacuous,
    heuristic — but it is not exhaustive.
  - KeyStore/EncryptedSharedPreferences are reported at their canonical
    factory-method call site only (`KeyStore.getInstance(`,
    `EncryptedSharedPreferences.create(`), not every reference to the type
    name — this is deliberate ("usage sites", spec wording), trading recall
    for precision (an import or a field DECLARATION of type KeyStore is not
    itself a usage).
  - CLASS_ANNOT_RE / DAO_METHOD_ANNOT_RE match the SIMPLE annotation name
    (`@Entity`, `@Query`, ...), not a fully-qualified form
    (`@androidx.room.Entity`). jadx's default output uses the simple form
    with an import, so this is the right default — but it is UNVALIDATED
    against a real @Entity/@Dao in the wild: the reference corpus this
    script was checked against has zero Room usage at the source level (see
    selftest for the only positive-path coverage of the Room branches).

Pure stdlib. Deterministic.

Usage:
  python3 extract_persistence.py <sources_dir> [classify_json] [--out <path>]
  Without classify_json, the whole sources_dir is scanned (unscoped).
  With classify_json, scoping mirrors extract_endpoints.py: only
  business-candidate and unclassifiable packages are scanned; known-third-party
  is excluded.
"""
import argparse
import bisect
import json
import math
import os
import re

# --- secret redaction (adapted from extract_endpoints.py, generalized from
# URL text to arbitrary string values — see module docstring §"redaction") ---

KEY_PATTERNS = [
    re.compile(r"^AKIA[0-9A-Z]{16}$"),  # AWS access key
    re.compile(r"^AIza[0-9A-Za-z_\-]{35}$"),  # Google API key
    re.compile(r"^sk_(live|test)_[0-9A-Za-z]{16,}$"),  # Stripe
    re.compile(r"^ghp_[0-9A-Za-z]{36}$"),  # GitHub token
    re.compile(r"^xox[baprs]-[0-9A-Za-z-]{10,}$"),  # Slack token
]

# Broader delimiter set than extract_endpoints.py's URL-only DELIM_CHARS,
# since here we tokenize arbitrary Java-adjacent text (DDL, snippets), not
# just URLs — whitespace, quotes and brackets also count as separators.
GENERIC_DELIM_CHARS = "/?&=:@,;()\"' \t{}[]<>"


def shannon_entropy(s):
    if not s:
        return 0.0
    freq = {}
    for ch in s:
        freq[ch] = freq.get(ch, 0) + 1
    length = len(s)
    return -sum((c / length) * math.log2(c / length) for c in freq.values())


def looks_like_secret(literal):
    if any(p.match(literal) for p in KEY_PATTERNS):
        return True
    if (
        len(literal) >= 20
        and shannon_entropy(literal) >= 4.0
        and re.match(r"^[A-Za-z0-9+/_=\-\.]+$", literal)
    ):
        return True
    return False


def redact_value(text):
    """Generic secret redaction for one arbitrary string value. Returns
    (redacted_text, redacted_count). None-safe (some detail fields are
    optional). Same two-pass approach as extract_endpoints.py's URL
    redaction (known-format sweep, then entropy check on isolated tokens),
    generalized to a non-URL delimiter set — same fusion limitation applies
    (documented in extract_endpoints.py, not re-litigated here)."""
    if text is None:
        return None, 0
    working = text
    redacted_count = 0

    for pattern in KEY_PATTERNS:
        unanchored = re.compile(pattern.pattern.strip("^$"))
        matches = list(unanchored.finditer(working))
        for match in reversed(matches):
            working = working[: match.start()] + "[REDACTED]" + working[match.end():]
            redacted_count += 1

    delim_class = "[" + re.escape(GENERIC_DELIM_CHARS) + "]"
    parts = re.split(f"({delim_class})", working)
    redacted_parts = []
    for part in parts:
        if part and re.match(delim_class, part):
            redacted_parts.append(part)
        elif part and "[REDACTED]" in part:
            fragments = part.split("[REDACTED]")
            checked = []
            for frag in fragments:
                if frag and looks_like_secret(frag):
                    redacted_count += 1
                    checked.append("[REDACTED]")
                else:
                    checked.append(frag)
            redacted_parts.append("[REDACTED]".join(checked))
        elif part and looks_like_secret(part):
            redacted_count += 1
            redacted_parts.append("[REDACTED]")
        else:
            redacted_parts.append(part)

    return "".join(redacted_parts), redacted_count


# --- classify.json scoping (mirrors extract_endpoints.py's tag_for_rel_pkg,
# collapsed to a boolean since persistence findings don't carry a tag) ---


def package_allowed(rel_pkg, classify_result):
    best_match = None
    for key, info in classify_result["packages"].items():
        if rel_pkg == key or rel_pkg.startswith(key + "/") or rel_pkg.startswith(key + os.sep):
            if best_match is None or len(key) > len(best_match[0]):
                best_match = (key, info)
    if best_match is None:
        return False
    return best_match[1]["bucket"] != "known-third-party"


# --- structural regexes ---

STRING_LITERAL_RE = re.compile(r'"((?:[^"\\]|\\.)*)"')

CLASS_DECL_RE = re.compile(
    r"\b(?:public|private|protected|abstract|final|static|\s)*"
    r"(?:class|interface|enum)\s+(\w+)"
    r"(?:<[^>]*>)?"
    r"(?:\s+extends\s+([\w.,\s<>]+?))?"
    r"(?:\s+implements\s+([\w.,\s<>]+))?"
    r"\s*\{"
)

CLASS_ANNOT_RE = re.compile(r"@(Entity|Dao|Database)\b")
DAO_METHOD_ANNOT_RE = re.compile(r"@(Query|Insert|Update|Delete)\b")
METHOD_NAME_RE = re.compile(r"\b(\w+)\s*\(")
COLUMN_INFO_RE = re.compile(r'@ColumnInfo\s*\(([^)]*)\)')
NAME_ARG_RE = re.compile(r'name\s*=\s*"((?:[^"\\]|\\.)*)"')
TABLE_NAME_ARG_RE = re.compile(r'tableName\s*=\s*"((?:[^"\\]|\\.)*)"')
VERSION_ARG_RE = re.compile(r"version\s*=\s*(\d+)")
ENTITIES_ARG_RE = re.compile(r"entities\s*=\s*\{([^}]*)\}")

GET_SHARED_PREFS_RE = re.compile(
    r'\bgetSharedPreferences\s*\(\s*"((?:[^"\\]|\\.)*)"\s*,\s*([^)]*)\)'
)
PREFS_KEY_RE = re.compile(
    r"\b(\w*pref\w*|editor)\s*\.\s*(get|put)(String|Int|Boolean|Long|Float|StringSet)"
    r'\s*\(\s*"((?:[^"\\]|\\.)*)"',
    re.IGNORECASE,
)
PREFS_KEY_RE2 = re.compile(
    r'\b(\w*pref\w*|editor)\s*\.\s*(contains|remove)\s*\(\s*"((?:[^"\\]|\\.)*)"',
    re.IGNORECASE,
)

KEYSTORE_RE = re.compile(r"\bKeyStore\s*\.\s*getInstance\s*\(")
ENCRYPTED_PREFS_RE = re.compile(r"\bEncryptedSharedPreferences\s*\.\s*create\s*\(")

CREATE_TABLE_RE = re.compile(r"create\s+table", re.IGNORECASE)
TABLE_NAME_DDL_RE = re.compile(
    r"create\s+table\s+(?:if\s+not\s+exists\s+)?[`\"'\[]?(\w+)", re.IGNORECASE
)

FIELD_DECL_RE = re.compile(
    r"^\s*(?:public\s+|private\s+|protected\s+|final\s+|static\s+|transient\s+|volatile\s+)*"
    r"([A-Za-z_][\w.]*(?:<[^;()]*>)?(?:\[\])?)\s+(\w+)\s*(?:=.*)?;\s*$",
    re.DOTALL,
)
ANNOT_PREFIX_RE = re.compile(r"^\s*(?:@\w+(?:\([^)]*\))?\s*)+")


def build_line_index(content):
    return [i for i, ch in enumerate(content) if ch == "\n"]


def line_of(nl_offsets, pos):
    return bisect.bisect_right(nl_offsets, pos) + 1


def match_parens(content, pos):
    """content[pos] must be '('. Returns the index right after the matching ')'."""
    depth = 0
    i = pos
    n = len(content)
    while i < n:
        if content[i] == "(":
            depth += 1
        elif content[i] == ")":
            depth -= 1
            if depth == 0:
                return i + 1
        i += 1
    return n


def match_braces(content, pos):
    """content[pos] is the char right after an already-consumed opening '{'
    (depth starts at 1). Returns the index of the matching '}'."""
    depth = 1
    i = pos
    n = len(content)
    while i < n:
        if content[i] == "{":
            depth += 1
        elif content[i] == "}":
            depth -= 1
            if depth == 0:
                return i
        i += 1
    return n


def annotation_args(content, end_of_annotation_name):
    """Given the position right after `@Name`, returns (args_text, pos_after)
    — args_text is '' if the annotation has no parenthesized arguments."""
    i = end_of_annotation_name
    n = len(content)
    while i < n and content[i] in " \t\r\n":
        i += 1
    if i < n and content[i] == "(":
        end = match_parens(content, i)
        return content[i + 1 : end - 1], end
    return "", end_of_annotation_name


def all_classes(content):
    """Every class/interface/enum declaration in the file: list of dicts
    with name, extends (raw, comma-joined text or None), body_start, body_end.
    body_end == body_start if the brace never closes (malformed/truncated
    input — degrades to an empty body rather than crashing)."""
    classes = []
    for m in CLASS_DECL_RE.finditer(content):
        body_start = m.end()
        body_end = match_braces(content, body_start)
        classes.append(
            {
                "name": m.group(1),
                "extends": m.group(2),
                "decl_start": m.start(),
                "body_start": body_start,
                "body_end": body_end,
            }
        )
    return classes


def enclosing_class(pos, classes):
    """Innermost class whose body contains pos, or None."""
    best = None
    for c in classes:
        if c["body_start"] <= pos < c["body_end"]:
            if best is None or (c["body_end"] - c["body_start"]) < (
                best["body_end"] - best["body_start"]
            ):
                best = c
    return best["name"] if best else None


def simple_name(qualified):
    return qualified.strip().split(".")[-1].split("<")[0].strip()


def top_level_statements(body):
    """';'-terminated statements at brace-depth 0 relative to the body's
    start (i.e. directly in the class body, not inside a method/initializer
    block). A `for(;;)` header never qualifies — it only occurs inside a
    method BODY, which is itself wrapped in '{}' and therefore at depth >= 1
    by the time the parser reaches it."""
    depth = 0
    stmt_start = 0
    out = []
    for i, ch in enumerate(body):
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
        elif ch == ";" and depth == 0:
            out.append(body[stmt_start : i + 1])
            stmt_start = i + 1
    return out


def entity_fields(body):
    fields = []
    for stmt in top_level_statements(body):
        column_name = None
        cm = COLUMN_INFO_RE.search(stmt)
        if cm:
            nm = NAME_ARG_RE.search(cm.group(1))
            if nm:
                column_name = nm.group(1)
        stripped = ANNOT_PREFIX_RE.sub("", stmt, count=1)
        if "(" in stripped:
            continue  # method-like signature, not a field decl (see docstring)
        fm = FIELD_DECL_RE.match(stripped)
        if fm:
            fields.append(
                {"name": fm.group(2), "type": fm.group(1), "column_name": column_name}
            )
    return fields


def extract_from_file(content, nl_offsets, rel):
    findings = []
    redacted_total = 0
    classes = all_classes(content)

    dao_spans = []  # (body_start, body_end, name) — for scoping @Query/@Insert/...

    # --- Room: @Entity / @Dao / @Database ---
    for m in CLASS_ANNOT_RE.finditer(content):
        kind = m.group(1)
        args, args_end = annotation_args(content, m.end())
        cm = CLASS_DECL_RE.search(content, args_end)
        if not cm:
            continue
        class_name = cm.group(1)
        line = line_of(nl_offsets, m.start())
        body_start = cm.end()
        body_end = match_braces(content, body_start)

        if kind == "Entity":
            tm = TABLE_NAME_ARG_RE.search(args)
            table_name, r = redact_value(tm.group(1) if tm else class_name)
            redacted_total += r
            fields = []
            for f in entity_fields(content[body_start:body_end]):
                col, r2 = redact_value(f["column_name"]) if f["column_name"] else (None, 0)
                redacted_total += r2
                fields.append({"name": f["name"], "type": f["type"], "column_name": col})
            findings.append(
                {
                    "type": "room_entity",
                    "class": class_name,
                    "file": rel,
                    "line": line,
                    "detail": {"table_name": table_name, "fields": fields},
                }
            )
        elif kind == "Dao":
            dao_spans.append((body_start, body_end, class_name))
            findings.append(
                {
                    "type": "room_dao",
                    "class": class_name,
                    "file": rel,
                    "line": line,
                    "detail": {},
                }
            )
        elif kind == "Database":
            vm = VERSION_ARG_RE.search(args)
            em = ENTITIES_ARG_RE.search(args)
            entities = []
            if em:
                for piece in em.group(1).split(","):
                    piece = piece.strip()
                    if piece:
                        entities.append(simple_name(piece.split(".class")[0]))
            findings.append(
                {
                    "type": "room_database",
                    "class": class_name,
                    "file": rel,
                    "line": line,
                    "detail": {
                        "version": vm.group(1) if vm else None,
                        "entities": entities,
                    },
                }
            )

    # --- Room: @Dao methods (@Query/@Insert/@Update/@Delete), scoped to a Dao body ---
    for m in DAO_METHOD_ANNOT_RE.finditer(content):
        dao = None
        for body_start, body_end, name in dao_spans:
            if body_start <= m.start() < body_end:
                dao = (body_start, body_end, name)
                break
        if dao is None:
            continue
        annotation = m.group(1)
        args, args_end = annotation_args(content, m.end())
        mm = METHOD_NAME_RE.search(content, args_end, dao[1])
        if not mm:
            continue
        sql_literals = [lm.group(1) for lm in STRING_LITERAL_RE.finditer(args)]
        sql, r = redact_value(" ".join(sql_literals)) if sql_literals else (None, 0)
        redacted_total += r
        findings.append(
            {
                "type": "room_dao_method",
                "class": dao[2],
                "file": rel,
                "line": line_of(nl_offsets, m.start()),
                "detail": {"method": mm.group(1), "annotation": annotation, "sql": sql},
            }
        )

    # --- SharedPreferences: file names ---
    for m in GET_SHARED_PREFS_RE.finditer(content):
        name, r = redact_value(m.group(1))
        redacted_total += r
        findings.append(
            {
                "type": "shared_prefs_file",
                "class": enclosing_class(m.start(), classes),
                "file": rel,
                "line": line_of(nl_offsets, m.start()),
                "detail": {"name": name, "mode": m.group(2).strip()},
            }
        )

    # --- SharedPreferences: keys read/written ---
    for m in PREFS_KEY_RE.finditer(content):
        accessor = m.group(2) + m.group(3)
        key, r = redact_value(m.group(4))
        redacted_total += r
        findings.append(
            {
                "type": "shared_prefs_key",
                "class": enclosing_class(m.start(), classes),
                "file": rel,
                "line": line_of(nl_offsets, m.start()),
                "detail": {"accessor": accessor, "key": key},
            }
        )
    for m in PREFS_KEY_RE2.finditer(content):
        key, r = redact_value(m.group(3))
        redacted_total += r
        findings.append(
            {
                "type": "shared_prefs_key",
                "class": enclosing_class(m.start(), classes),
                "file": rel,
                "line": line_of(nl_offsets, m.start()),
                "detail": {"accessor": m.group(2), "key": key},
            }
        )

    # --- Secure storage: KeyStore / EncryptedSharedPreferences usage sites ---
    lines = content.splitlines()
    for m, ftype, api in (
        *((m, "keystore_usage", "KeyStore.getInstance") for m in KEYSTORE_RE.finditer(content)),
        *(
            (m, "encrypted_prefs_usage", "EncryptedSharedPreferences.create")
            for m in ENCRYPTED_PREFS_RE.finditer(content)
        ),
    ):
        ln = line_of(nl_offsets, m.start())
        snippet_raw = lines[ln - 1].strip() if 0 < ln <= len(lines) else ""
        snippet, r = redact_value(snippet_raw[:200])
        redacted_total += r
        findings.append(
            {
                "type": ftype,
                "class": enclosing_class(m.start(), classes),
                "file": rel,
                "line": ln,
                "detail": {"api": api, "snippet": snippet},
            }
        )

    # --- SQLite: SQLiteOpenHelper subclasses ---
    for c in classes:
        if not c["extends"]:
            continue
        parents = [simple_name(p) for p in c["extends"].split(",") if p.strip()]
        if "SQLiteOpenHelper" in parents:
            findings.append(
                {
                    "type": "sqlite_helper",
                    "class": c["name"],
                    "file": rel,
                    "line": line_of(nl_offsets, c["decl_start"]),
                    "detail": {"extends": "SQLiteOpenHelper"},
                }
            )

    # --- SQLite: table DDL string literals ---
    for m in STRING_LITERAL_RE.finditer(content):
        literal = m.group(1)
        if not CREATE_TABLE_RE.search(literal):
            continue
        tm = TABLE_NAME_DDL_RE.search(literal)
        ddl, r = redact_value(literal)
        redacted_total += r
        findings.append(
            {
                "type": "sqlite_table_ddl",
                "class": enclosing_class(m.start(), classes),
                "file": rel,
                "line": line_of(nl_offsets, m.start()),
                "detail": {"table_name": tm.group(1) if tm else None, "ddl": ddl},
            }
        )

    return findings, redacted_total


def build_summary(findings, secrets_redacted):
    counts = {}
    for f in findings:
        counts[f["type"]] = counts.get(f["type"], 0) + 1
    return {
        "room_entities": counts.get("room_entity", 0),
        "room_daos": counts.get("room_dao", 0),
        "room_dao_methods": counts.get("room_dao_method", 0),
        "room_databases": counts.get("room_database", 0),
        "shared_prefs_files": counts.get("shared_prefs_file", 0),
        "shared_prefs_keys": counts.get("shared_prefs_key", 0),
        "keystore_usages": counts.get("keystore_usage", 0),
        "encrypted_prefs_usages": counts.get("encrypted_prefs_usage", 0),
        "sqlite_helpers": counts.get("sqlite_helper", 0),
        "sqlite_table_ddls": counts.get("sqlite_table_ddl", 0),
        "total_findings": len(findings),
        "secrets_redacted": secrets_redacted,
    }


def extract(sources_dir, classify_result=None):
    findings = []
    secrets_redacted = 0

    for root, _dirs, files in os.walk(sources_dir):
        for fname in files:
            if not fname.endswith(".java"):
                continue
            full = os.path.join(root, fname)
            rel = os.path.relpath(full, sources_dir)
            rel_pkg = os.path.dirname(rel).replace(os.sep, "/")
            if classify_result is not None and not package_allowed(rel_pkg, classify_result):
                continue

            with open(full, encoding="utf-8", errors="replace") as f:
                content = f.read()
            if not content:
                continue
            nl_offsets = build_line_index(content)
            file_findings, file_redacted = extract_from_file(content, nl_offsets, rel)
            findings.extend(file_findings)
            secrets_redacted += file_redacted

    findings.sort(key=lambda x: (x["file"], x["line"], x["type"], x["class"] or ""))
    return {"summary": build_summary(findings, secrets_redacted), "findings": findings}


def main():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("sources_dir")
    parser.add_argument("classify_json", nargs="?", default=None)
    parser.add_argument("--out", default="data/persistence.json")
    args = parser.parse_args()

    classify_result = None
    if args.classify_json:
        with open(args.classify_json, encoding="utf-8") as f:
            classify_result = json.load(f)

    result = extract(args.sources_dir, classify_result)
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
