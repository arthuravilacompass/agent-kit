#!/usr/bin/env python3
"""selftest_grade_fidelity.py — fixture com 1 acerto, 1 falso-positivo, 1 falso-negativo."""
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(__file__))
from grade_fidelity import grade  # noqa: E402


def write(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def main():
    with tempfile.TemporaryDirectory() as tmp:
        endpoints_path = os.path.join(tmp, "endpoints.json")
        with open(endpoints_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "endpoints": [
                        {"url": "https://real.example.com/a", "file": "x", "line": 1, "tag": "business"},
                        {"url": "https://falso-positivo.example.com/b", "file": "x", "line": 2, "tag": "business"},
                    ],
                    "secrets_redacted": 0,
                },
                f,
            )

        real_source = os.path.join(tmp, "real_source")
        write(
            os.path.join(real_source, "App.java"),
            'String a = "https://real.example.com/a";\n'
            'String c = "https://falso-negativo.example.com/c";\n',
        )

        result = grade(endpoints_path, real_source)

        assert result["true_positive_count"] == 1, result
        assert result["false_positive_count"] == 1, result
        assert "https://falso-positivo.example.com/b" in result["false_positives"], result
        assert result["false_negative_count"] == 1, result
        assert "https://falso-negativo.example.com/c" in result["false_negatives"], result
        assert result["recall"] == 0.5, result["recall"]

    print("OK: recall/falso-positivo/falso-negativo calculados corretamente")


if __name__ == "__main__":
    main()
