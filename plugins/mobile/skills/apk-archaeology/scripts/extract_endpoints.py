#!/usr/bin/env python3
# desc: extrai endpoints de código decompilado com redação de segredo obrigatória (spec §5 [3])
"""extract_endpoints.py — Dimensão B do apk-archaeology (design §5 [3]).

Extrai strings literais de URL de (business-candidate ∪ unclassifiable), excluindo
known-third-party. Cada endpoint é tagueado pela proveniência do pacote onde foi
achado. Qualquer string de alta entropia ou formato de chave conhecido é redigida
ANTES de qualquer coisa ir pro output — nunca aparece o valor literal (spec §7).

Limitação documentada: não deduz segredo EMBUTIDO dentro de uma URL (ex. query
string com api_key=...) — só literais isolados. Cobertura de padrão de chave é
uma lista curada pequena, não uma ferramenta de scanning de segredo dedicada.

Stdlib puro. Determinístico.

Uso:
  python3 extract_endpoints.py <sources_dir> <classify_json> [--out <path>]
"""
import argparse
import hashlib
import json
import math
import os
import re
import sys

URL_RE = re.compile(r"^(https?://[^\s\\]+)$")
STRING_LITERAL_RE = re.compile(r'"((?:[^"\\]|\\.)*)"')

KEY_PATTERNS = [
    re.compile(r"^AKIA[0-9A-Z]{16}$"),  # AWS access key
    re.compile(r"^AIza[0-9A-Za-z_\-]{35}$"),  # Google API key
    re.compile(r"^sk_(live|test)_[0-9A-Za-z]{16,}$"),  # Stripe
    re.compile(r"^ghp_[0-9A-Za-z]{36}$"),  # GitHub token
    re.compile(r"^xox[baprs]-[0-9A-Za-z-]{10,}$"),  # Slack token
]


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


def allowed_packages(classify_result):
    return {
        key
        for key, info in classify_result["packages"].items()
        if info["bucket"] != "known-third-party"
    }


def tag_for_rel_pkg(rel_pkg, classify_result):
    best_match = None
    for key, info in classify_result["packages"].items():
        if rel_pkg == key or rel_pkg.startswith(key + "/") or rel_pkg.startswith(key + os.sep):
            if best_match is None or len(key) > len(best_match[0]):
                best_match = (key, info)
    if best_match is None:
        return None
    bucket = best_match[1]["bucket"]
    if bucket == "known-third-party":
        return None
    return "business" if bucket == "business-candidate" else "unclassifiable"


def extract(sources_dir, classify_result):
    endpoints = []
    secrets_redacted = 0

    for root, _dirs, files in os.walk(sources_dir):
        for fname in files:
            if not fname.endswith(".java"):
                continue
            full = os.path.join(root, fname)
            rel = os.path.relpath(full, sources_dir)
            rel_pkg = os.path.dirname(rel).replace(os.sep, "/")
            tag = tag_for_rel_pkg(rel_pkg, classify_result)
            if tag is None:
                continue

            with open(full, encoding="utf-8", errors="replace") as f:
                for lineno, line in enumerate(f, start=1):
                    for m in STRING_LITERAL_RE.finditer(line):
                        literal = m.group(1)
                        url_match = URL_RE.match(literal)
                        if url_match:
                            endpoints.append(
                                {
                                    "url": url_match.group(1),
                                    "file": rel,
                                    "line": lineno,
                                    "tag": tag,
                                }
                            )
                            continue
                        if looks_like_secret(literal):
                            secrets_redacted += 1

    seen = set()
    unique = []
    for e in sorted(endpoints, key=lambda e: (e["url"], e["file"], e["line"])):
        key = (e["url"], e["file"], e["line"])
        if key not in seen:
            seen.add(key)
            unique.append(e)

    return {"endpoints": unique, "secrets_redacted": secrets_redacted}


def main():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("sources_dir")
    parser.add_argument("classify_json")
    parser.add_argument("--out", default=None)
    args = parser.parse_args()

    with open(args.classify_json, encoding="utf-8") as f:
        classify_result = json.load(f)

    result = extract(args.sources_dir, classify_result)
    output = json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False)

    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(output + "\n")
    else:
        print(output)


if __name__ == "__main__":
    main()
