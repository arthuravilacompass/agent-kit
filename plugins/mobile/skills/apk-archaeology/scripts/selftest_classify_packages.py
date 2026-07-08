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
    # lib conhecida com cabeça não-compartilhada multi-segmento: known-third-party
    os.makedirs(os.path.join(base, "javax", "inject"))
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
                {"name": "Javax inject", "prefixes": ["javax"]},
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
        assert packages["javax"]["bucket"] == "known-third-party", packages["javax"]
        assert packages["javax"]["matched_lib"] == "Javax inject"
        assert packages["br/com/zup"]["bucket"] == "business-candidate", packages["br/com/zup"]
        assert packages["org/schabi"]["bucket"] == "business-candidate", packages["org/schabi"]

    # Regression test: verify unreachable multi-segment non-shared prefixes are NOT matched.
    # This documents that prefixes like "foo.bar" (non-shared head, multiple segments) cannot
    # be reached by the algorithm, which stops after matching the head "foo" alone.
    with tempfile.TemporaryDirectory() as tmp:
        sources = os.path.join(tmp, "sources")
        os.makedirs(sources)
        os.makedirs(os.path.join(sources, "foo", "bar"))

        libs_path = os.path.join(tmp, "known-libs.json")
        with open(libs_path, "w", encoding="utf-8") as f:
            json.dump({
                "libraries": [
                    {"name": "Some Multi Segment Non-Shared", "prefixes": ["foo.bar"]},
                ]
            }, f)

        known_libs = load_known_libs(libs_path)
        result = classify(sources, known_libs)
        packages = result["packages"]

        # foo/bar package lands at "foo" (non-shared head), so it classifies as business-candidate,
        # NOT as known-third-party (it never matches the unreachable "foo.bar" prefix).
        assert packages["foo"]["bucket"] == "business-candidate", packages["foo"]
        assert packages["foo"]["matched_lib"] is None, (
            "Regression: unreachable prefix 'foo.bar' should not match at 'foo' head"
        )

    print("OK: 10/10 asserções passaram")


if __name__ == "__main__":
    main()
