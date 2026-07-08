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
        # interface com múltiplos pais via extends (idioma comum em Java) — achado de
        # revisão: regex antiga só capturava 1 nome, e a vírgula fazia o MATCH INTEIRO
        # falhar, derrubando o node e toda edge que apontasse pra ele, sem aviso
        write(
            os.path.join(sources, "br/com/zup/app/MultiParent.java"),
            "package br.com.zup.app;\n"
            "public interface MultiParent extends BaseActivity, Callback {\n}\n",
        )
        write(
            os.path.join(sources, "br/com/zup/app/MultiParentImpl.java"),
            "package br.com.zup.app;\n"
            "public class MultiParentImpl implements MultiParent {\n}\n",
        )
        # generic multi-argumento com generic ANINHADO num dos argumentos — achado de
        # revisão: split ingênuo por vírgula quebrava "BaseRepo<Response, Handler<Foo>>"
        # no meio do generic, e o nome residual "Handler" coincidia com uma classe real,
        # fabricando uma ARESTA FALSA (Foo não tem relação nenhuma com Handler)
        write(
            os.path.join(sources, "br/com/zup/app/GenericChild.java"),
            "package br.com.zup.app;\n"
            "public class GenericChild extends BaseRepo<Response, Handler<GenericChild>> {\n}\n",
        )
        write(
            os.path.join(sources, "br/com/zup/app/BaseRepo.java"),
            "package br.com.zup.app;\n"
            "public class BaseRepo<A, B> {\n}\n",
        )
        write(
            os.path.join(sources, "br/com/zup/app/Handler.java"),
            "package br.com.zup.app;\n"
            "public class Handler {\n}\n",
        )
        write(
            os.path.join(sources, "br/com/zup/app/Response.java"),
            "package br.com.zup.app;\n"
            "public class Response {\n}\n",
        )

        result = extract_graph(sources, CLASSIFY_RESULT)

        assert "LoginActivity" in result["nodes"], result["nodes"]
        assert "BaseActivity" in result["nodes"], result["nodes"]
        assert "Callback" in result["nodes"], result["nodes"]
        assert "b" not in result["nodes"], "classe de pacote unclassifiable vazou pro grafo"

        edges = {(e["from"], e["to"], e["kind"]) for e in result["edges"]}
        assert ("LoginActivity", "BaseActivity", "extends") in edges, edges
        assert ("LoginActivity", "Callback", "implements") in edges, edges

        # MultiParent precisa existir como node e ter AMBOS os pais como edges "extends"
        assert "MultiParent" in result["nodes"], (
            f"interface com múltiplos pais desapareceu do grafo. nodes: {result['nodes']}"
        )
        assert ("MultiParent", "BaseActivity", "extends") in edges, edges
        assert ("MultiParent", "Callback", "extends") in edges, edges
        assert ("MultiParentImpl", "MultiParent", "implements") in edges, edges

        # generic multi-argumento com generic aninhado: só a edge real (BaseRepo),
        # NUNCA uma edge falsa pro "Handler" que sobraria de um split ingênuo
        assert ("GenericChild", "BaseRepo", "extends") in edges, edges
        assert ("GenericChild", "Handler", "extends") not in edges, (
            f"ARESTA FALSA: split ingênuo vazou 'Handler' como pai espúrio. edges: {edges}"
        )
        assert ("GenericChild", "Response", "extends") not in edges, (
            f"ARESTA FALSA: split ingênuo vazou 'Response' como pai espúrio. edges: {edges}"
        )

        assert any("ExternalSyntheticLambda0" in w for w in result["artifact_warnings"]), result[
            "artifact_warnings"
        ]
        assert not any(
            n.startswith("LoginActivity$") for n in result["nodes"]
        ), "classe sintética não filtrada"

    print("OK: todas as asserções passaram (edges corretos, unclassifiable excluído, sintética filtrada)")


if __name__ == "__main__":
    main()
