# apk-archaeology (v0 provisional) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Construir a skill provisional `apk-archaeology` no plugin `mobile` do agent-kit — um pipeline que extrai fluxos/regras de negócio (A), contratos de API (B) e grafo de módulo (C) de um APK Android legado decompilado, com bandas de confiança explícitas — e produzir uma demo real rodada (v0) que prova viabilidade com números de fidelidade medidos, não fabricados.

**Architecture:** Harness (Claude Code) + Orchestration (`SKILL.md`, sequência fixa de 6 passos) + scripts determinísticos Python/stdlib puro pra classificação/extração/grafo (zero LLM) + 1 fan-out de agentes só pra síntese da Dimensão A. Grading de fidelidade é não-circular (gabarito vem do repo-fonte real do NewPipe, nunca do próprio output).

**Tech Stack:** Python 3 stdlib puro (sem dependências externas — segue convenção do resto do agent-kit), Bash, `jadx` + `apktool` como binários externos (checados no PATH, não vendorizados).

**Insumo:** `docs/superpowers/specs/2026-07-08-apk-archaeology-design.md` (17 seções, aprovado pelo usuário).

## Global Constraints

- **3 baldes de classificação**, nunca binário: `known-third-party` / `business-candidate` / `unclassifiable` (spec §5, §6).
- **3 bandas de confiança**, nunca achatadas no mesmo nível na consolidação: B=fato · C=reconstrução (com ressalva de artefato) · A=inferência tiered (spec §5 [6]).
- **Redação de segredo obrigatória**: todo match de alta entropia/formato de chave conhecido nunca aparece como valor literal em nenhum output persistido (spec §7).
- **Regra de âncora**: regra de negócio sintetizada sem evidência determinística (string/endpoint/entry point) sai como `unanchored`, nunca como inferência de baixa confiança disfarçada (spec §5 [5], §11.1).
- **`unclassifiable` nunca é tratado como lógica de negócio** pelo agente de síntese (spec §5 [5]).
- **Grading de fidelidade não-circular**: gabarito vem do repo-fonte real (clone git), nunca do próprio output decompilado do compound (spec §9).
- **Governança de publicação**: NewPipe (GPLv3) é shareable com fonte ao lado. "Telecorp" (pseudônimo) — só estatística agregada sobre a ferramenta é shareable; conteúdo extraído (endpoint real, domínio real, nome de pacote real) é interno, nunca em exemplo (spec §8).
- **Zero números de ROI/produtividade/tempo-economizado** no v0 — sem baseline, seria fabricado (spec §10, §13).
- **`SKILL.md` marca STATUS: provisional** — não é `wired` (spec §3).
- Todo script Python é **stdlib puro**, sem pytest — segue convenção existente do repo (`generate_inventory.py`, `arch_violations.py`): teste é um script companheiro `selftest_*.py` com `assert` + exit code, rodado diretamente.

---

### Task 1: `classify_packages.py` + `known-libs.json` — classificação em 3 baldes

**Files:**
- Create: `plugins/mobile/skills/apk-archaeology/scripts/known-libs.json`
- Create: `plugins/mobile/skills/apk-archaeology/scripts/classify_packages.py`
- Test: `plugins/mobile/skills/apk-archaeology/scripts/selftest_classify_packages.py`

**Interfaces:**
- Produces: `classify(sources_dir: str, known_libs: list[tuple[tuple[str,...], str]]) -> dict` retornando `{"packages": {"<chave/de/pacote>": {"bucket": "known-third-party"|"business-candidate"|"unclassifiable", "matched_lib": str|None}}}`. CLI: `python3 classify_packages.py <sources_dir> <known_libs_json> [--out <path>]`.
- Regra de granularidade: pacotes sob namespace compartilhado (`com`/`org`/`br`/`io`/`net`/`de`/`jp`/`co`) são classificados no primeiro segmento NÃO-compartilhado (ex.: `br/com/zup/vivoeasy3` → chave `br/com/zup`); os demais, no primeiro segmento (ex.: `androidx` → chave `androidx`).

- [ ] **Step 1: Criar `known-libs.json`**

```bash
mkdir -p ~/dev/agent-kit/plugins/mobile/skills/apk-archaeology/scripts
```

Criar `plugins/mobile/skills/apk-archaeology/scripts/known-libs.json`:

```json
{
  "libraries": [
    {"name": "Kotlin stdlib", "prefixes": ["kotlin"]},
    {"name": "Kotlin coroutines", "prefixes": ["kotlinx"]},
    {"name": "AndroidX", "prefixes": ["androidx"]},
    {"name": "Android framework", "prefixes": ["android"]},
    {"name": "OkHttp", "prefixes": ["okhttp3"]},
    {"name": "Okio", "prefixes": ["okio"]},
    {"name": "Retrofit", "prefixes": ["retrofit2"]},
    {"name": "Ktor", "prefixes": ["io.ktor"]},
    {"name": "RxJava", "prefixes": ["io.reactivex"]},
    {"name": "Dagger/Hilt", "prefixes": ["dagger"]},
    {"name": "Javax inject", "prefixes": ["javax.inject"]},
    {"name": "Koin", "prefixes": ["org.koin"]},
    {"name": "Google (Firebase/GMS/Protobuf)", "prefixes": ["com.google"]},
    {"name": "Squareup (Retrofit deps/Moshi/Picasso)", "prefixes": ["com.squareup"]},
    {"name": "Glide", "prefixes": ["com.bumptech"]},
    {"name": "Lottie", "prefixes": ["com.airbnb"]},
    {"name": "ButterKnife", "prefixes": ["butterknife"]},
    {"name": "EventBus", "prefixes": ["org.greenrobot"]},
    {"name": "Timber", "prefixes": ["timber"]},
    {"name": "Coil", "prefixes": ["coil"]},
    {"name": "Protocol Buffers runtime", "prefixes": ["com.google.protobuf"]},
    {"name": "JUnit", "prefixes": ["junit"]},
    {"name": "JUnit (org)", "prefixes": ["org.junit"]},
    {"name": "Jetbrains annotations", "prefixes": ["org.jetbrains"]},
    {"name": "Facebook SDK", "prefixes": ["com.facebook"]},
    {"name": "Adjust attribution", "prefixes": ["com.adjust"]},
    {"name": "ClearSale antifraude", "prefixes": ["br.com.clearsale"]}
  ]
}
```

