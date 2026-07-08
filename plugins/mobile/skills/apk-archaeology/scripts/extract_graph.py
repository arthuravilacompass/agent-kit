#!/usr/bin/env python3
# desc: grafo de dependência (estilo Lakos) entre classes de negócio (spec §5 [4])
"""extract_graph.py — Dimensão C do apk-archaeology (design §5 [4]).

Grafo de referência (extends/implements) SÓ entre classes em pacotes
business-candidate. É uma RECONSTRUÇÃO via regex sobre Java decompilado pelo jadx,
não um parser real — carrega os artefatos de decompilador documentados na spec
(generics apagados, classes sintéticas tipo $ExternalSyntheticLambda0, símbolos que
o R8 mesclou/inlineou). Edges pra tipos fora do conjunto de classes descobertas
(framework, lib externa) são descartados — não é grafo de todas as dependências,
só das internas ao código de negócio.

Assimetria deliberada com extract_endpoints.py: aqui só business-candidate entra
(unclassifiable nunca vira node de grafo de módulo — ver spec §5 [4]).

Stdlib puro. Determinístico.

Uso:
  python3 extract_graph.py <sources_dir> <classify_json> [--out <path>]
"""
import argparse
import json
import os
import re
import sys

CLASS_DECL_RE = re.compile(
    r"\b(?:public|private|protected|abstract|final|static|\s)*"
    r"(?:class|interface|enum)\s+(\w+)"
    r"(?:<[^>]*>)?"
    r"(?:\s+extends\s+([\w.,\s<>]+?))?"
    r"(?:\s+implements\s+([\w.,\s<>]+))?"
    r"\s*\{"
)

SYNTHETIC_RE = re.compile(r"\$[A-Za-z0-9_]*(Lambda|Synthetic)")


def business_dirs(classify_result):
    return {
        key
        for key, info in classify_result["packages"].items()
        if info["bucket"] == "business-candidate"
    }


def simple_name(qualified):
    return qualified.strip().split(".")[-1].split("<")[0].strip()


def parse_file(path):
    with open(path, encoding="utf-8", errors="replace") as f:
        content = f.read()
    declarations = []
    for m in CLASS_DECL_RE.finditer(content):
        class_name, extends, implements = m.group(1), m.group(2), m.group(3)
        interfaces = []
        if implements:
            interfaces = [simple_name(i) for i in implements.split(",") if i.strip()]
        # extends admite múltiplos pais: classe só tem 1 na prática, mas interface
        # Java permite `interface Foo extends A, B` — tratamos os dois com a mesma
        # lista (achado de revisão: capturar só 1 fazia o match INTEIRO falhar
        # quando havia vírgula, derrubando o node e todas as edges dele, sem aviso)
        parents = [simple_name(e) for e in extends.split(",") if e.strip()] if extends else []
        declarations.append((class_name, parents, interfaces))
    return declarations


def extract_graph(sources_dir, classify_result):
    business = business_dirs(classify_result)
    all_classes = set()
    raw_edges = []
    artifact_warnings = []

    for pkg_key in sorted(business):
        pkg_dir = os.path.join(sources_dir, pkg_key)
        if not os.path.isdir(pkg_dir):
            continue
        for root, _dirs, files in os.walk(pkg_dir):
            for fname in files:
                if not fname.endswith(".java"):
                    continue
                if SYNTHETIC_RE.search(fname):
                    artifact_warnings.append(f"classe sintética ignorada: {fname}")
                    continue
                full = os.path.join(root, fname)
                for class_name, parents, interfaces in parse_file(full):
                    all_classes.add(class_name)
                    for parent in parents:
                        raw_edges.append((class_name, parent, "extends"))
                    for iface in interfaces:
                        raw_edges.append((class_name, iface, "implements"))

    edges = [
        {"from": f, "to": t, "kind": k}
        for (f, t, k) in sorted(set(raw_edges))
        if t in all_classes
    ]

    return {
        "nodes": sorted(all_classes),
        "edges": edges,
        "artifact_warnings": sorted(set(artifact_warnings)),
    }


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

    result = extract_graph(args.sources_dir, classify_result)
    output = json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False)

    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(output + "\n")
    else:
        print(output)


if __name__ == "__main__":
    main()
