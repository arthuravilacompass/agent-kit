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