> Nota: prefixos com 2 segmentos (ex. `com.google`) só funcionam corretamente porque `com`/`org`/`io`/`br` estão em `SHARED_ROOTS` no script — a classificação para nesses casos exatamente no 2º segmento. Ver §6 da spec: isto é fingerprint por nome, frágil sob ofuscação pesada por design — não é bug, é a limitação documentada.

- [ ] **Step 2: Escrever o teste (falha primeiro)**

Criar `plugins/mobile/skills/apk-archaeology/scripts/selftest_classify_packages.py`:

```python
#!/usr/bin/env python3
"""selftest_classify_packages.py — fixture sintética, sem dependência de APK real."""
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(__file__))
from classify_packages import classify, load_known_libs  # noqa: E402


def make_fixture(base):
    # obfuscado (1-2 letras): unclassifiable
    os.makedirs(os.path.join(base, "a"))
    os.makedirs(os.path.join(base, "ci"))
    # lib conhecida direta: known-third-party
    os.makedirs(os.path.join(base, "androidx"))
    os.makedirs(os.path.join(base, "kotlin"))
    # lib conhecida sob namespace compartilhado: known-third-party
    os.makedirs(os.path.join(base, "com", "google"))
    # negócio real sob namespace compartilhado triplo: business-candidate
    os.makedirs(os.path.join(base, "br", "com", "zup"))
    # negócio real direto: business-candidate
    os.makedirs(os.path.join(base, "org", "schabi"))


def write_known_libs(path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump({
            "libraries": [
                {"name": "AndroidX", "prefixes": ["androidx"]},
                {"name": "Kotlin stdlib", "prefixes": ["kotlin"]},
                {"name": "Google", "prefixes": ["com.google"]},
            ]
        }, f)


def main():
    with tempfile.TemporaryDirectory() as tmp:
        sources = os.path.join(tmp, "sources")
        os.makedirs(sources)
        make_fixture(sources)

        libs_path = os.path.join(tmp, "known-libs.json")
        write_known_libs(libs_path)

        known_libs = load_known_libs(libs_path)
        result = classify(sources, known_libs)
        packages = result["packages"]

        assert packages["a"]["bucket"] == "unclassifiable", packages["a"]
        assert packages["ci"]["bucket"] == "unclassifiable", packages["ci"]
        assert packages["androidx"]["bucket"] == "known-third-party", packages["androidx"]
        assert packages["androidx"]["matched_lib"] == "AndroidX"
        assert packages["kotlin"]["bucket"] == "known-third-party", packages["kotlin"]
        assert packages["com/google"]["bucket"] == "known-third-party", packages["com/google"]
        assert packages["br/com/zup"]["bucket"] == "business-candidate", packages["br/com/zup"]
        assert packages["org/schabi"]["bucket"] == "business-candidate", packages["org/schabi"]

    print("OK: 7/7 asserções passaram")


if __name__ == "__main__":
    main()
```

- [ ] **Step 3: Rodar o teste, confirmar que falha (classify_packages.py ainda não existe)**

Run: `python3 plugins/mobile/skills/apk-archaeology/scripts/selftest_classify_packages.py`
Expected: `ModuleNotFoundError: No module named 'classify_packages'`

- [ ] **Step 4: Implementar `classify_packages.py`**

Criar `plugins/mobile/skills/apk-archaeology/scripts/classify_packages.py`:

```python
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
```

- [ ] **Step 5: Rodar o teste, confirmar que passa**

Run: `python3 plugins/mobile/skills/apk-archaeology/scripts/selftest_classify_packages.py`
Expected: `OK: 7/7 asserções passaram`

- [ ] **Step 6: Commit**

```bash
cd ~/dev/agent-kit
git add plugins/mobile/skills/apk-archaeology/scripts/known-libs.json \
        plugins/mobile/skills/apk-archaeology/scripts/classify_packages.py \
        plugins/mobile/skills/apk-archaeology/scripts/selftest_classify_packages.py
git commit -m "feat(mobile): add apk-archaeology package classifier (3-bucket)"
```

---

### Task 2: `extract_endpoints.py` — Dimensão B com redação de segredo obrigatória

**Files:**
- Create: `plugins/mobile/skills/apk-archaeology/scripts/extract_endpoints.py`
- Test: `plugins/mobile/skills/apk-archaeology/scripts/selftest_extract_endpoints.py`

**Interfaces:**
- Consumes: output de `classify()` (Task 1) — dict `{"packages": {...}}`.
- Produces: `extract(sources_dir: str, classify_result: dict) -> dict` retornando `{"endpoints": [{"url": str, "file": str, "line": int, "tag": "business"|"unclassifiable"}], "secrets_redacted": int}`. CLI: `python3 extract_endpoints.py <sources_dir> <classify_json> [--out <path>]`.

