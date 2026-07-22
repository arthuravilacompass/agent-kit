#!/usr/bin/env python3
"""selftest_extract_permissions.py — synthetic fixture: a fake
AndroidManifest.xml with 6 <uses-permission> entries using standard Android
platform permission strings (not client-specific — these are the Android
SDK's own permission names), covering both attribute orders
(maxSdkVersion-before-name and maxSdkVersion-after-name), permissions with no
maxSdkVersion at all, and an entry carrying an extra, unrelated attribute
(`tools:node="remove"`, a real-world manifest-merger directive) — the
regression lock for the extra-attribute bug the two-stage TAG_RE/NAME_RE
match replaced a single-shot regex to fix."""
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(__file__))
from extract_permissions import extract_permissions  # noqa: E402


def write(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


MANIFEST = """<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android"
    xmlns:tools="http://schemas.android.com/tools" package="com.example.app">
    <uses-permission android:name="android.permission.INTERNET"/>
    <uses-permission android:name="android.permission.CAMERA"/>
    <uses-permission android:name="android.permission.ACCESS_FINE_LOCATION"/>
    <uses-permission android:maxSdkVersion="32" android:name="android.permission.READ_EXTERNAL_STORAGE"/>
    <uses-permission android:name="android.permission.RECORD_AUDIO" android:maxSdkVersion="28"/>
    <uses-permission tools:node="remove" android:name="android.permission.READ_PHONE_STATE"/>
</manifest>
"""


def main():
    with tempfile.TemporaryDirectory() as tmp:
        apktool_dir = os.path.join(tmp, "apktool")
        write(os.path.join(apktool_dir, "AndroidManifest.xml"), MANIFEST)

        result = extract_permissions(apktool_dir)

        assert result["permissions"] == [
            {"name": "android.permission.ACCESS_FINE_LOCATION", "max_sdk_version": None},
            {"name": "android.permission.CAMERA", "max_sdk_version": None},
            {"name": "android.permission.INTERNET", "max_sdk_version": None},
            {"name": "android.permission.READ_EXTERNAL_STORAGE", "max_sdk_version": 32},
            {"name": "android.permission.READ_PHONE_STATE", "max_sdk_version": None},
            {"name": "android.permission.RECORD_AUDIO", "max_sdk_version": 28},
        ], result["permissions"]

        # regression lock: an entry carrying an extra attribute alongside
        # android:name (here tools:node="remove", a real manifest-merger
        # directive) must still be extracted, not silently dropped by a
        # regex that expects the tag to end right after its two attributes
        # of interest.
        names = {p["name"] for p in result["permissions"]}
        assert "android.permission.READ_PHONE_STATE" in names, result["permissions"]

        assert result["summary"]["total_permissions"] == 6, result["summary"]

        # honest failure when AndroidManifest.xml is missing -- not a silent
        # empty result (unlike extract_harvest.py's OPTIONAL resource files,
        # the manifest is a required input every APK has).
        empty_apktool = os.path.join(tmp, "empty_apktool")
        os.makedirs(empty_apktool)
        raised = False
        try:
            extract_permissions(empty_apktool)
        except SystemExit:
            raised = True
        assert raised, "missing AndroidManifest.xml must fail loud (SystemExit), not go quiet"

    print(
        "OK: 6 declared permissions parsed (both maxSdkVersion attribute "
        "orders + no-maxSdk entries + an extra-attribute entry), sorted by "
        "name, missing manifest fails loud"
    )


if __name__ == "__main__":
    main()
