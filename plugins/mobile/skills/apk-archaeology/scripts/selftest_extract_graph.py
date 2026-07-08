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