- [ ] **Step 1: Escrever o teste (falha primeiro)**

Criar `plugins/mobile/skills/apk-archaeology/scripts/selftest_extract_endpoints.py`:

```python
#!/usr/bin/env python3
"""selftest_extract_endpoints.py — fixture com URL real, secret sintético, e lib excluída."""
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(__file__))
from extract_endpoints import extract  # noqa: E402

CLASSIFY_RESULT = {
    "packages": {
        "br/com/zup/app": {"bucket": "business-candidate", "matched_lib": None},
        "a": {"bucket": "unclassifiable", "matched_lib": None},
        "androidx": {"bucket": "known-third-party", "matched_lib": "AndroidX"},
    }
}


def write(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def main():
    with tempfile.TemporaryDirectory() as tmp:
        sources = os.path.join(tmp, "sources")

        # business-candidate: tem URL real (deve aparecer, tag=business)
        write(
            os.path.join(sources, "br/com/zup/app/Api.java"),
            'package br.com.zup.app;\n'
            'public class Api {\n'
            '    String base = "https://api.example.com.br/v1/login";\n'
            '    String key = "AKIAABCDEFGHIJKLMNOP";\n'
            '}\n',
        )
        # unclassifiable: também tem URL (deve aparecer, tag=unclassifiable)
        write(
            os.path.join(sources, "a/b.java"),
            'package a;\n'
            'public class b {\n'
            '    String u = "https://sdk.thirdparty.io/track";\n'
            '}\n',
        )
        # known-third-party: NUNCA deve aparecer, mesmo tendo URL
        write(
            os.path.join(sources, "androidx/x/Y.java"),
            'package androidx.x;\n'
            'public class Y {\n'
            '    String u = "https://androidx.internal.example/should-not-appear";\n'
            '}\n',
        )

        result = extract(sources, CLASSIFY_RESULT)
        urls = {e["url"] for e in result["endpoints"]}

        assert "https://api.example.com.br/v1/login" in urls, urls
        assert "https://sdk.thirdparty.io/track" in urls, urls
        assert "https://androidx.internal.example/should-not-appear" not in urls, urls

        by_url = {e["url"]: e for e in result["endpoints"]}
        assert by_url["https://api.example.com.br/v1/login"]["tag"] == "business"
        assert by_url["https://sdk.thirdparty.io/track"]["tag"] == "unclassifiable"

        assert result["secrets_redacted"] == 1, result["secrets_redacted"]
        raw_json = json.dumps(result)
        assert "AKIAABCDEFGHIJKLMNOP" not in raw_json, "SEGREDO VAZOU NO OUTPUT"

    print("OK: todas as asserções passaram (URLs corretas, lib excluída, segredo redigido)")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Rodar o teste, confirmar que falha**

Run: `python3 plugins/mobile/skills/apk-archaeology/scripts/selftest_extract_endpoints.py`
Expected: `ModuleNotFoundError: No module named 'extract_endpoints'`

- [ ] **Step 3: Implementar `extract_endpoints.py`**

Criar `plugins/mobile/skills/apk-archaeology/scripts/extract_endpoints.py`:

```python
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
```

- [ ] **Step 4: Rodar o teste, confirmar que passa**

Run: `python3 plugins/mobile/skills/apk-archaeology/scripts/selftest_extract_endpoints.py`
Expected: `OK: todas as asserções passaram (URLs corretas, lib excluída, segredo redigido)`

- [ ] **Step 5: Commit**

```bash
cd ~/dev/agent-kit
git add plugins/mobile/skills/apk-archaeology/scripts/extract_endpoints.py \
        plugins/mobile/skills/apk-archaeology/scripts/selftest_extract_endpoints.py
git commit -m "feat(mobile): add apk-archaeology endpoint extractor with secret redaction"
```

---

### Task 3: `extract_graph.py` — Dimensão C (grafo de módulo, reconstrução)

**Files:**
- Create: `plugins/mobile/skills/apk-archaeology/scripts/extract_graph.py`
- Test: `plugins/mobile/skills/apk-archaeology/scripts/selftest_extract_graph.py`

**Interfaces:**
- Consumes: output de `classify()` (Task 1).
- Produces: `extract_graph(sources_dir: str, classify_result: dict) -> dict` retornando `{"nodes": [str], "edges": [{"from": str, "to": str, "kind": "extends"|"implements"}], "artifact_warnings": [str]}`. CLI: `python3 extract_graph.py <sources_dir> <classify_json> [--out <path>]`.

- [ ] **Step 1: Escrever o teste (falha primeiro)**

Criar `plugins/mobile/skills/apk-archaeology/scripts/selftest_extract_graph.py`:

```python
#!/usr/bin/env python3
"""selftest_extract_graph.py — fixture com extends/implements e uma classe sintética."""
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(__file__))
from extract_graph import extract_graph  # noqa: E402

CLASSIFY_RESULT = {
    "packages": {
        "br/com/zup/app": {"bucket": "business-candidate", "matched_lib": None},
        "a": {"bucket": "unclassifiable", "matched_lib": None},
    }
}


