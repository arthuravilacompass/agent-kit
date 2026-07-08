#!/usr/bin/env python3
# desc: gradeia fidelidade de endpoints.json contra o repo-fonte REAL (spec §9, não-circular)
"""grade_fidelity.py — scorecard da Dimensão B (design §9/§10).

Compara os endpoints extraídos do APK decompilado contra as URLs literais que
existem de fato no repositório-fonte real (clone git, não o output do próprio
compound) — grading não-circular. O gabarito TEM que vir de um clone real do
repo-fonte, nunca da árvore decompilada pelo próprio pipeline.

Limitações conhecidas (achadas na demo v0, não corrigidas nesta rodada — ver design
doc, seção Lições da demo):
- `URL_RE` não distingue string literal de comentário Javadoc (`<a href="...">`
  tem aspas igual a um literal de código) — o gabarito pode incluir URL nunca
  compilada. Correção manual foi necessária na demo v0; não codificada aqui.
- `real_urls()` NUNCA redige o que lê do source real antes de persistir em
  `--out` — diferente de `extract_endpoints.py` (5 rounds de hardening de
  redação, spec §7). Se `real_source_dir` for código de cliente real (não
  público como neste demo), um segredo no source vira segredo no scorecard
  persistido. Sem trigger real na demo (NewPipe é público), mas real em uso
  contra fonte de cliente — candidato a fix antes de reuso fora de demo.

Stdlib puro.

Uso:
  python3 grade_fidelity.py <endpoints_json> <real_source_dir> [--out <path>]
"""
import argparse
import json
import os
import re
import sys

URL_RE = re.compile(r'"(https?://[^"\s\\]+)"')


def real_urls(real_source_dir):
    urls = set()
    for root, dirs, files in os.walk(real_source_dir):
        if ".git" in dirs:
            dirs.remove(".git")
        for fname in files:
            if not (fname.endswith(".java") or fname.endswith(".kt")):
                continue
            full = os.path.join(root, fname)
            with open(full, encoding="utf-8", errors="replace") as f:
                for line in f:
                    for m in URL_RE.finditer(line):
                        urls.add(m.group(1))
    return urls


def grade(endpoints_json_path, real_source_dir):
    with open(endpoints_json_path, encoding="utf-8") as f:
        extracted = json.load(f)

    extracted_urls = {e["url"] for e in extracted["endpoints"]}
    truth_urls = real_urls(real_source_dir)

    true_positive = extracted_urls & truth_urls
    false_positive = extracted_urls - truth_urls
    false_negative = truth_urls - extracted_urls

    recall = (len(true_positive) / len(truth_urls)) if truth_urls else None

    return {
        "extracted_count": len(extracted_urls),
        "real_count": len(truth_urls),
        "true_positive_count": len(true_positive),
        "false_positive_count": len(false_positive),
        "false_negative_count": len(false_negative),
        "recall": recall,
        "false_positives": sorted(false_positive),
        "false_negatives": sorted(false_negative),
    }


def main():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("endpoints_json")
    parser.add_argument("real_source_dir")
    parser.add_argument("--out", default=None)
    args = parser.parse_args()

    result = grade(args.endpoints_json, args.real_source_dir)
    output = json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False)

    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(output + "\n")
    else:
        print(output)


if __name__ == "__main__":
    main()
