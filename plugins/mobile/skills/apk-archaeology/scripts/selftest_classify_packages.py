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