def write(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def main():
    with tempfile.TemporaryDirectory() as tmp:
        sources = os.path.join(tmp, "sources")

        write(
            os.path.join(sources, "br/com/zup/app/BaseActivity.java"),
            "package br.com.zup.app;\n"
            "public abstract class BaseActivity {\n}\n",
        )
        write(
            os.path.join(sources, "br/com/zup/app/LoginActivity.java"),
            "package br.com.zup.app;\n"
            "public class LoginActivity extends BaseActivity implements Callback {\n}\n",
        )
        write(
            os.path.join(sources, "br/com/zup/app/Callback.java"),
            "package br.com.zup.app;\n"
            "public interface Callback {\n}\n",
        )
        # classe sintética: deve ser ignorada, gerar warning, não virar node/edge
        write(
            os.path.join(sources, "br/com/zup/app/LoginActivity$$ExternalSyntheticLambda0.java"),
            "package br.com.zup.app;\n"
            "public class LoginActivity$$ExternalSyntheticLambda0 extends BaseActivity {\n}\n",
        )
        # unclassifiable: fora do escopo do grafo, nunca deve aparecer como node
        write(
            os.path.join(sources, "a/b.java"),
            "package a;\n"
            "public class b extends c {\n}\n",
        )

        result = extract_graph(sources, CLASSIFY_RESULT)

        assert "LoginActivity" in result["nodes"], result["nodes"]
        assert "BaseActivity" in result["nodes"], result["nodes"]
        assert "Callback" in result["nodes"], result["nodes"]
        assert "b" not in result["nodes"], "classe de pacote unclassifiable vazou pro grafo"

        edges = {(e["from"], e["to"], e["kind"]) for e in result["edges"]}
        assert ("LoginActivity", "BaseActivity", "extends") in edges, edges
        assert ("LoginActivity", "Callback", "implements") in edges, edges

        assert any("ExternalSyntheticLambda0" in w for w in result["artifact_warnings"]), result[
            "artifact_warnings"
        ]
        assert not any(
            n.startswith("LoginActivity$") for n in result["nodes"]
        ), "classe sintética não filtrada"

    print("OK: todas as asserções passaram (edges corretos, unclassifiable excluído, sintética filtrada)")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Rodar o teste, confirmar que falha**

Run: `python3 plugins/mobile/skills/apk-archaeology/scripts/selftest_extract_graph.py`
Expected: `ModuleNotFoundError: No module named 'extract_graph'`

- [ ] **Step 3: Implementar `extract_graph.py`**

Criar `plugins/mobile/skills/apk-archaeology/scripts/extract_graph.py`:

```python
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
    r"(?:\s+extends\s+([\w.]+)(?:<[^>]*>)?)?"
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
        parent = simple_name(extends) if extends else None
        declarations.append((class_name, parent, interfaces))
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
                for class_name, parent, interfaces in parse_file(full):
                    all_classes.add(class_name)
                    if parent:
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
```

- [ ] **Step 4: Rodar o teste, confirmar que passa**

Run: `python3 plugins/mobile/skills/apk-archaeology/scripts/selftest_extract_graph.py`
Expected: `OK: todas as asserções passaram (edges corretos, unclassifiable excluído, sintética filtrada)`

- [ ] **Step 5: Commit**

```bash
cd ~/dev/agent-kit
git add plugins/mobile/skills/apk-archaeology/scripts/extract_graph.py \
        plugins/mobile/skills/apk-archaeology/scripts/selftest_extract_graph.py
git commit -m "feat(mobile): add apk-archaeology module dependency graph extractor"
```

---

### Task 4: `decompile.sh` — orquestração jadx + apktool

**Files:**
- Create: `plugins/mobile/skills/apk-archaeology/scripts/decompile.sh`

**Interfaces:**
- Produces: `<dir_saida>/jadx/sources/*.java`, `<dir_saida>/apktool/AndroidManifest.xml` + `res/`. CLI: `decompile.sh <caminho.apk> <dir_saida>`.

- [ ] **Step 1: Implementar `decompile.sh`**

Criar `plugins/mobile/skills/apk-archaeology/scripts/decompile.sh`:

```bash
#!/usr/bin/env bash
# desc: orquestra jadx + apktool sobre um APK (spec §5 [1])
set -euo pipefail

if [[ $# -lt 2 ]]; then
  echo "uso: decompile.sh <caminho.apk> <dir_saida>" >&2
  exit 1
fi

APK="$1"
OUT="$2"

if ! command -v jadx >/dev/null 2>&1; then
  echo "ERRO: jadx não encontrado no PATH." >&2
  echo "Instale: brew install jadx" >&2
  echo "  ou baixe o release direto: https://github.com/skylot/jadx/releases/latest" >&2
  exit 1
fi

if ! command -v apktool >/dev/null 2>&1; then
  echo "ERRO: apktool não encontrado no PATH." >&2
  echo "Instale: brew install apktool" >&2
  exit 1
fi

if [[ ! -f "$APK" ]]; then
  echo "ERRO: APK não encontrado: $APK" >&2
  exit 1
fi

mkdir -p "$OUT"

echo "[1/2] jadx (source legível)..." >&2
jadx -d "$OUT/jadx" --no-res -j 4 "$APK" 2>&1 | tail -5

echo "[2/2] apktool (manifest/resources)..." >&2
apktool d "$APK" -o "$OUT/apktool" -f >/dev/null 2>&1

CLASS_COUNT=$(find "$OUT/jadx/sources" -name "*.java" | wc -l | tr -d ' ')
echo "OK: $CLASS_COUNT classes em $OUT/jadx/sources; manifest em $OUT/apktool/AndroidManifest.xml" >&2
```

```bash
chmod +x plugins/mobile/skills/apk-archaeology/scripts/decompile.sh
```

- [ ] **Step 2: Testar contra um APK real da lab (NewPipe, já disponível)**

Run:
```bash
cd ~/dev/agent-kit
bash plugins/mobile/skills/apk-archaeology/scripts/decompile.sh \
  ~/dev/apk-archaeology-lab/samples/newpipe.apk \
  ~/dev/apk-archaeology-lab/decompile-test-run
```
Expected: última linha `OK: <N> classes em .../jadx/sources; manifest em .../apktool/AndroidManifest.xml` (N próximo de 3423, do spike anterior — pode variar levemente por diferença de flags `--no-res`).

- [ ] **Step 3: Limpar a saída de teste (não é fixture permanente)**

```bash
rm -rf ~/dev/apk-archaeology-lab/decompile-test-run
```

- [ ] **Step 4: Commit**

```bash
cd ~/dev/agent-kit
git add plugins/mobile/skills/apk-archaeology/scripts/decompile.sh
git commit -m "feat(mobile): add apk-archaeology jadx+apktool orchestration script"
```

---

### Task 5: `SKILL.md` — definição de orquestração da skill

**Files:**
- Create: `plugins/mobile/skills/apk-archaeology/SKILL.md`

**Interfaces:**
- Consumes: nomes/contratos exatos de `classify_packages.py`, `extract_endpoints.py`, `extract_graph.py`, `decompile.sh` (Tasks 1-4).
- Produces: nada programático — é o documento de orquestração que o Harness (Claude Code) segue.

- [ ] **Step 1: Criar `SKILL.md`**

Criar `plugins/mobile/skills/apk-archaeology/SKILL.md`:

```markdown
---
name: apk-archaeology
description: "STATUS: provisional — invoque para extrair valor de um APK Android legado (descompilado) rumo a uma migração pra Flutter: fluxos/regras de negócio, contratos de API, grafo de módulo, com bandas de confiança explícitas. Não wired — refinar após primeiro uso real."
disable-model-invocation: true
---

# apk-archaeology — Extração de valor de APK legado (provisional)

> **STATUS: provisional/experimental.** Template de consolidação e contrato de handoff
> são refinados após o primeiro uso real num cliente — ver design doc:
> `docs/superpowers/specs/2026-07-08-apk-archaeology-design.md`.

Extrai 3 dimensões de um APK Android legado — fluxos/regras de negócio (A), contratos
de API (B), grafo de módulo (C) — como insumo pra migração nativo→Flutter. Adapta o
padrão do `core:archaeology` (dispatch paralelo por dimensão → consolidação estruturada)
pra uma fonte compilada/possivelmente ofuscada em vez de código-fonte vivo.

## Quando Usar

Você tem um `.apk` de um app legado que vai (ou pode vir a) ser migrado pra Flutter, e
quer uma spec candidata + contratos de API + fronteiras de módulo antes de planejar a
migração. Não é análise de segurança/malware — é preparação de migração.

## Input

Caminho pra um arquivo `.apk`.

## Steps

### 1. Decompilar

```
scripts/decompile.sh <caminho.apk> <dir_trabalho>
```

Produz `<dir_trabalho>/jadx/sources/` (Java legível) e `<dir_trabalho>/apktool/`
(manifest/resources).

### 2. Classificar pacotes

```
python3 scripts/classify_packages.py <dir_trabalho>/jadx/sources scripts/known-libs.json --out <dir_trabalho>/classify.json
```

3 baldes: `known-third-party` / `business-candidate` / `unclassifiable`. Ver design
doc §6 pra por que `unclassifiable` existe e não é opcional.

### 3. Extrair endpoints (Dimensão B — fato)

```
python3 scripts/extract_endpoints.py <dir_trabalho>/jadx/sources <dir_trabalho>/classify.json --out <dir_trabalho>/endpoints.json
```

Roda sobre `business-candidate ∪ unclassifiable`. Redação de segredo é automática —
confira `secrets_redacted` no output; se > 0, **não** exponha o `endpoints.json` bruto
fora do ambiente local antes de confirmar que nenhum literal vazou (grep manual como
segunda checagem é aceitável nesta fase provisional).

### 4. Extrair grafo de módulo (Dimensão C — reconstrução)

```
python3 scripts/extract_graph.py <dir_trabalho>/jadx/sources <dir_trabalho>/classify.json --out <dir_trabalho>/graph.json
```

Só sobre `business-candidate`. Note `artifact_warnings` no output — classes sintéticas
filtradas são esperadas, não bug.

### 5. Síntese da Dimensão A (agente — fan-out)

Particione `graph.json` em unidades de trabalho (componente conexo do grafo é o método
mais simples pra v0 — duas classes ligadas por edge caem na mesma partição; classes
sem edge formam partições de 1). Para CADA partição, dispare um agente com este
contexto:

- As classes da partição (código-fonte de `jadx/sources/<pacote>/`).
- Endpoints de `endpoints.json` que citam arquivos dessa partição.
- Entry points nomeados (Activities/Fragments/ViewModels do manifest ou reconhecíveis
  por convenção de nome) e string resources de `apktool/res/values/strings.xml`, como
  âncora.

Instrua o agente: sintetize fluxos/regras de negócio observáveis nesta partição. Toda
regra citada em `arquivo:linha`. **Regra de âncora**: se não conseguir amarrar uma
regra numa string, endpoint ou entry point concreto, marque como `unanchored` — não
maquie como inferência de baixa confiança normal. Nunca trate classes de pacote
`unclassifiable` como lógica de negócio.

### 6. Consolidar

Uma síntese, 3 bandas SEMPRE separadas visualmente, nunca achatadas:

```markdown
## Proveniência
- Input: <nome do apk> · <hash sha256> · versões jadx/apktool · wall-clock · máquina

## B — Contratos de API (fato)
[lista de endpoints com tag business/unclassifiable, arquivo:linha]

## C — Grafo de módulo (reconstrução — ver artifact_warnings)
[resumo do grafo: clusters, acoplamento, nós sintéticos filtrados]

## A — Fluxos e regras de negócio (inferência tiered)
[por partição: regras com tier de confiança + arquivo:linha; unanchored destacado à parte]

## O que isto NÃO é
[ver design doc §10 — não mede produtividade, comportamento legado ≠ aprovado,
 regra de baixa frequência pode ter sido esquecida, etc.]
```

## Regras invioláveis

- `unclassifiable` nunca é tratado como lógica de negócio pelo agente (passo 5).
- Toda string de alta entropia/formato de chave conhecido é redigida antes de qualquer
  output persistido (passo 3) — nunca o valor literal.
- As 3 bandas de confiança nunca são achatadas no mesmo nível na consolidação (passo 6).
- Regra sem âncora concreta sai como `unanchored`, não como inferência normal.
- Conteúdo extraído de APK de terceiro sem autorização (não o cliente atual) nunca sai
  do ambiente local — ver design doc §8 (governança de publicação).
```

- [ ] **Step 2: Validar o plugin**

Run: `claude plugin validate ~/dev/agent-kit/plugins/mobile`
Expected: saída sem erro de schema pra `apk-archaeology/SKILL.md` (frontmatter válido).

- [ ] **Step 3: Commit**

```bash
cd ~/dev/agent-kit
git add plugins/mobile/skills/apk-archaeology/SKILL.md
git commit -m "feat(mobile): add apk-archaeology SKILL.md orchestration (provisional)"
```

---

### Task 6: `grade_fidelity.py` — scorecard não-circular da Dimensão B

**Files:**
- Create: `plugins/mobile/skills/apk-archaeology/scripts/grade_fidelity.py`
- Test: `plugins/mobile/skills/apk-archaeology/scripts/selftest_grade_fidelity.py`

**Interfaces:**
- Consumes: output de `extract()` (Task 2) via arquivo JSON; diretório de um clone git real (não decompilado).
- Produces: `grade(endpoints_json_path: str, real_source_dir: str) -> dict` com `{"extracted_count", "real_count", "true_positive_count", "false_positive_count", "false_negative_count", "recall", "false_positives": [...], "false_negatives": [...]}`.

- [ ] **Step 1: Escrever o teste (falha primeiro)**

Criar `plugins/mobile/skills/apk-archaeology/scripts/selftest_grade_fidelity.py`:

```python
#!/usr/bin/env python3
"""selftest_grade_fidelity.py — fixture com 1 acerto, 1 falso-positivo, 1 falso-negativo."""
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(__file__))
from grade_fidelity import grade  # noqa: E402


def write(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def main():
    with tempfile.TemporaryDirectory() as tmp:
        endpoints_path = os.path.join(tmp, "endpoints.json")
        with open(endpoints_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "endpoints": [
                        {"url": "https://real.example.com/a", "file": "x", "line": 1, "tag": "business"},
                        {"url": "https://falso-positivo.example.com/b", "file": "x", "line": 2, "tag": "business"},
                    ],
                    "secrets_redacted": 0,
                },
                f,
            )

        real_source = os.path.join(tmp, "real_source")
        write(
            os.path.join(real_source, "App.java"),
            'String a = "https://real.example.com/a";\n'
            'String c = "https://falso-negativo.example.com/c";\n',
        )

        result = grade(endpoints_path, real_source)

        assert result["true_positive_count"] == 1, result
        assert result["false_positive_count"] == 1, result
        assert "https://falso-positivo.example.com/b" in result["false_positives"], result
        assert result["false_negative_count"] == 1, result
        assert "https://falso-negativo.example.com/c" in result["false_negatives"], result
        assert result["recall"] == 0.5, result["recall"]

    print("OK: recall/falso-positivo/falso-negativo calculados corretamente")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Rodar o teste, confirmar que falha**

Run: `python3 plugins/mobile/skills/apk-archaeology/scripts/selftest_grade_fidelity.py`
Expected: `ModuleNotFoundError: No module named 'grade_fidelity'`

- [ ] **Step 3: Implementar `grade_fidelity.py`**

Criar `plugins/mobile/skills/apk-archaeology/scripts/grade_fidelity.py`:

```python
#!/usr/bin/env python3
# desc: gradeia fidelidade de endpoints.json contra o repo-fonte REAL (spec §9, não-circular)
"""grade_fidelity.py — scorecard da Dimensão B (design §9/§10).

Compara os endpoints extraídos do APK decompilado contra as URLs literais que
existem de fato no repositório-fonte real (clone git, não o output do próprio
compound) — grading não-circular. O gabarito TEM que vir de um clone real do
repo-fonte, nunca da árvore decompilada pelo próprio pipeline.

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
```

- [ ] **Step 4: Rodar o teste, confirmar que passa**

Run: `python3 plugins/mobile/skills/apk-archaeology/scripts/selftest_grade_fidelity.py`
Expected: `OK: recall/falso-positivo/falso-negativo calculados corretamente`

- [ ] **Step 5: Commit**

```bash
cd ~/dev/agent-kit
git add plugins/mobile/skills/apk-archaeology/scripts/grade_fidelity.py \
        plugins/mobile/skills/apk-archaeology/scripts/selftest_grade_fidelity.py
git commit -m "feat(mobile): add apk-archaeology non-circular fidelity grader"
```

---

### Task 7: Rodar a demo v0 fim-a-fim e produzir o exemplo

**Files:**
- Create: `plugins/mobile/skills/apk-archaeology/examples/newpipe-demo.md`
- Create (fora de git, na lab — ver spec §15): `~/dev/apk-archaeology-lab/newpipe-source/` (clone real, gabarito)
- Create (fora de git): `~/dev/apk-archaeology-lab/demo-run/` (outputs intermediários da demo)

**Interfaces:**
- Consumes: Tasks 1-6 completas; amostras já em `~/dev/apk-archaeology-lab/samples/{newpipe.apk, vivo-easy.apk}`.
- Produces: `examples/newpipe-demo.md` — artefato shareable (spec §8) com proveniência, mapa tiered em 3 bandas, scorecard de fidelidade com números reais, caixa "o que isto NÃO é".

Este task não é TDD (é execução + curadoria de output) — os critérios de aceite vêm
direto da spec §9.

- [ ] **Step 1: Clonar o repo-fonte real do NewPipe (gabarito não-circular)**

```bash
cd ~/dev/apk-archaeology-lab
git clone --depth 1 --branch v0.28.8 https://github.com/TeamNewPipe/NewPipe.git newpipe-source
```

- [ ] **Step 2: Rodar o pipeline completo (passos 1-4) contra o NewPipe**

```bash
cd ~/dev/agent-kit
mkdir -p ~/dev/apk-archaeology-lab/demo-run/newpipe

bash plugins/mobile/skills/apk-archaeology/scripts/decompile.sh \
  ~/dev/apk-archaeology-lab/samples/newpipe.apk \
  ~/dev/apk-archaeology-lab/demo-run/newpipe

python3 plugins/mobile/skills/apk-archaeology/scripts/classify_packages.py \
  ~/dev/apk-archaeology-lab/demo-run/newpipe/jadx/sources \
  plugins/mobile/skills/apk-archaeology/scripts/known-libs.json \
  --out ~/dev/apk-archaeology-lab/demo-run/newpipe/classify.json

python3 plugins/mobile/skills/apk-archaeology/scripts/extract_endpoints.py \
  ~/dev/apk-archaeology-lab/demo-run/newpipe/jadx/sources \
  ~/dev/apk-archaeology-lab/demo-run/newpipe/classify.json \
  --out ~/dev/apk-archaeology-lab/demo-run/newpipe/endpoints.json

python3 plugins/mobile/skills/apk-archaeology/scripts/extract_graph.py \
  ~/dev/apk-archaeology-lab/demo-run/newpipe/jadx/sources \
  ~/dev/apk-archaeology-lab/demo-run/newpipe/classify.json \
  --out ~/dev/apk-archaeology-lab/demo-run/newpipe/graph.json
```

Expected: os 4 comandos saem sem erro; `endpoints.json` e `graph.json` existem e são JSON válido.

- [ ] **Step 3: Gradear a Dimensão B contra o gabarito real (não-circular)**

```bash
python3 plugins/mobile/skills/apk-archaeology/scripts/grade_fidelity.py \
  ~/dev/apk-archaeology-lab/demo-run/newpipe/endpoints.json \
  ~/dev/apk-archaeology-lab/newpipe-source \
  --out ~/dev/apk-archaeology-lab/demo-run/newpipe/scorecard-b.json

cat ~/dev/apk-archaeology-lab/demo-run/newpipe/scorecard-b.json
```

Expected: JSON com `recall` numérico real (não estimado) e listas de falso-positivo/negativo — **estes números vão pro exemplo tal como saírem, mesmo que o recall não seja perfeito** (spec §10: reportar, não esconder).

- [ ] **Step 4: Síntese da Dimensão A (agente) — manual, com grading humano**

Escolha 2-3 partições do grafo (`graph.json`) que tenham classes reconhecíveis (ex.:
componentes ligados a `MainActivity`, `DownloaderImpl`, alguma feature de subscription).
Para cada uma, invoque um agente seguindo exatamente as instruções do passo 5 do
`SKILL.md` (Task 5). Depois, LEIA o código-fonte real em
`~/dev/apk-archaeology-lab/newpipe-source` pras mesmas classes e classifique cada
claim sintetizada como verdadeiro/falso à mão.

Anote: N claims de alta confiança, M verificados verdadeiros, K falsos, e quantos
saíram `unanchored`. Isso é o número de calibração de A (spec §10) — **se algum claim
de alta confiança for falso, ele entra no exemplo mesmo assim**.

- [ ] **Step 5: Rodar o apêndice da Telecorp (só B+C, sem agente — spec §9)**

```bash
mkdir -p ~/dev/apk-archaeology-lab/demo-run/telecorp

bash plugins/mobile/skills/apk-archaeology/scripts/decompile.sh \
  ~/dev/apk-archaeology-lab/samples/vivo-easy.apk \
  ~/dev/apk-archaeology-lab/demo-run/telecorp

python3 plugins/mobile/skills/apk-archaeology/scripts/classify_packages.py \
  ~/dev/apk-archaeology-lab/demo-run/telecorp/jadx/sources \
  plugins/mobile/skills/apk-archaeology/scripts/known-libs.json \
  --out ~/dev/apk-archaeology-lab/demo-run/telecorp/classify.json

python3 plugins/mobile/skills/apk-archaeology/scripts/extract_endpoints.py \
  ~/dev/apk-archaeology-lab/demo-run/telecorp/jadx/sources \
  ~/dev/apk-archaeology-lab/demo-run/telecorp/classify.json \
  --out ~/dev/apk-archaeology-lab/demo-run/telecorp/endpoints.json
```

Confira, sem imprimir o conteúdo de `endpoints.json` no terminal (é interno — spec §8):

```bash
python3 -c "
import json
d = json.load(open('$HOME/dev/apk-archaeology-lab/demo-run/telecorp/endpoints.json'))
c = json.load(open('$HOME/dev/apk-archaeology-lab/demo-run/telecorp/classify.json'))
buckets = {}
for info in c['packages'].values():
    buckets[info['bucket']] = buckets.get(info['bucket'], 0) + 1
print('secrets_redacted:', d['secrets_redacted'])
print('endpoints (contagem, não conteúdo):', len(d['endpoints']))
print('distribuição de baldes:', buckets)
"
```

Expected: só números agregados impressos — nenhum endpoint/domínio real da Telecorp
aparece no terminal nem em nenhum arquivo fora de `~/dev/apk-archaeology-lab/` (spec §8).

- [ ] **Step 6: Montar `examples/newpipe-demo.md`**

Usar o template de consolidação do `SKILL.md` (Task 5, passo 6), preenchido com os
números REAIS dos steps 2-5 acima. Estrutura obrigatória (spec §10):

```markdown
# apk-archaeology — Demo v0 (NewPipe)

## Proveniência
- Input: NewPipe v0.28.8 (org.schabi.newpipe) — apk público, github.com/TeamNewPipe/NewPipe
- jadx <versão> · apktool <versão> · <data> · <SO/arquitetura>

## B — Contratos de API (fato)
- <N> endpoints extraídos, tag business/unclassifiable
- Scorecard: recall <valor real de scorecard-b.json>, <K> falso-positivo, <M> falso-negativo
  (lista completa em anexo, não neste resumo)

## C — Grafo de módulo (reconstrução)
- <N> nodes, <N> edges, <N> classes sintéticas filtradas (artifact_warnings)

## A — Fluxos e regras de negócio (inferência tiered)
- <N> claims sintetizados nas partições analisadas, <M> verificados verdadeiros contra
  a fonte real, <K> falsos, <J> unanchored
- [claims individuais com arquivo:linha e veredito]

## O que isto NÃO é
- Não mede produtividade — sem baseline, sem migração real.
- Fidelidade medida em referência limpa (NewPipe) — não em código ofuscado (ver
  apêndice Telecorp, dados agregados abaixo).
- Dimensão A demonstrada em referência pobre em regra de negócio (NewPipe é player de
  mídia) — recuperação de regra de negócio real permanece projetada, não medida.
- Inferência de A pode errar mesmo em tier alto — calibrado, não garantido.
- Regra de negócio de baixa frequência é esquecida por design — spec candidata é
  insumo pra reconciliação humana, não substituto dela.

## Apêndice — smoke Telecorp (app comercial real, pseudônimo — spec §8)
- <N>% dos pacotes top-level caíram em `unclassifiable` (ofuscação real)
- <N> segredos potenciais redigidos (nenhum valor literal neste documento)
- Conteúdo extraído (endpoints/domínios reais) NÃO incluído — interno, spec §8
```

- [ ] **Step 7: Conferir critério de aceite da demo (spec §9) linha por linha**

- [ ] Pipeline rodou NewPipe fim-a-fim sem intervenção manual (steps 2-3 acima).
- [ ] Mapa tiered com 3 bandas visualmente distintas no `.md` final.
- [ ] Scorecard com números reais, não estimados.
- [ ] Smoke da Telecorp confirma redação disparando (`secrets_redacted` > 0 OU documentado por que é 0) + zero segredo/endpoint literal no `.md` final + distribuição de baldes reportada.

- [ ] **Step 8: Commit (só o exemplo shareable — nada da Telecorp)**

```bash
cd ~/dev/agent-kit
git add plugins/mobile/skills/apk-archaeology/examples/newpipe-demo.md
git commit -m "docs(mobile): add apk-archaeology v0 demo output (NewPipe, graded)"
```

---

## Self-Review (feito ao gerar este plano)

**Cobertura da spec**: dimensões A/B/C (Tasks 1-3, 7) · decompilação (Task 4) ·
orquestração/SKILL.md (Task 5) · grading não-circular (Task 6) · demo v0 com AC (Task 7)
· redação de segredo (Task 2, testado) · regra de âncora (Task 5, SKILL.md) · governança
Telecorp (Task 7, step 5-6) · status provisional (Task 5, frontmatter). Não coberto
neste plano, deliberadamente (spec §12, v2): análise dinâmica, benchmark com
`mapping.txt` como oráculo — documentados como fora de escopo, não esquecidos.

**Consistência de tipo**: `classify()` retorna `{"packages": {...}}` — usado
identicamente por `extract()` (Task 2) e `extract_graph()` (Task 3). Chave de pacote
(`br/com/zup`, `androidx`) é a mesma convenção nas 3 tasks. Conferido.

**Verificação empírica (não só leitura)**: os 4 scripts (Tasks 1, 2, 3, 6) foram
materializados e rodados de verdade nesta sessão — todos os 4 selftests passam
(`classify_packages`, `extract_endpoints` com confirmação de que o segredo sintético
nunca aparece no JSON serializado, `extract_graph` com confirmação de que a regex de
classe sintética filtra `$$ExternalSyntheticLambda0` via backtracking real, `grade_fidelity`
com recall/falso-positivo/negativo calculados corretamente). `classify_packages.py`
também rodou contra a árvore real decompilada do NewPipe (3423 classes, não fixture) —
achou 1 limitação real (falso-positivo em `us.shandian.giga`, documentada acima e no
design doc §6) que a fixture sintética não teria revelado. Scripts de verificação em
`/tmp` (descartados, não fazem parte do plano — só confirmam que o código do plano
funciona antes de alguém começar a implementar).
