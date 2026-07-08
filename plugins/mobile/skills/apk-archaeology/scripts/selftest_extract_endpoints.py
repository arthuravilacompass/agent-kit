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
        # business-candidate: chave de formato conhecido fundida DIRETAMENTE (zero
        # delimitador) a um segredo genérico de alta entropia distinto — regressão
        # achada na revisão round 4: o guard "[REDACTED]" in part pulava o token
        # inteiro, deixando o resíduo de alta entropia vazar sem checagem.
        write(
            os.path.join(sources, "br/com/zup/app/FusedDualSecret.java"),
            'package br.com.zup.app;\n'
            'public class FusedDualSecret {\n'
            '    String u = "https://x.io/p/AKIAIOSFODNN7EXAMPLEaB3xZ9qWmK7pL2vN8sT4uY6r";\n'
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

        # round 4: chave conhecida + segredo genérico fundidos sem NENHUM delimitador
        # entre eles — os dois devem ser redigidos, não só o de formato conhecido
        url_fused_dual = "https://x.io/p/[REDACTED][REDACTED]"
        assert url_fused_dual in urls, (
            f"URL com par de segredos fundidos não encontrada. URLs: {urls}"
        )
        assert by_url[url_fused_dual]["tag"] == "business"
        assert "https://x.io/p/" in url_fused_dual, (
            "Host/path não preservados na URL com par de segredos fundidos"
        )

        # 7 secrets redacted: 1 standalone + 1 query param + 1 userinfo + 2 fundidos
        # a sufixo de baixa entropia (round 3) + 2 do par fundido sem delimitador (round 4)
        assert result["secrets_redacted"] == 7, result["secrets_redacted"]
        raw_json = json.dumps(result)
        assert "AKIAABCDEFGHIJKLMNOP" not in raw_json, "SEGREDO VAZOU NO OUTPUT"
        assert "AKIAIOSFODNN7EXAMPLE" not in raw_json, (
            "SEGREDO VAZOU NO OUTPUT (chave fundida round 3)"
        )
        assert "aB3xZ9qWmK7pL2vN8sT4uY6r" not in raw_json, (
            "SEGREDO VAZOU NO OUTPUT (segredo genérico fundido, regressão round 4)"
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
