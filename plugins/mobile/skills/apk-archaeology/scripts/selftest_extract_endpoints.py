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
        # business-candidate: URL com segredo embutido no query parameter
        write(
            os.path.join(sources, "br/com/zup/app/ApiWithSecret.java"),
            'package br.com.zup.app;\n'
            'public class ApiWithSecret {\n'
            '    String url = "https://api.example.com.br/track?api_key=AKIAABCDEFGHIJKLMNOP";\n'
            '}\n',
        )
        # business-candidate: URL com segredo embutido na posição userinfo (Sentry DSN style)
        write(
            os.path.join(sources, "br/com/zup/app/SentryConfig.java"),
            'package br.com.zup.app;\n'
            'public class SentryConfig {\n'
            '    String dsn = "https://AKIAABCDEFGHIJKLMNOP@api.example.com/telemetry";\n'
            '}\n',
        )
        # business-candidate: chave de formato conhecido fundida a sufixo de baixa entropia
        # (round 3 — derrota o delimiter-split E o fallback de entropia simultaneamente)
        write(
            os.path.join(sources, "br/com/zup/app/CdnAsset.java"),
            'package br.com.zup.app;\n'
            'public class CdnAsset {\n'
            '    String u = "https://cdn.example.com/AKIAIOSFODNN7EXAMPLE.txt";\n'
            '}\n',
        )
        # business-candidate: mesma classe de fusão, sufixo "-v1" em vez de extensão de arquivo
        write(
            os.path.join(sources, "br/com/zup/app/VersionedAsset.java"),
            'package br.com.zup.app;\n'
            'public class VersionedAsset {\n'
            '    String u = "https://api.example.com/v/AKIAIOSFODNN7EXAMPLE-v1";\n'
            '}\n',
        )

        result = extract(sources, CLASSIFY_RESULT)
        urls = {e["url"] for e in result["endpoints"]}

        assert "https://api.example.com.br/v1/login" in urls, urls
        assert "https://sdk.thirdparty.io/track" in urls, urls
        assert "https://androidx.internal.example/should-not-appear" not in urls, urls

        # URL com segredo embutido deve aparecer COM o segredo redigido
        url_with_secret_redacted = "https://api.example.com.br/track?api_key=[REDACTED]"
        assert url_with_secret_redacted in urls, (
            f"URL com segredo redigido não encontrada. URLs: {urls}"
        )

        by_url = {e["url"]: e for e in result["endpoints"]}
        assert by_url["https://api.example.com.br/v1/login"]["tag"] == "business"
        assert by_url["https://sdk.thirdparty.io/track"]["tag"] == "unclassifiable"
        assert by_url[url_with_secret_redacted]["tag"] == "business"

        # URL com segredo embutido na posição userinfo deve aparecer COM o segredo redigido
        url_with_userinfo_secret_redacted = "https://[REDACTED]@api.example.com/telemetry"
        assert url_with_userinfo_secret_redacted in urls, (
            f"URL com segredo na userinfo não encontrada. URLs: {urls}"
        )

        # round 3, caso 1: chave de formato conhecido fundida a extensão de arquivo (.txt)
        url_fused_extension_redacted = "https://cdn.example.com/[REDACTED].txt"
        assert url_fused_extension_redacted in urls, (
            f"URL com chave fundida a .txt não encontrada. URLs: {urls}"
        )
        assert by_url[url_fused_extension_redacted]["tag"] == "business"
        assert "https://cdn.example.com/" in url_fused_extension_redacted, (
            "Host/path não preservados na URL fundida a .txt"
        )
        assert ".txt" in url_fused_extension_redacted, (
            "Sufixo .txt não preservado na URL fundida"
        )

        # round 3, caso 2: chave de formato conhecido fundida a sufixo de versão (-v1)
        url_fused_version_redacted = "https://api.example.com/v/[REDACTED]-v1"
        assert url_fused_version_redacted in urls, (
            f"URL com chave fundida a -v1 não encontrada. URLs: {urls}"
        )
        assert by_url[url_fused_version_redacted]["tag"] == "business"
        assert "https://api.example.com/v/" in url_fused_version_redacted, (
            "Host/path não preservados na URL fundida a -v1"
        )
        assert "-v1" in url_fused_version_redacted, (
            "Sufixo -v1 não preservado na URL fundida"
        )

        # 5 secrets redacted: 1 standalone key + 1 in query parameter + 1 in userinfo
        # + 2 known-format keys fused to adjacent in-charset, non-delimiter text (round 3)
        assert result["secrets_redacted"] == 5, result["secrets_redacted"]
        raw_json = json.dumps(result)
        assert "AKIAABCDEFGHIJKLMNOP" not in raw_json, "SEGREDO VAZOU NO OUTPUT"
        assert "AKIAIOSFODNN7EXAMPLE" not in raw_json, (
            "SEGREDO VAZOU NO OUTPUT (chave fundida round 3)"
        )

        # Verify URL structure is preserved (non-secret parts still present)
        assert "https://api.example.com.br/track" in url_with_secret_redacted, (
            "URL structure não preservada"
        )
        assert "api_key" in url_with_secret_redacted, (
            "Query parameter key não preservado"
        )
        assert "api.example.com/telemetry" in url_with_userinfo_secret_redacted, (
            "URL structure with userinfo não preservada"
        )

    print("OK: todas as asserções passaram (URLs corretas, lib excluída, segredo redigido, URL com segredo embutido redaçado, chave fundida a sufixo redigida)")


if __name__ == "__main__":
    main()
