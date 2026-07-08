#!/usr/bin/env python3
# desc: extrai endpoints de código decompilado com redação de segredo obrigatória (spec §5 [3])
"""extract_endpoints.py — Dimensão B do apk-archaeology (design §5 [3]).

Extrai strings literais de URL de (business-candidate ∪ unclassifiable), excluindo
known-third-party. Cada endpoint é tagueado pela proveniência do pacote onde foi
achado. Qualquer string de alta entropia ou formato de chave conhecido é redigida
ANTES de qualquer coisa ir pro output — nunca aparece o valor literal (spec §7).

Limitação documentada: os 5 formatos de chave conhecida (KEY_PATTERNS) são buscados
de forma NÃO-ANCORADA na URL inteira — sobrevivem à fusão com qualquer caractere
adjacente (ponto, hífen, underscore, etc). A heurística de entropia, por outro lado,
só roda sobre tokens ISOLADOS (delimitados por / ? & = : @) e é fundamentalmente
contornável por fusão — um segredo genérico (sem formato conhecido) fundido a texto
de baixa entropia pode escapar dela. Isso é aceito como limitação best-effort desta
heurística, não perseguido com mais delimitadores.

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

DELIM_CHARS = "/?&=:@"


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
                            url = url_match.group(1)

                            # Pass 1: unanchored search for KNOWN KEY FORMATS across the
                            # whole raw URL, independent of tokenization. This is robust
                            # against fusion with any adjacent character (a delimiter-based
                            # split can never close this — see module docstring).
                            redacted_count = 0
                            for pattern in KEY_PATTERNS:
                                unanchored_src = pattern.pattern.strip("^$")
                                unanchored = re.compile(unanchored_src)
                                matches = list(unanchored.finditer(url))
                                for match in reversed(matches):
                                    url = url[: match.start()] + "[REDACTED]" + url[match.end():]
                                    redacted_count += 1

                            # Pass 2: entropy heuristic on ISOLATED tokens only (best-effort,
                            # documented limitation — can be defeated by fusing a secret with
                            # adjacent in-charset, non-delimiter characters like '.', '-', '_';
                            # this branch does not attempt to close that gap, see docstring).
                            parts = re.split(f"([{DELIM_CHARS}])", url)
                            redacted_parts = []
                            for part in parts:
                                if re.match(f"[{DELIM_CHARS}]", part):
                                    redacted_parts.append(part)
                                elif "[REDACTED]" in part:
                                    # Pass 1 already redacted a known-key match somewhere
                                    # inside this token — still entropy-check the residual
                                    # (non-redacted) text fused to it, so a distinct
                                    # high-entropy secret glued directly onto the redacted
                                    # span isn't skipped entirely (round-4 review regression:
                                    # skipping the whole token let a fused generic secret leak).
                                    fragments = part.split("[REDACTED]")
                                    checked = []
                                    for frag in fragments:
                                        if frag and looks_like_secret(frag):
                                            redacted_count += 1
                                            checked.append("[REDACTED]")
                                        else:
                                            checked.append(frag)
                                    redacted_parts.append("[REDACTED]".join(checked))
                                elif looks_like_secret(part):
                                    redacted_count += 1
                                    redacted_parts.append("[REDACTED]")
                                else:
                                    redacted_parts.append(part)

                            redacted_url = "".join(redacted_parts)
                            secrets_redacted += redacted_count

                            endpoints.append(
                                {
                                    "url": redacted_url,
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
