#!/usr/bin/env python3
"""selftest_extract_harvest.py — synthetic fixture, no dependency on a real APK.

Covers all 5 categories: BuildConfig (URL + name-flagged secret + plain
field), network_security_config.xml (cleartext true/false + pin-set +
domain-only block), a @Module and a @Component (Dagger-shaped), a crash-key
call site (+ a plural setCustomKeys call that must NOT match), and
colors.xml/dimens.xml design tokens.
"""
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(__file__))
from extract_harvest import harvest  # noqa: E402

# Deliberately short (<20 chars) and low shannon-entropy — mirrors a REAL
# corpus finding (a hex-encoded `*_APPKEY` field measured ~3.2 bits/char,
# under the >=4.0 threshold). The value-only heuristic would NOT catch this;
# only the field-NAME signal (contains "API_KEY") should force redaction.
NAME_FLAGGED_SECRET = "a1b2c3d4e5f6g7h8i9"


def write(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def make_fixture(tmp):
    sources = os.path.join(tmp, "sources")
    apktool = os.path.join(tmp, "apktool")

    # --- 1. BuildConfig.java: URL, name-flagged secret, plain version field ---
    write(
        os.path.join(sources, "com/example/app/BuildConfig.java"),
        "package com.example.app;\n"
        "\n"
        "public final class BuildConfig {\n"
        '    public static final String BASE_URL = "https://api.example.com/v1";\n'
        f'    public static final String API_KEY = "{NAME_FLAGGED_SECRET}";\n'
        '    public static final String VERSION_NAME = "1.0.0";\n'
        "    public static final boolean FEATURE_X_ENABLED = true;\n"
        "}\n",
    )

    # --- 2. network_security_config.xml ---
    write(
        os.path.join(apktool, "res/xml/network_security_config.xml"),
        '<?xml version="1.0" encoding="utf-8"?>\n'
        "<network-security-config>\n"
        '    <domain-config cleartextTrafficPermitted="false">\n'
        '        <domain includeSubdomains="true">api.example.com</domain>\n'
        '        <domain includeSubdomains="false">cdn.example.com</domain>\n'
        '        <pin-set expiration="2030-01-01">\n'
        '            <pin digest="SHA-256">AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=</pin>\n'
        '            <pin digest="SHA-256">BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB=</pin>\n'
        "        </pin-set>\n"
        "    </domain-config>\n"
        '    <domain-config cleartextTrafficPermitted="true">\n'
        '        <domain includeSubdomains="true">insecure.example.com</domain>\n'
        "    </domain-config>\n"
        "</network-security-config>\n",
    )

    # --- 3. DI: a @Component wrapping a nested @Module (Dagger shape) ---
    write(
        os.path.join(sources, "com/example/di/AppComponent.java"),
        "package com.example.di;\n"
        "\n"
        "import dagger.Binds;\n"
        "import dagger.BindsInstance;\n"
        "import dagger.Component;\n"
        "import dagger.Module;\n"
        "\n"
        "@Component(modules = {AppComponent.NetworkModule.class})\n"
        "public interface AppComponent {\n"
        "\n"
        "    @Component.Builder\n"
        "    interface Builder {\n"
        "        @BindsInstance\n"
        "        Builder context(Context context);\n"
        "\n"
        "        AppComponent build();\n"
        "    }\n"
        "\n"
        "    ApiClient apiClient();\n"
        "\n"
        "    @Module\n"
        "    interface NetworkModule {\n"
        "        @Binds\n"
        "        ApiClient provideApiClient(ApiClientImpl impl);\n"
        "\n"
        "        @Binds\n"
        "        OkHttpClient provideOkHttpClient(OkHttpClientImpl impl);\n"
        "    }\n"
        "}\n",
    )

    # --- 4. Crash keys: one literal call site + one plural (must not match) ---
    write(
        os.path.join(sources, "com/example/crash/CrashReporter.java"),
        "package com.example.crash;\n"
        "\n"
        "public class CrashReporter {\n"
        "    void report(Map<String, String> extra) {\n"
        '        firebaseCrashlytics.setCustomKey("user_tier", "gold");\n'
        "        firebaseCrashlytics.setCustomKeys(extra);\n"
        "    }\n"
        "}\n",
    )

    # --- 5. Design tokens ---
    write(
        os.path.join(apktool, "res/values/colors.xml"),
        '<?xml version="1.0" encoding="utf-8"?>\n'
        "<resources>\n"
        '    <color name="brand_primary">#FF0000</color>\n'
        '    <color name="brand_secondary">#00FF00</color>\n'
        "</resources>\n",
    )
    write(
        os.path.join(apktool, "res/values/dimens.xml"),
        '<?xml version="1.0" encoding="utf-8"?>\n'
        "<resources>\n"
        '    <dimen name="spacing_small">8.0dp</dimen>\n'
        "</resources>\n",
    )

    return sources, apktool


def main():
    with tempfile.TemporaryDirectory() as tmp:
        sources, apktool = make_fixture(tmp)
        result = harvest(sources, apktool)

        # --- 1. BuildConfig ---
        by_field = {f["field"]: f for f in result["build_config"]}
        assert len(result["build_config"]) == 4, result["build_config"]

        assert by_field["BASE_URL"]["value"] == "https://api.example.com/v1", by_field["BASE_URL"]
        assert by_field["BASE_URL"]["value_redacted"] is False
        assert by_field["BASE_URL"]["secret_name_flag"] is False

        # name-flagged secret: redacted even though the value itself is short
        # and low-entropy (would NOT trip extract_endpoints.looks_like_secret alone)
        api_key = by_field["API_KEY"]
        assert api_key["value"] == "[REDACTED]", api_key
        assert api_key["value_redacted"] is True
        assert api_key["secret_name_flag"] is True
        assert api_key["file"] == os.path.join("com", "example", "app", "BuildConfig.java"), api_key
        assert api_key["line"] == 5, api_key

        assert by_field["VERSION_NAME"]["value"] == "1.0.0"
        assert by_field["VERSION_NAME"]["secret_name_flag"] is False
        assert by_field["FEATURE_X_ENABLED"]["value"] == "true"
        assert by_field["FEATURE_X_ENABLED"]["type"] == "boolean"

        assert result["summary"]["build_config_files_scanned"] == 1
        assert result["summary"]["build_config_fields_total"] == 4
        assert result["summary"]["build_config_secrets_redacted"] == 1
        assert result["summary"]["build_config_secret_names_flagged"] == 1

        raw_json = json.dumps(result)
        assert NAME_FLAGGED_SECRET not in raw_json, "SECRET LEAKED IN OUTPUT"

        # --- 2. network_security_config ---
        nsc = result["network_security_config"]
        assert nsc["found"] is True
        assert nsc["file"] == os.path.join("res", "xml", "network_security_config.xml"), nsc
        assert nsc["base_cleartext_traffic_permitted"] is None, (
            "no cleartextTrafficPermitted on the root element in this fixture"
        )
        assert len(nsc["domain_configs"]) == 2, nsc

        dc0 = nsc["domain_configs"][0]
        assert dc0["cleartext_traffic_permitted"] is False, dc0
        assert len(dc0["domains"]) == 2, dc0
        assert {"domain": "api.example.com", "include_subdomains": True, "line": 4} in dc0["domains"]
        assert {"domain": "cdn.example.com", "include_subdomains": False, "line": 5} in dc0["domains"]
        assert dc0["pin_set"]["expiration"] == "2030-01-01"
        assert len(dc0["pin_set"]["pins"]) == 2
        assert all(p["digest"] == "SHA-256" for p in dc0["pin_set"]["pins"])

        dc1 = nsc["domain_configs"][1]
        assert dc1["cleartext_traffic_permitted"] is True, dc1
        assert len(dc1["domains"]) == 1
        assert dc1["pin_set"] is None, "domain-config with no <pin-set> must stay null"

        assert result["summary"]["network_security_config_domain_configs_total"] == 2
        assert result["summary"]["network_security_config_domains_total"] == 3
        assert result["summary"]["network_security_config_pins_total"] == 2

        # --- 3. DI modules: Component (0 provides) + nested Module (2 provides) ---
        by_class = {m["class"]: m for m in result["di_modules"]}
        assert set(by_class) == {"AppComponent", "NetworkModule"}, by_class

        comp = by_class["AppComponent"]
        assert comp["annotation"] == "@Component", comp
        assert comp["provides"] == [], (
            f"Component must not swallow the nested Module's bindings: {comp}"
        )

        mod = by_class["NetworkModule"]
        assert mod["annotation"] == "@Module", mod
        assert set(mod["provides"]) == {"provideApiClient", "provideOkHttpClient"}, mod

        assert result["summary"]["di_modules_total"] == 2
        assert result["summary"]["di_bindings_total"] == 2

        # --- 4. Crash keys: literal call site only, plural must not match ---
        assert len(result["crash_keys"]) == 1, result["crash_keys"]
        assert result["crash_keys"][0]["key"] == "user_tier", result["crash_keys"][0]
        assert result["summary"]["crash_keys_total"] == 1

        # --- 5. Design tokens ---
        colors = {c["name"]: c["value"] for c in result["design_tokens"]["colors"]}
        assert colors == {"brand_primary": "#FF0000", "brand_secondary": "#00FF00"}, colors
        dimens = {d["name"]: d["value"] for d in result["design_tokens"]["dimens"]}
        assert dimens == {"spacing_small": "8.0dp"}, dimens
        assert result["summary"]["design_tokens_colors_total"] == 2
        assert result["summary"]["design_tokens_dimens_total"] == 1

        # --- honest null: no res/xml at all ---
        empty_apktool = os.path.join(tmp, "empty_apktool")
        os.makedirs(empty_apktool)
        empty_result = harvest(sources, empty_apktool)
        assert empty_result["network_security_config"]["found"] is False
        assert empty_result["network_security_config"]["domain_configs"] == []
        assert empty_result["design_tokens"]["colors"] == []
        assert empty_result["design_tokens"]["dimens"] == []

    print(
        "OK: BuildConfig (URL kept, name-flagged secret redacted, plain fields kept), "
        "network_security_config (cleartext true/false, pin-set, domain-only block), "
        "DI Component/Module boundary (no cross-swallow), crash key (plural excluded), "
        "design tokens, honest null on missing res/xml"
    )


if __name__ == "__main__":
    main()
