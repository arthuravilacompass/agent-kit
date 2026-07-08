#!/usr/bin/env python3
# desc: classifica pacotes de uma árvore jadx decompilada em 3 baldes (spec §5 [2])
"""classify_packages.py — Dimensão de suporte do apk-archaeology (design §5 [2]).

Classifica cada pacote de topo (ou, para namespaces compartilhados como com/org/br,
o primeiro segmento NÃO-compartilhado) em 3 baldes:
  known-third-party   — casou known-libs.json
  business-candidate  — nome de pacote real e distintivo, não casou lib conhecida
  unclassifiable      — pacote de 1-2 letras (padrão de flatten do R8/ProGuard);
                        pode ser negócio real OU lib renomeada, não dá pra saber
                        (ver §6 da spec — fragilidade documentada, não bug)

LIMITAÇÃO CONHECIDA (verificada contra NewPipe real, §6 da spec): o regex de
ofuscação também gera falso-positivo em app LIMPO quando um pacote real usa
prefixo curto estilo ccTLD (ex.: `us.shandian.giga`, uma lib real, virou
`unclassifiable`). Efeito assimétrico: inofensivo na Dimensão B (endpoint
ainda extraído, só tag menos precisa); perda real na Dimensão C (classe fica
fora do grafo). Não é bug de lógica — é a mesma fragilidade de fingerprint
por nome já documentada, só que na direção oposta (falso-positivo, não só
falso-negativo).

Stdlib puro. Determinístico: mesma árvore + mesmo known-libs.json = mesmo output.

Uso:
  python3 classify_packages.py <sources_dir> <known_libs_json> [--out <path>]
  Sem --out, imprime JSON no stdout.
"""
import argparse
import json
import os
import re
import sys

OBFUSCATED_RE = re.compile(r"^[a-z]{1,2}[0-9]?$")
SHARED_ROOTS = {"com", "org", "br", "io", "net", "de", "jp", "co"}
MAX_SHARED_ROOT_DEPTH = 4  # guarda contra estrutura anômala/loop


def load_known_libs(path):
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    entries = []
    for lib in data["libraries"]:
        for prefix in lib["prefixes"]:
            entries.append((tuple(prefix.split(".")), lib["name"]))
    return entries


def match_known_lib(segments, known_libs):
    seg_tuple = tuple(segments)
    for prefix_segments, lib_name in known_libs:
        if seg_tuple == prefix_segments:
            return lib_name
    return None


def classify(sources_dir, known_libs):
    packages = {}

    def walk(dir_path, segments):
        for entry in sorted(os.listdir(dir_path)):
            full = os.path.join(dir_path, entry)
            if not os.path.isdir(full):
                continue
            new_segments = segments + [entry]
            if entry in SHARED_ROOTS and len(new_segments) < MAX_SHARED_ROOT_DEPTH:
                walk(full, new_segments)
                continue
            key = "/".join(new_segments)
            lib = match_known_lib(new_segments, known_libs)
            if lib:
                packages[key] = {"bucket": "known-third-party", "matched_lib": lib}
            elif OBFUSCATED_RE.match(entry):
                packages[key] = {"bucket": "unclassifiable", "matched_lib": None}
            else:
                packages[key] = {"bucket": "business-candidate", "matched_lib": None}

    walk(sources_dir, [])
    return {"packages": packages}


def main():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("sources_dir")
    parser.add_argument("known_libs_json")
    parser.add_argument("--out", default=None)
    args = parser.parse_args()

    known_libs = load_known_libs(args.known_libs_json)
    result = classify(args.sources_dir, known_libs)
    output = json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False)

    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(output + "\n")
    else:
        print(output)


if __name__ == "__main__":
    main()
