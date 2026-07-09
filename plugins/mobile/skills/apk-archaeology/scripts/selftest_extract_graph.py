#!/usr/bin/env python3
"""selftest_extract_graph.py — fixture with extends/implements and one synthetic class."""
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
        # synthetic class: should be ignored, generate a warning, never become a node/edge
        write(
            os.path.join(sources, "br/com/zup/app/LoginActivity$$ExternalSyntheticLambda0.java"),
            "package br.com.zup.app;\n"
            "public class LoginActivity$$ExternalSyntheticLambda0 extends BaseActivity {\n}\n",
        )
        # unclassifiable: outside the graph's scope, should never appear as a node
        write(
            os.path.join(sources, "a/b.java"),
            "package a;\n"
            "public class b extends c {\n}\n",
        )
        # interface with multiple parents via extends (common Java idiom) — review
        # finding: the old regex only captured 1 name, and the comma made the WHOLE
        # MATCH fail, silently dropping the node and every edge pointing to it
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
        # multi-argument generic with a NESTED generic in one of the arguments — review
        # finding: a naive comma split broke "BaseRepo<Response, Handler<Foo>>" in the
        # middle of the generic, and the residual name "Handler" matched a real class,
        # fabricating a FALSE EDGE (Foo has no relation whatsoever to Handler)
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
        assert "b" not in result["nodes"], "unclassifiable package class leaked into the graph"

        edges = {(e["from"], e["to"], e["kind"]) for e in result["edges"]}
        assert ("LoginActivity", "BaseActivity", "extends") in edges, edges
        assert ("LoginActivity", "Callback", "implements") in edges, edges

        # MultiParent must exist as a node and have BOTH parents as "extends" edges
        assert "MultiParent" in result["nodes"], (
            f"interface with multiple parents disappeared from the graph. nodes: {result['nodes']}"
        )
        assert ("MultiParent", "BaseActivity", "extends") in edges, edges
        assert ("MultiParent", "Callback", "extends") in edges, edges
        assert ("MultiParentImpl", "MultiParent", "implements") in edges, edges

        # multi-argument generic with a nested generic: only the real edge (BaseRepo),
        # NEVER a false edge to the "Handler" that a naive split would leave over
        assert ("GenericChild", "BaseRepo", "extends") in edges, edges
        assert ("GenericChild", "Handler", "extends") not in edges, (
            f"FALSE EDGE: naive split leaked 'Handler' as a spurious parent. edges: {edges}"
        )
        assert ("GenericChild", "Response", "extends") not in edges, (
            f"FALSE EDGE: naive split leaked 'Response' as a spurious parent. edges: {edges}"
        )

        assert any("ExternalSyntheticLambda0" in w for w in result["artifact_warnings"]), result[
            "artifact_warnings"
        ]
        assert not any(
            n.startswith("LoginActivity$") for n in result["nodes"]
        ), "synthetic class not filtered"

    print("OK: all assertions passed (correct edges, unclassifiable excluded, synthetic filtered)")


if __name__ == "__main__":
    main()
