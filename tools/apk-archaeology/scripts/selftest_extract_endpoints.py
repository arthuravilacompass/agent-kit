#!/usr/bin/env python3
"""selftest_extract_endpoints.py — fixture with a real URL, synthetic secret, and excluded lib."""
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

        # business-candidate: has a real URL (should appear, tag=business)
        write(
            os.path.join(sources, "br/com/zup/app/Api.java"),
            'package br.com.zup.app;\n'
            'public class Api {\n'
            '    String base = "https://api.example.com.br/v1/login";\n'
            '    String key = "AKIAABCDEFGHIJKLMNOP";\n'
            '}\n',
        )
        # unclassifiable: also has a URL (should appear, tag=unclassifiable)
        write(
            os.path.join(sources, "a/b.java"),
            'package a;\n'
            'public class b {\n'
            '    String u = "https://sdk.thirdparty.io/track";\n'
            '}\n',
        )
        # known-third-party: must NEVER appear, even though it has a URL
        write(
            os.path.join(sources, "androidx/x/Y.java"),
            'package androidx.x;\n'
            'public class Y {\n'
            '    String u = "https://androidx.internal.example/should-not-appear";\n'
            '}\n',
        )
        # business-candidate: URL with a secret embedded in the query parameter
        write(
            os.path.join(sources, "br/com/zup/app/ApiWithSecret.java"),
            'package br.com.zup.app;\n'
            'public class ApiWithSecret {\n'
            '    String url = "https://api.example.com.br/track?api_key=AKIAABCDEFGHIJKLMNOP";\n'
            '}\n',
        )
        # business-candidate: URL with a secret embedded in the userinfo position (Sentry DSN style)
        write(
            os.path.join(sources, "br/com/zup/app/SentryConfig.java"),
            'package br.com.zup.app;\n'
            'public class SentryConfig {\n'
            '    String dsn = "https://AKIAABCDEFGHIJKLMNOP@api.example.com/telemetry";\n'
            '}\n',
        )
        # business-candidate: known-format key fused to a low-entropy suffix
        # (round 3 — defeats both the delimiter-split AND the entropy fallback at once)
        write(
            os.path.join(sources, "br/com/zup/app/CdnAsset.java"),
            'package br.com.zup.app;\n'
            'public class CdnAsset {\n'
            '    String u = "https://cdn.example.com/AKIAIOSFODNN7EXAMPLE.txt";\n'
            '}\n',
        )
        # business-candidate: same fusion class, "-v1" suffix instead of a file extension
        write(
            os.path.join(sources, "br/com/zup/app/VersionedAsset.java"),
            'package br.com.zup.app;\n'
            'public class VersionedAsset {\n'
            '    String u = "https://api.example.com/v/AKIAIOSFODNN7EXAMPLE-v1";\n'
            '}\n',
        )
        # business-candidate: known-format key fused DIRECTLY (zero delimiter)
        # to a distinct, generic high-entropy secret — regression found in
        # round 4 review: the "[REDACTED]" in part guard skipped the whole
        # token, letting the high-entropy residue leak unchecked.
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

        # URL with embedded secret should appear WITH the secret redacted
        url_with_secret_redacted = "https://api.example.com.br/track?api_key=[REDACTED]"
        assert url_with_secret_redacted in urls, (
            f"URL with redacted secret not found. URLs: {urls}"
        )

        by_url = {e["url"]: e for e in result["endpoints"]}
        assert by_url["https://api.example.com.br/v1/login"]["tag"] == "business"
        assert by_url["https://sdk.thirdparty.io/track"]["tag"] == "unclassifiable"
        assert by_url[url_with_secret_redacted]["tag"] == "business"

        # URL with a secret embedded in the userinfo position should appear WITH the secret redacted
        url_with_userinfo_secret_redacted = "https://[REDACTED]@api.example.com/telemetry"
        assert url_with_userinfo_secret_redacted in urls, (
            f"URL with userinfo secret not found. URLs: {urls}"
        )

        # round 3, case 1: known-format key fused to a file extension (.txt)
        url_fused_extension_redacted = "https://cdn.example.com/[REDACTED].txt"
        assert url_fused_extension_redacted in urls, (
            f"URL with key fused to .txt not found. URLs: {urls}"
        )
        assert by_url[url_fused_extension_redacted]["tag"] == "business"
        assert "https://cdn.example.com/" in url_fused_extension_redacted, (
            "Host/path not preserved in the URL fused to .txt"
        )
        assert ".txt" in url_fused_extension_redacted, (
            ".txt suffix not preserved in the fused URL"
        )

        # round 3, case 2: known-format key fused to a version suffix (-v1)
        url_fused_version_redacted = "https://api.example.com/v/[REDACTED]-v1"
        assert url_fused_version_redacted in urls, (
            f"URL with key fused to -v1 not found. URLs: {urls}"
        )
        assert by_url[url_fused_version_redacted]["tag"] == "business"
        assert "https://api.example.com/v/" in url_fused_version_redacted, (
            "Host/path not preserved in the URL fused to -v1"
        )
        assert "-v1" in url_fused_version_redacted, (
            "-v1 suffix not preserved in the fused URL"
        )

        # round 4: known key + generic secret fused with NO delimiter at all
        # between them — both must be redacted, not just the known-format one
        url_fused_dual = "https://x.io/p/[REDACTED][REDACTED]"
        assert url_fused_dual in urls, (
            f"URL with fused secret pair not found. URLs: {urls}"
        )
        assert by_url[url_fused_dual]["tag"] == "business"
        assert "https://x.io/p/" in url_fused_dual, (
            "Host/path not preserved in the URL with a fused secret pair"
        )

        # 7 secrets redacted: 1 standalone + 1 query param + 1 userinfo + 2 fused
        # to a low-entropy suffix (round 3) + 2 from the delimiter-less fused pair (round 4)
        assert result["secrets_redacted"] == 7, result["secrets_redacted"]
        raw_json = json.dumps(result)
        assert "AKIAABCDEFGHIJKLMNOP" not in raw_json, "SECRET LEAKED IN OUTPUT"
        assert "AKIAIOSFODNN7EXAMPLE" not in raw_json, (
            "SECRET LEAKED IN OUTPUT (round 3 fused key)"
        )
        assert "aB3xZ9qWmK7pL2vN8sT4uY6r" not in raw_json, (
            "SECRET LEAKED IN OUTPUT (fused generic secret, round 4 regression)"
        )

        # Verify URL structure is preserved (non-secret parts still present)
        assert "https://api.example.com.br/track" in url_with_secret_redacted, (
            "URL structure not preserved"
        )
        assert "api_key" in url_with_secret_redacted, (
            "Query parameter key not preserved"
        )
        assert "api.example.com/telemetry" in url_with_userinfo_secret_redacted, (
            "URL structure with userinfo not preserved"
        )

    print("OK: all assertions passed (correct URLs, lib excluded, secret redacted, URL with embedded secret redacted, key fused to suffix redacted)")


if __name__ == "__main__":
    main()
